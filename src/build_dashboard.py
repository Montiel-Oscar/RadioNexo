"""Inserta las estadísticas agregadas en un HTML autónomo, sin datos clínicos."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "dashboard/template.html"
STATS = ROOT / "results/visualization_stats.json"
OUTPUT = ROOT / "dashboard/index.html"


def main() -> None:
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count("__RADIONEXO_DATA__") != 1:
        raise ValueError("La plantilla debe tener exactamente un marcador de datos")
    payload = json.dumps(stats, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    OUTPUT.write_text(template.replace("__RADIONEXO_DATA__", payload), encoding="utf-8")
    print(f"Panel generado: {OUTPUT}")


if __name__ == "__main__":
    main()
