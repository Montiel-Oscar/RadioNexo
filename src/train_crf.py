"""CRF BIO por rol, condicionado al indicador espacial anotado.

Un CRF independiente para Trajector y Landmark permite solapamiento entre
roles, varias menciones continuas y vocabulario no visto. El esquema BIO no
puede representar dos menciones del mismo rol superpuestas ni unir segmentos
discontinuos de una misma mención; esos límites se contabilizan.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from baseline_rules import indicator_bounds, sentence_bounds
from evaluate import MAIN_ROLES, read_jsonl


def shape(word: str) -> str:
    raw = "".join("X" if char.isupper() else "x" if char.islower()
                  else "d" if char.isdigit() else char for char in word)
    return "".join(char for index, char in enumerate(raw)
                   if index == 0 or char != raw[index - 1])


def features(document: dict, relation: dict) -> tuple[list[dict], int, int]:
    tokens = document["tokens"]
    indicator_start, indicator_end = indicator_bounds(relation)
    left, right = sentence_bounds(document, indicator_start, indicator_end)
    words = [token["text"] for token in tokens]
    indicator = " ".join(word.casefold() for word in words[indicator_start:indicator_end])
    sequence = []
    for index in range(left, right):
        word = words[index]
        lower = word.casefold()
        distance = (index - indicator_start if index < indicator_start else
                    index - indicator_end + 1 if index >= indicator_end else 0)
        item = {
            "bias": True,
            "word": lower,
            "shape": shape(word),
            "prefix2": lower[:2],
            "prefix3": lower[:3],
            "suffix2": lower[-2:],
            "suffix3": lower[-3:],
            "is_digit": word.isdigit(),
            "is_upper": word.isupper(),
            "indicator": indicator,
            "at_indicator": indicator_start <= index < indicator_end,
            "distance": str(max(-12, min(12, distance))),
            "side": "left" if distance < 0 else "right" if distance > 0 else "indicator",
        }
        for offset in (-2, -1, 1, 2):
            neighbor = index + offset
            if left <= neighbor < right:
                item[f"word{offset:+d}"] = words[neighbor].casefold()
                item[f"shape{offset:+d}"] = shape(words[neighbor])
            else:
                item[f"boundary{offset:+d}"] = True
        sequence.append(item)
    return sequence, left, right


def labels(document: dict, relation: dict, role_name: str,
           left: int, right: int) -> tuple[list[str], Counter]:
    tags = ["O"] * (right - left)
    skipped = Counter()
    segments = []
    for role in relation["roles"]:
        if role["name"] != role_name:
            continue
        if len(role["span"]["segments"]) > 1:
            skipped["discontinuous_mentions_split"] += 1
        segments.extend(tuple(part) for part in role["span"]["segments"])
    # Ante solapamientos del mismo rol conservamos primero el tramo más largo.
    for start, end in sorted(segments, key=lambda part: (-(part[1] - part[0]), part[0])):
        if start < left or end > right:
            skipped["outside_sentence"] += 1
            continue
        if any(tags[index - left] != "O" for index in range(start, end)):
            skipped["overlapping_segments"] += 1
            continue
        tags[start - left] = "B"
        for index in range(start + 1, end):
            tags[index - left] = "I"
    return tags, skipped


def decode(tags: list[str], offset: int) -> list[tuple[int, int]]:
    spans = []
    start = None
    for index, tag in enumerate(tags + ["O"]):
        if tag == "B" or tag == "I" and start is None:
            if start is not None:
                spans.append((offset + start, offset + index))
            start = index
        elif tag == "O" and start is not None:
            spans.append((offset + start, offset + index))
            start = None
    return spans


def train(train_documents: list[dict], model_dir: Path) -> dict:
    import pycrfsuite

    model_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = Counter()
    for role_name in MAIN_ROLES:
        trainer = pycrfsuite.Trainer(algorithm="lbfgs", verbose=False)
        for document in train_documents:
            for relation in document["relations"]:
                xseq, left, right = features(document, relation)
                yseq, skipped = labels(document, relation, role_name, left, right)
                diagnostics.update({f"{role_name}_{key}": value for key, value in skipped.items()})
                trainer.append(xseq, yseq)
                diagnostics[f"{role_name}_sequences"] += 1
        trainer.set_params({
            "c1": 0.1,
            "c2": 0.1,
            "max_iterations": 100,
            "feature.possible_transitions": True,
        })
        trainer.train(str(model_dir / f"{role_name.lower()}.crfsuite"))
    return dict(diagnostics)


def predict(documents: list[dict], model_dir: Path) -> list[dict]:
    import pycrfsuite

    taggers = {}
    for role_name in MAIN_ROLES:
        tagger = pycrfsuite.Tagger()
        tagger.open(str(model_dir / f"{role_name.lower()}.crfsuite"))
        taggers[role_name] = tagger
    frames = []
    for document in documents:
        for relation in document["relations"]:
            xseq, left, _ = features(document, relation)
            roles = []
            for name in MAIN_ROLES:
                for start, end in decode(taggers[name].tag(xseq), left):
                    roles.append({"name": name, "span": {"segments": [[start, end]]}})
            frames.append({"id": document["id"], "indicator": relation["indicator"],
                           "roles": roles})
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/processed/train.jsonl"))
    parser.add_argument("--input", type=Path, default=Path("data/processed/dev.jsonl"))
    parser.add_argument("--models", type=Path, default=Path("models/crf_v1"))
    parser.add_argument("--output", type=Path, default=Path("results/tmp/crf_dev.jsonl"))
    parser.add_argument("--predict-only", action="store_true",
                        help="Carga pesos existentes sin volver a entrenar")
    args = parser.parse_args()
    target = read_jsonl(args.input)
    training = read_jsonl(args.train)
    if {document["id"] for document in training} & {document["id"] for document in target}:
        raise SystemExit("Fuga de datos: train e input comparten identificadores")
    if args.predict_only:
        if any(not (args.models / f"{role.lower()}.crfsuite").is_file() for role in MAIN_ROLES):
            raise SystemExit("Faltan pesos CRF; entrenar antes de --predict-only")
        print("Cargando pesos CRF existentes...", flush=True)
    else:
        print("Entrenando CRF...", flush=True)
        diagnostics = train(training, args.models)
        print("Diagnóstico de representación:", json.dumps(diagnostics), flush=True)
    frames = predict(target, args.models)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for frame in frames:
            handle.write(json.dumps(frame, ensure_ascii=False) + "\n")
    print(f"Predicciones: {args.output} ({len(frames)} indicadores)")


if __name__ == "__main__":
    main()
