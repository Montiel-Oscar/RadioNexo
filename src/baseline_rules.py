"""Línea base léxica y de proximidad, condicionada al indicador verdadero.

El vocabulario de fragmentos y las preferencias de lado se aprenden sólo de
train. No se lee ningún rol de los documentos a predecir. Se propone como
máximo un fragmento continuo por rol e indicador; ese límite es deliberado.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from evaluate import MAIN_ROLES, read_jsonl


WINDOW = 12
MAX_PHRASE = 6


def normalized(tokens: list[dict], start: int, end: int) -> tuple[str, ...]:
    return tuple(token["text"].casefold() for token in tokens[start:end])


def indicator_bounds(relation: dict) -> tuple[int, int]:
    segments = relation["indicator"]["segments"]
    return min(start for start, _ in segments), max(end for _, end in segments)


def sentence_bounds(document: dict, start: int, end: int) -> tuple[int, int]:
    for left, right in document["sentences"]:
        if left <= start and end <= right:
            return left, right
    return 0, len(document["tokens"])


def fit(train: list[dict]) -> tuple[dict[str, Counter], dict[tuple[str, str], Counter]]:
    lexicon = {role: Counter() for role in MAIN_ROLES}
    side_counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for document in train:
        tokens = document["tokens"]
        for relation in document["relations"]:
            indicator_start, indicator_end = indicator_bounds(relation)
            indicator = " ".join(normalized(tokens, indicator_start, indicator_end))
            for role in relation["roles"]:
                name = role["name"]
                if name not in MAIN_ROLES or len(role["span"]["segments"]) != 1:
                    continue
                start, end = role["span"]["segments"][0]
                if end - start <= MAX_PHRASE:
                    lexicon[name][normalized(tokens, start, end)] += 1
                if end <= indicator_start:
                    side_counts[(indicator, name)]["left"] += 1
                elif start >= indicator_end:
                    side_counts[(indicator, name)]["right"] += 1
    return lexicon, side_counts


def find_candidate(
    tokens: list[dict], indicator_start: int, indicator_end: int,
    sentence_start: int, sentence_end: int, role: str, indicator: str,
    lexicon: dict[str, Counter], side_counts: dict[tuple[str, str], Counter],
) -> tuple[int, int] | None:
    candidates: list[tuple[tuple[int, int, int, int], tuple[int, int]]] = []
    side_prior = side_counts.get((indicator, role), Counter())
    if not side_prior:
        side_prior = Counter({"left": 1}) if role == "Trajector" else Counter({"right": 1})
    preferred = "left" if side_prior["left"] >= side_prior["right"] else "right"
    for side in ("left", "right"):
        if side == "left":
            first, last = max(sentence_start, indicator_start - WINDOW), indicator_start
        else:
            first, last = indicator_end, min(sentence_end, indicator_end + WINDOW)
        for start in range(first, last):
            for end in range(start + 1, min(last, start + MAX_PHRASE) + 1):
                phrase = normalized(tokens, start, end)
                frequency = lexicon[role][phrase]
                if not frequency:
                    continue
                gap = indicator_start - end if side == "left" else start - indicator_end
                # Prioridad de lado, luego cercanía, longitud y frecuencia.
                rank = (side != preferred, gap, -(end - start), -frequency)
                candidates.append((rank, (start, end)))
    return min(candidates)[1] if candidates else None


def predict(document: dict, lexicon: dict[str, Counter],
            side_counts: dict[tuple[str, str], Counter]) -> list[dict]:
    tokens = document["tokens"]
    frames = []
    for relation in document["relations"]:
        start, end = indicator_bounds(relation)
        sentence_start, sentence_end = sentence_bounds(document, start, end)
        indicator = " ".join(normalized(tokens, start, end))
        roles = []
        for name in MAIN_ROLES:
            candidate = find_candidate(
                tokens, start, end, sentence_start, sentence_end,
                name, indicator, lexicon, side_counts,
            )
            if candidate is not None:
                roles.append({"name": name, "span": {"segments": [list(candidate)]}})
        frames.append({"id": document["id"], "indicator": relation["indicator"], "roles": roles})
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/processed/train.jsonl"))
    parser.add_argument("--input", type=Path, default=Path("data/processed/dev.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/tmp/baseline_rules_dev.jsonl"))
    args = parser.parse_args()
    if args.input.resolve() == args.train.resolve():
        raise SystemExit("La evaluación de referencia debe usar dev, no train")
    train = read_jsonl(args.train)
    target = read_jsonl(args.input)
    if {document["id"] for document in train} & {document["id"] for document in target}:
        raise SystemExit("Fuga de datos: train e input comparten identificadores")
    lexicon, side_counts = fit(train)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for document in target:
            for frame in predict(document, lexicon, side_counts):
                handle.write(json.dumps(frame, ensure_ascii=False) + "\n")
    print(f"Predicciones: {args.output} ({len(target)} informes)")
    print("Vocabulario:", {role: len(lexicon[role]) for role in MAIN_ROLES})


if __name__ == "__main__":
    main()
