"""Muestra ejemplos sólo de entrenamiento para revisar el esquema a mano.

Uso: python3 src/inspect_cases.py
No escribe ni publica textos del corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

from corpus import Document, Relation, load_corpus


ROOT = Path(__file__).resolve().parents[1]


def category(document: Document, relation: Relation | None) -> str | None:
    if relation is None:
        return "sin_relacion"
    role_names = [role.name for role in relation.roles]
    if any(len(role.span.segments) > 1 for role in relation.roles):
        return "discontinuo"
    if "Trajector" not in role_names or "Landmark" not in role_names:
        return "rol_ausente"
    if role_names.count("Trajector") > 1 or role_names.count("Landmark") > 1:
        return "roles_multiples"
    if role_names.count("Trajector") == 1 and role_names.count("Landmark") == 1:
        return "simple"
    return None


def show(document: Document, relation: Relation | None) -> None:
    print(f"Informe {document.identifier}")
    if relation is None:
        print("  Sin relaciones anotadas; no equivale necesariamente a informe normal.")
        return
    indicator = relation.indicator
    print(f"  Indicador: {document.text_of(indicator)!r} {indicator.as_dict()['segments']}")
    for role in relation.roles:
        print(f"  {role.name}: {document.text_of(role.span)!r} {role.span.as_dict()['segments']}")
    start = max(0, document.tokens[indicator.segments[0].start].start_char - 110)
    end = min(len(document.text), document.tokens[indicator.segments[-1].end - 1].end_char + 150)
    print("  Contexto:", repr(" ".join(document.text[start:end].split())))


def main() -> None:
    split_file = json.loads((ROOT / "data/splits/radsprl_v1.json").read_text(encoding="utf-8"))
    train_ids = set(split_file["splits"]["train"])
    wanted = {"sin_relacion", "discontinuo", "rol_ausente", "roles_multiples", "simple"}
    for document in load_corpus(ROOT / "data/raw/Rad-SpRL.xml"):
        if document.identifier not in train_ids:
            continue
        candidates = document.relations or (None,)
        for relation in candidates:
            label = category(document, relation)
            if label in wanted:
                print(f"\n[{label}]")
                show(document, relation)
                wanted.remove(label)
        if not wanted:
            break
    if wanted:
        raise RuntimeError(f"No se encontraron ejemplos de entrenamiento: {sorted(wanted)}")


if __name__ == "__main__":
    main()
