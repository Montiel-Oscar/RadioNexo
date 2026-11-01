"""Audita la estructura de Rad-SpRL sin modificar el corpus.

Uso: python src/audit_corpus.py [ruta/a/Rad-SpRL.xml]
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
import xml.etree.ElementTree as ET


ROLES = {"Trajector", "Landmark", "Diagnosis", "Hedge"}
DEFAULT_XML = Path(__file__).resolve().parents[1] / "data/raw/Rad-SpRL.xml"


def one_segment(text: str, tokens: list[ET.Element], start: int, length: int) -> str:
    """Reconstruye un segmento continuo a partir de índices de tokens."""
    if start < 0 or length < 1 or start + length > len(tokens):
        raise ValueError("token span fuera de rango")
    first = tokens[start]
    last = tokens[start + length - 1]
    char_start = int(first.attrib["cs"])
    char_end = int(last.attrib["cs"]) + int(last.attrib["cl"])
    if char_start < 0 or char_end > len(text) or char_start >= char_end:
        raise ValueError("character span fuera de rango")
    return text[char_start:char_end]


def token_text(text: str, tokens: list[ET.Element], starts: str, lengths: str) -> str:
    """Reconstruye uno o varios segmentos; Rad-SpRL usa comas para discontinuos."""
    start_parts = [int(value) for value in starts.split(",")]
    length_parts = [int(value) for value in lengths.split(",")]
    if len(start_parts) != len(length_parts):
        raise ValueError("número distinto de inicios y longitudes")
    return " … ".join(
        one_segment(text, tokens, start, length)
        for start, length in zip(start_parts, length_parts)
    )


def audit(path: Path) -> None:
    root = ET.parse(path).getroot()
    documents = root.findall("Document")
    counts: Counter[str] = Counter()
    indicators: Counter[str] = Counter()
    role_types: Counter[str] = Counter()
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    seen_indicators: set[tuple[str, str, str]] = set()
    errors: list[str] = []

    for document in documents:
        doc_id = document.attrib.get("id", "[sin id]")
        if doc_id in seen_ids:
            errors.append(f"{doc_id}: id repetido")
        seen_ids.add(doc_id)

        text = document.findtext("Text")
        annotations = document.find("Annotations")
        if text is None or annotations is None:
            errors.append(f"{doc_id}: falta texto o bloque de anotaciones")
            continue

        digest = sha256(text.encode("utf-8")).hexdigest()
        if digest in seen_texts:
            counts["textos_exactamente_duplicados"] += 1
        seen_texts.add(digest)

        tokens = annotations.findall("Token")
        sentences = annotations.findall("Sentence")
        relations = annotations.findall("RadSpRLRelation")
        counts["tokens"] += len(tokens)
        counts["oraciones"] += len(sentences)
        counts["relaciones"] += len(relations)
        if not relations:
            counts["informes_sin_relaciones"] += 1

        for index, token in enumerate(tokens):
            try:
                start = int(token.attrib["cs"])
                length = int(token.attrib["cl"])
                if start < 0 or length < 1 or start + length > len(text):
                    raise ValueError("offset inválido")
            except (KeyError, ValueError):
                errors.append(f"{doc_id}: token {index} fuera de rango")

        for index, sentence in enumerate(sentences):
            try:
                token_text(text, tokens, sentence.attrib["ts"], sentence.attrib["tl"])
            except (KeyError, ValueError):
                errors.append(f"{doc_id}: oración {index} fuera de rango")

        for index, relation in enumerate(relations):
            seen_indicators.add((doc_id, relation.attrib.get("ts", ""), relation.attrib.get("tl", "")))
            try:
                indicator = token_text(text, tokens, relation.attrib["ts"], relation.attrib["tl"])
                indicators[indicator.casefold()] += 1
            except (KeyError, ValueError):
                errors.append(f"{doc_id}: indicador de relación {index} fuera de rango")

            local_roles: Counter[str] = Counter()
            for role in relation:
                if role.tag not in ROLES:
                    errors.append(f"{doc_id}: rol desconocido {role.tag}")
                    continue
                local_roles[role.tag] += 1
                counts[f"menciones_{role.tag}"] += 1
                if "," in role.attrib.get("ts", ""):
                    counts["menciones_discontinuas"] += 1
                role_types[f"{role.tag}:{role.attrib.get('type', '[sin tipo]')}"] += 1
                try:
                    token_text(text, tokens, role.attrib["ts"], role.attrib["tl"])
                except (KeyError, ValueError):
                    errors.append(f"{doc_id}: {role.tag} de relación {index} fuera de rango")

            if local_roles["Trajector"] and local_roles["Landmark"]:
                counts["relaciones_con_hallazgo_y_ubicacion"] += 1
            if not local_roles["Trajector"]:
                counts["relaciones_sin_hallazgo"] += 1
            if not local_roles["Landmark"]:
                counts["relaciones_sin_ubicacion"] += 1
            if local_roles["Trajector"] > 1 or local_roles["Landmark"] > 1:
                counts["relaciones_con_roles_multiples"] += 1
            if local_roles["Hedge"]:
                counts["relaciones_con_hedge"] += 1

    print(f"Archivo: {path}")
    print(f"Documentos XML: {len(documents)} (atributo numDocs={root.attrib.get('numDocs')})")
    print(f"Indicadores distintos por documento y posición: {len(seen_indicators)}")
    for name, value in sorted(counts.items()):
        print(f"{name}: {value}")
    print("Indicadores más frecuentes:", indicators.most_common(12))
    print("Tipos de rol:", sorted(role_types.items()))
    print(f"Errores estructurales: {len(errors)}")
    for error in errors[:20]:
        print(" -", error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", nargs="?", type=Path, default=DEFAULT_XML)
    audit(parser.parse_args().xml)
