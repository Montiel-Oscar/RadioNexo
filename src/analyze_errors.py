"""Diagnóstico agregado de errores en dev, sin imprimir informes clínicos."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from evaluate import MAIN_ROLES, read_jsonl, score, span_key


def overlap(a: tuple[tuple[int, int], ...], b: tuple[tuple[int, int], ...]) -> bool:
    return any(max(x, u) < min(y, v) for x, y in a for u, v in b)


def analyze(gold: list[dict], predictions: list[dict]) -> dict:
    by_frame = {(row["id"], tuple(map(tuple, row["indicator"]["segments"]))): row
                for row in predictions}
    indicator_groups: dict[str, list[tuple[dict, dict, dict | None]]] = defaultdict(list)
    structure_groups: dict[str, list[tuple[dict, dict, dict | None]]] = defaultdict(list)
    errors = Counter()
    frame_count = 0
    for document in gold:
        tokens = document["tokens"]
        for relation in document["relations"]:
            frame_count += 1
            indicator_key = tuple(map(tuple, relation["indicator"]["segments"]))
            start, end = indicator_key[0]
            indicator = " ".join(token["text"].casefold() for token in tokens[start:end])
            predicted = by_frame.get((document["id"], indicator_key))
            record = (document, relation, predicted)
            indicator_groups[indicator].append(record)
            main_roles = [role for role in relation["roles"] if role["name"] in MAIN_ROLES]
            if any(len(role["span"]["segments"]) > 1 for role in main_roles):
                structure_groups["discontinuo"].append(record)
            if any(sum(role["name"] == name for role in main_roles) > 1 for name in MAIN_ROLES):
                structure_groups["multiplicidad"].append(record)
            if not main_roles:
                structure_groups["sin_roles_principales"].append(record)
            if len(main_roles) == 2 and all(
                sum(role["name"] == name for role in main_roles) == 1 for name in MAIN_ROLES
            ) and all(len(role["span"]["segments"]) == 1 for role in main_roles):
                structure_groups["un_trayector_un_lugar"].append(record)

            for name in MAIN_ROLES:
                gold_spans = [span_key(role["span"], len(tokens)) for role in main_roles
                              if role["name"] == name]
                predicted_spans = [span_key(role["span"], len(tokens))
                                   for role in predicted["roles"] if role["name"] == name] if predicted else []
                for gold_span in gold_spans:
                    if gold_span in predicted_spans:
                        continue
                    category = "solapamiento_sin_coincidencia_exacta" if any(
                        overlap(gold_span, candidate) for candidate in predicted_spans
                    ) else "sin_solapamiento"
                    errors[f"{name}_{category}"] += 1
                if not gold_spans and predicted_spans:
                    errors[f"{name}_prediccion_sin_rol_gold"] += len(predicted_spans)

    def subset_metrics(rows: list[tuple[dict, dict, dict | None]]) -> dict:
        subset_gold = []
        subset_predictions = []
        for document, relation, predicted in rows:
            subset_gold.append({"id": document["id"], "tokens": document["tokens"],
                                "relations": [relation]})
            if predicted:
                subset_predictions.append(predicted)
        # Un informe puede tener varios indicadores en el mismo grupo.
        merged = {}
        for document in subset_gold:
            identifier = document["id"]
            if identifier not in merged:
                merged[identifier] = {"id": identifier, "tokens": document["tokens"],
                                      "relations": []}
            merged[identifier]["relations"].extend(document["relations"])
        result = score(merged.values(), subset_predictions)
        return {"frames": len(rows), **result["overall_micro"]}

    by_indicator = {name: subset_metrics(rows) for name, rows in indicator_groups.items()}
    frequent = dict(sorted(by_indicator.items(), key=lambda item: -item[1]["frames"])[:10])
    return {
        "total_frames": frame_count,
        "overall": score(gold, predictions),
        "frequent_indicators": frequent,
        "structures": {name: subset_metrics(rows) for name, rows in structure_groups.items()},
        "false_negative_types": dict(errors),
        "note": "Subgrupos superpuestos; métricas condicionadas al indicador anotado.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=Path("data/processed/dev.jsonl"))
    parser.add_argument("--predictions", type=Path, default=Path("results/tmp/baseline_rules_dev.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/baseline_rules_dev_analysis.json"))
    args = parser.parse_args()
    result = analyze(read_jsonl(args.gold), read_jsonl(args.predictions))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
