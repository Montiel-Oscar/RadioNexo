"""Genera particiones de identificadores sin copiar texto clínico.

Agrupa informes de texto idéntico y estratifica por presencia de alguna
relación anotada. Uso: python3 src/make_splits.py
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML = ROOT / "data/raw/Rad-SpRL.xml"
DEFAULT_OUTPUT = ROOT / "data/splits/radsprl_v1.json"
SEED = 42


def make_splits(xml_path: Path, output_path: Path) -> None:
    documents = ET.parse(xml_path).getroot().findall("Document")
    groups: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for document in documents:
        identifier = document.attrib["id"]
        text = document.findtext("Text")
        annotations = document.find("Annotations")
        if text is None or annotations is None:
            raise ValueError(f"Documento incompleto: {identifier}")
        digest = sha256(text.encode("utf-8")).hexdigest()
        groups[digest].append((identifier, bool(annotations.findall("RadSpRLRelation"))))

    strata: dict[str, list[list[str]]] = {"con_relacion": [], "sin_relacion": []}
    for digest, entries in sorted(groups.items()):
        statuses = {status for _, status in entries}
        if len(statuses) != 1:
            raise ValueError(f"Duplicados con etiquetas incompatibles: {digest}")
        key = "con_relacion" if True in statuses else "sin_relacion"
        strata[key].append(sorted(identifier for identifier, _ in entries))

    randomizer = random.Random(SEED)
    splits: dict[str, list[str]] = {"train": [], "dev": [], "test": []}
    for name, sets in strata.items():
        randomizer.shuffle(sets)
        total = sum(len(group) for group in sets)
        train_target = round(0.70 * total)
        dev_target = round(0.15 * total)
        counts = {split: 0 for split in splits}
        for group in sets:
            if counts["train"] < train_target:
                split = "train"
            elif counts["dev"] < dev_target:
                split = "dev"
            else:
                split = "test"
            splits[split].extend(group)
            counts[split] += len(group)
        print(f"{name}: total={total}; " + ", ".join(f"{s}={counts[s]}" for s in splits))

    for identifiers in splits.values():
        identifiers.sort()
    all_ids = [identifier for ids in splits.values() for identifier in ids]
    if len(all_ids) != len(documents) or len(set(all_ids)) != len(documents):
        raise ValueError("Partición incompleta o con identificadores duplicados")

    output = {
        "dataset": "Rad-SpRL.xml (krobertslab/datasets, master)",
        "source_sha256": sha256(xml_path.read_bytes()).hexdigest(),
        "seed": SEED,
        "method": "70/15/15 aprox.; estratificado por presencia de relación; texto idéntico agrupado",
        "splits": splits,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Escrito: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, default=DEFAULT_XML)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    make_splits(args.xml, args.output)
