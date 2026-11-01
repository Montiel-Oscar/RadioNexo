"""Métrica exacta de roles condicionada al indicador espacial verdadero.

Predicciones: JSONL, un registro por indicador espacial predicho:
{"id":"00004","indicator":{"segments":[[55,56]]},"roles":[
  {"name":"Trajector","span":{"segments":[[53,55]]}},
  {"name":"Landmark","span":{"segments":[[57,60]]}}
]}

Omitir un indicador equivale a predecir cero roles para él. En este protocolo
no se permiten indicadores inventados: detectar indicadores es otra tarea.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Iterable


MAIN_ROLES = ("Trajector", "Landmark")
SpanKey = tuple[tuple[int, int], ...]
FrameKey = tuple[str, SpanKey]
MentionKey = tuple[str, SpanKey, str, SpanKey]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def span_key(value: dict, token_count: int) -> SpanKey:
    try:
        segments = tuple((int(start), int(end)) for start, end in value["segments"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Formato de segmentos inválido") from exc
    if not segments:
        raise ValueError("Un fragmento requiere al menos un segmento")
    if any(start < 0 or start >= end or end > token_count for start, end in segments):
        raise ValueError("Segmento fuera del rango de tokens")
    if any(left[1] > right[0] for left, right in zip(segments, segments[1:])):
        raise ValueError("Segmentos superpuestos o desordenados")
    return segments


def score(gold_documents: Iterable[dict], predicted_frames: Iterable[dict]) -> dict:
    """Devuelve conteos y P/R/F1 por rol y global, con coincidencia exacta."""
    gold_list = list(gold_documents)
    documents = {doc["id"]: doc for doc in gold_list}
    if len(documents) != len(gold_list):
        raise ValueError("Informes duplicados en la referencia")
    gold_frames: set[FrameKey] = set()
    gold_mentions: set[MentionKey] = set()
    for identifier, document in documents.items():
        token_count = len(document["tokens"])
        for relation in document["relations"]:
            indicator = span_key(relation["indicator"], token_count)
            frame = (identifier, indicator)
            if frame in gold_frames:
                raise ValueError(f"Indicador duplicado en referencia: {identifier}")
            gold_frames.add(frame)
            for role in relation["roles"]:
                if role["name"] in MAIN_ROLES:
                    gold_mentions.add((identifier, indicator, role["name"],
                                       span_key(role["span"], token_count)))

    predicted_mentions: set[MentionKey] = set()
    seen_frames: set[FrameKey] = set()
    for frame_record in predicted_frames:
        identifier = frame_record["id"]
        if identifier not in documents:
            raise ValueError(f"Informe ajeno a la referencia: {identifier}")
        token_count = len(documents[identifier]["tokens"])
        indicator = span_key(frame_record["indicator"], token_count)
        frame = (identifier, indicator)
        if frame not in gold_frames:
            raise ValueError(f"Indicador no anotado: {identifier} {indicator}")
        if frame in seen_frames:
            raise ValueError(f"Indicador repetido en predicciones: {identifier} {indicator}")
        seen_frames.add(frame)
        for role in frame_record["roles"]:
            name = role["name"]
            if name not in MAIN_ROLES:
                raise ValueError(f"Rol fuera de la tarea principal: {name}")
            mention = (identifier, indicator, name, span_key(role["span"], token_count))
            if mention in predicted_mentions:
                raise ValueError(f"Mención predicha dos veces: {mention}")
            predicted_mentions.add(mention)

    counts: Counter[str] = Counter()
    for mention in predicted_mentions & gold_mentions:
        counts[f"{mention[2]}_tp"] += 1
    for mention in predicted_mentions - gold_mentions:
        counts[f"{mention[2]}_fp"] += 1
    for mention in gold_mentions - predicted_mentions:
        counts[f"{mention[2]}_fn"] += 1

    def metrics(tp: int, fp: int, fn: int) -> dict:
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {"tp": tp, "fp": fp, "fn": fn,
                "precision": precision, "recall": recall, "f1": f1}

    by_role = {
        role: metrics(counts[f"{role}_tp"], counts[f"{role}_fp"], counts[f"{role}_fn"])
        for role in MAIN_ROLES
    }
    overall = metrics(sum(item["tp"] for item in by_role.values()),
                      sum(item["fp"] for item in by_role.values()),
                      sum(item["fn"] for item in by_role.values()))
    return {"overall_micro": overall, "by_role": by_role,
            "gold_frames": len(gold_frames), "predicted_frames": len(seen_frames)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path, help="JSONL de train/dev/test preparado")
    parser.add_argument("--predictions", required=True, type=Path, help="JSONL de indicadores y roles")
    args = parser.parse_args()
    print(json.dumps(score(read_jsonl(args.gold), read_jsonl(args.predictions)), indent=2))
