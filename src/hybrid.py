"""Híbrido fijo: CRF por defecto; reglas sólo para roles vacíos del CRF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluate import MAIN_ROLES, read_jsonl


def key(frame: dict) -> tuple[str, tuple[tuple[int, int], ...]]:
    return frame["id"], tuple(tuple(part) for part in frame["indicator"]["segments"])


def combine(rule_frames: list[dict], crf_frames: list[dict]) -> tuple[list[dict], dict]:
    rules = {key(frame): frame for frame in rule_frames}
    crf = {key(frame): frame for frame in crf_frames}
    if len(rules) != len(rule_frames) or len(crf) != len(crf_frames):
        raise ValueError("Indicadores duplicados en alguna predicción")
    if set(rules) != set(crf):
        raise ValueError("Reglas y CRF deben predecir los mismos indicadores")
    diagnostics = {"fallback_roles": 0, "fallback_mentions": 0, "crf_roles_kept": 0}
    output = []
    for frame in crf_frames:
        frame_key = key(frame)
        roles = []
        for name in MAIN_ROLES:
            crf_roles = [role for role in frame["roles"] if role["name"] == name]
            rule_roles = [role for role in rules[frame_key]["roles"] if role["name"] == name]
            if crf_roles:
                roles.extend(crf_roles)
                diagnostics["crf_roles_kept"] += 1
            else:
                roles.extend(rule_roles)
                if rule_roles:
                    diagnostics["fallback_roles"] += 1
                    diagnostics["fallback_mentions"] += len(rule_roles)
        output.append({"id": frame["id"], "indicator": frame["indicator"], "roles": roles})
    return output, diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, default=Path("results/tmp/baseline_rules_dev.jsonl"))
    parser.add_argument("--crf", type=Path, default=Path("results/tmp/crf_dev.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/tmp/hybrid_dev.jsonl"))
    args = parser.parse_args()
    predictions, diagnostics = combine(read_jsonl(args.rules), read_jsonl(args.crf))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for frame in predictions:
            handle.write(json.dumps(frame, ensure_ascii=False) + "\n")
    print(json.dumps({"frames": len(predictions), **diagnostics}, indent=2))


if __name__ == "__main__":
    main()
