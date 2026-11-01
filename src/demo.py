"""Demostración didáctica con frases inventadas; no evalúa el corpus.

Requiere haber preparado train y entrenado los dos CRF. El indicador espacial
se marca a mano porque los tres métodos estudiados lo reciben como entrada.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from baseline_rules import fit, predict as rules_predict
from evaluate import read_jsonl
from hybrid import combine
from train_crf import predict as crf_predict


EXAMPLES = (
    ("There is an opacity in the left lung .", "in"),
    ("A catheter tip projects over the right atrium .", "over"),
    ("No pleural effusion is seen in the right hemithorax .", "in"),
)


def document_from_sentence(number: int, sentence: str, indicator: str) -> dict:
    words = sentence.split()
    indicator_positions = [i for i, word in enumerate(words) if word.casefold() == indicator]
    if len(indicator_positions) != 1:
        raise ValueError(f"Se esperaba un indicador único: {indicator!r}")
    position = indicator_positions[0]
    return {
        "id": f"ejemplo-inventado-{number}",
        "tokens": [{"text": word} for word in words],
        "sentences": [[0, len(words)]],
        "relations": [{"indicator": {"segments": [[position, position + 1]]}, "roles": []}],
    }


def surface(document: dict, role: dict) -> str:
    words = [token["text"] for token in document["tokens"]]
    return " ... ".join(" ".join(words[start:end]) for start, end in role["span"]["segments"])


def describe(document: dict, frame: dict) -> str:
    parts = []
    for name in ("Trajector", "Landmark"):
        values = [surface(document, role) for role in frame["roles"] if role["name"] == name]
        parts.append(f"{name}: {', '.join(values) if values else '—'}")
    return " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/processed/train.jsonl"))
    parser.add_argument("--models", type=Path, default=Path("models/crf_v1"))
    args = parser.parse_args()
    if not args.train.is_file():
        parser.error("Falta train.jsonl; ejecuta primero: python src/prepare_data.py")
    if not all((args.models / f"{name}.crfsuite").is_file() for name in ("trajector", "landmark")):
        parser.error("Faltan pesos; ejecuta primero: python src/train_crf.py")

    documents = [document_from_sentence(i, sentence, indicator)
                 for i, (sentence, indicator) in enumerate(EXAMPLES, 1)]
    lexicon, sides = fit(read_jsonl(args.train))
    rules = [frame for document in documents for frame in rules_predict(document, lexicon, sides)]
    crf = crf_predict(documents, args.models)
    hybrid, _ = combine(rules, crf)

    print("DEMO ILUSTRATIVA — frases inventadas; no son datos de prueba ni F1")
    print("El indicador espacial se proporciona a los métodos; la negación no se evalúa.\n")
    for (sentence, indicator), document, rule, model, combined in zip(
        EXAMPLES, documents, rules, crf, hybrid, strict=True
    ):
        print(f"Texto: {sentence}")
        print(f"Indicador dado: {indicator}")
        for label, frame in (("Reglas", rule), ("CRF", model), ("Híbrido", combined)):
            print(f"  {label:7} {describe(document, frame)}")
        print()


if __name__ == "__main__":
    main()
