"""Comparación apareada con bootstrap por informe (no por mención)."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random

from evaluate import read_jsonl, score


def per_document(gold: list[dict], predictions: list[dict]) -> dict[str, tuple[int, int, int]]:
    by_id: dict[str, list[dict]] = defaultdict(list)
    for frame in predictions:
        by_id[frame["id"]].append(frame)
    gold_ids = {document["id"] for document in gold}
    if len(gold_ids) != len(gold):
        raise ValueError("Identificadores duplicados en referencia")
    if set(by_id) - gold_ids:
        raise ValueError("Predicción de un informe ajeno a la referencia")
    counts = {}
    for document in gold:
        metric = score([document], by_id[document["id"]])["overall_micro"]
        counts[document["id"]] = (metric["tp"], metric["fp"], metric["fn"])
    return counts


def f1(counts: list[tuple[int, int, int]]) -> float:
    tp = sum(row[0] for row in counts)
    fp = sum(row[1] for row in counts)
    fn = sum(row[2] for row in counts)
    denominator = 2 * tp + fp + fn
    return 2 * tp / denominator if denominator else 0.0


def compare(gold: list[dict], first: list[dict], second: list[dict],
            draws: int = 2000, seed: int = 42) -> dict:
    if draws < 1:
        raise ValueError("draws debe ser positivo")
    first_counts = per_document(gold, first)
    second_counts = per_document(gold, second)
    ids = [document["id"] for document in gold]
    rng = random.Random(seed)
    deltas = []
    for _ in range(draws):
        sample = rng.choices(ids, k=len(ids))
        deltas.append(f1([second_counts[key] for key in sample]) -
                      f1([first_counts[key] for key in sample]))
    deltas.sort()
    lower = deltas[int(0.025 * draws)]
    upper = deltas[min(draws - 1, int(0.975 * draws))]
    return {
        "first_f1": f1(list(first_counts.values())),
        "second_f1": f1(list(second_counts.values())),
        "delta_f1": f1(list(second_counts.values())) - f1(list(first_counts.values())),
        "paired_bootstrap_delta_95pct": [lower, upper],
        "bootstrap_draws": draws,
        "seed": seed,
        "unit": "document",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=Path("data/processed/dev.jsonl"))
    parser.add_argument("--first", type=Path, default=Path("results/tmp/baseline_rules_dev.jsonl"))
    parser.add_argument("--second", type=Path, default=Path("results/tmp/crf_dev.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/crf_vs_rules_dev.json"))
    args = parser.parse_args()
    result = compare(read_jsonl(args.gold), read_jsonl(args.first), read_jsonl(args.second))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
