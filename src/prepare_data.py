"""Convierte Rad-SpRL a JSONL local usando la partición registrada.

Por defecto prepara sólo train y dev. El conjunto test se prepara explícitamente
al final del desarrollo con ``--split test``.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from corpus import load_corpus


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "data/raw/Rad-SpRL.xml"
SPLIT_PATH = ROOT / "data/splits/radsprl_v1.json"
OUTPUT_DIR = ROOT / "data/processed"


def prepare(splits: list[str]) -> None:
    manifest = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    digest = sha256(XML_PATH.read_bytes()).hexdigest()
    if digest != manifest["source_sha256"]:
        raise ValueError("El XML local no coincide con la partición; revisar versión antes de continuar")

    documents = {document.identifier: document for document in load_corpus(XML_PATH)}
    all_ids = [identifier for ids in manifest["splits"].values() for identifier in ids]
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != set(documents):
        raise ValueError("La partición no cubre exactamente los informes del XML")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for split in splits:
        output_path = OUTPUT_DIR / f"{split}.jsonl"
        with output_path.open("w", encoding="utf-8") as handle:
            for identifier in manifest["splits"][split]:
                handle.write(json.dumps(documents[identifier].as_dict(), ensure_ascii=False) + "\n")
        print(f"{split}: {len(manifest['splits'][split])} informes -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("train", "dev", "test"), action="append")
    args = parser.parse_args()
    prepare(args.split or ["train", "dev"])
