"""Estadísticas agregadas para figuras y panel, sin publicar texto clínico.

Sólo resume la prueba ya evaluada. No entrena, selecciona ni cambia modelos.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from evaluate import MAIN_ROLES, read_jsonl, score


METHOD_PATHS = {
    "Reglas": Path("results/tmp/baseline_rules_test.jsonl"),
    "CRF": Path("results/tmp/crf_test.jsonl"),
    "Híbrido": Path("results/tmp/hybrid_test.jsonl"),
}


def mention_sets(gold: list[dict], predictions: list[dict]) -> tuple[set, set]:
    gold_mentions = set()
    for doc in gold:
        for relation in doc["relations"]:
            indicator = tuple(map(tuple, relation["indicator"]["segments"]))
            for role in relation["roles"]:
                if role["name"] in MAIN_ROLES:
                    gold_mentions.add((doc["id"], indicator, role["name"],
                                       tuple(map(tuple, role["span"]["segments"]))))
    predicted_mentions = {
        (frame["id"], tuple(map(tuple, frame["indicator"]["segments"])), role["name"],
         tuple(map(tuple, role["span"]["segments"])))
        for frame in predictions for role in frame["roles"]
    }
    return gold_mentions, predicted_mentions


def metrics(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p,
            "recall": r, "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}


def indicator_groups(gold: list[dict], sets: dict[str, tuple[set, set]]) -> list[dict]:
    tokens = {doc["id"]: [token["text"] for token in doc["tokens"]] for doc in gold}
    names = {}
    counts = Counter()
    for doc in gold:
        for relation in doc["relations"]:
            key = (doc["id"], tuple(map(tuple, relation["indicator"]["segments"])))
            name = " ".join(" ".join(tokens[doc["id"]][start:end])
                            for start, end in key[1]).casefold()
            names[key] = name
            counts[name] += 1
    rows = []
    for name, frames in counts.most_common():
        if frames < 6:
            continue  # Evita visualizaciones de categorías diminutas.
        row = {"indicator": name, "frames": frames, "methods": {}}
        for method, (reference, predicted) in sets.items():
            gold_subset = {mention for mention in reference if names[(mention[0], mention[1])] == name}
            pred_subset = {mention for mention in predicted if names[(mention[0], mention[1])] == name}
            row["methods"][method] = metrics(len(gold_subset & pred_subset),
                                               len(pred_subset - gold_subset),
                                               len(gold_subset - pred_subset))
        rows.append(row)
    return rows


def length_groups(sets: dict[str, tuple[set, set]]) -> list[dict]:
    reference = next(iter(sets.values()))[0]
    buckets = {"1 token": [], "2 tokens": [], "3 tokens": [], "4+ tokens": [], "Discontinua": []}
    for mention in reference:
        segments = mention[3]
        length = sum(end - start for start, end in segments)
        key = "Discontinua" if len(segments) > 1 else (
            "1 token" if length == 1 else "2 tokens" if length == 2 else
            "3 tokens" if length == 3 else "4+ tokens")
        buckets[key].append(mention)
    rows = []
    for bucket, mentions in buckets.items():
        rows.append({"bucket": bucket, "gold": len(mentions), "recall": {
            method: sum(mention in predicted for mention in mentions) / len(mentions)
            if mentions else 0.0 for method, (_, predicted) in sets.items()}})
    return rows


def document_wins(gold: list[dict], predictions: dict[str, list[dict]]) -> dict:
    grouped = {method: defaultdict(list) for method in predictions}
    for method, frames in predictions.items():
        for frame in frames:
            grouped[method][frame["id"]].append(frame)
    results = {}
    for other in ("Reglas", "Híbrido"):
        wins = Counter()
        for doc in gold:
            if not any(role["name"] in MAIN_ROLES for relation in doc["relations"]
                       for role in relation["roles"]):
                continue
            crf = score([doc], grouped["CRF"][doc["id"]])["overall_micro"]["f1"]
            rival = score([doc], grouped[other][doc["id"]])["overall_micro"]["f1"]
            wins["CRF" if crf > rival else other if rival > crf else "Empate"] += 1
        results[f"CRF_vs_{other}"] = dict(wins)
    return results


def summarize(gold: list[dict], predictions: dict[str, list[dict]]) -> dict:
    scores = {method: score(gold, frames) for method, frames in predictions.items()}
    sets = {method: mention_sets(gold, frames) for method, frames in predictions.items()}
    assert scores["CRF"]["overall_micro"]["tp"] == 521, "No es la prueba final congelada"
    assert scores["CRF"]["overall_micro"]["fp"] == 68
    assert scores["CRF"]["overall_micro"]["fn"] == 70
    return {
        "scope": "Prueba congelada; indicadores verdaderos proporcionados; fragmentos exactos",
        "documents": len(gold),
        "documents_with_indicators": sum(bool(doc["relations"]) for doc in gold),
        "indicators": sum(len(doc["relations"]) for doc in gold),
        "gold_mentions": len(next(iter(sets.values()))[0]),
        "methods": scores,
        "indicators_with_at_least_6_frames": indicator_groups(gold, sets),
        "gold_length_recall": length_groups(sets),
        "document_f1_comparison": document_wins(gold, predictions),
        "notes": [
            "Los grupos por longitud clasifican menciones gold; recall exacta no es F1.",
            "Las comparaciones por documento excluyen documentos sin menciones principales gold.",
            "Los desgloses son descriptivos posteriores a la prueba y no se usaron para ajustar modelos.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=Path("data/processed/test.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/visualization_stats.json"))
    args = parser.parse_args()
    gold = read_jsonl(args.gold)
    predictions = {name: read_jsonl(path) for name, path in METHOD_PATHS.items()}
    result = summarize(gold, predictions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Escritas estadísticas agregadas en {args.output}")


if __name__ == "__main__":
    main()
