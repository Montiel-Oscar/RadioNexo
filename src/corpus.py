"""Lector de Rad-SpRL y representación estable de sus anotaciones.

Los índices de tokens son de base cero y los extremos son exclusivos. Un
fragmento puede tener varios segmentos: no se convierte en una frase continua.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


ROLE_NAMES = frozenset({"Trajector", "Landmark", "Diagnosis", "Hedge"})


@dataclass(frozen=True)
class Segment:
    start: int
    end: int

    def as_list(self) -> list[int]:
        return [self.start, self.end]


@dataclass(frozen=True)
class Span:
    segments: tuple[Segment, ...]

    def as_dict(self) -> dict:
        return {"segments": [part.as_list() for part in self.segments]}


@dataclass(frozen=True)
class Token:
    start_char: int
    end_char: int
    text: str

    def as_dict(self) -> dict:
        return {"start_char": self.start_char, "end_char": self.end_char, "text": self.text}


@dataclass(frozen=True)
class Role:
    name: str
    entity_type: str | None
    span: Span

    def as_dict(self) -> dict:
        return {"name": self.name, "entity_type": self.entity_type, "span": self.span.as_dict()}


@dataclass(frozen=True)
class Relation:
    indicator: Span
    roles: tuple[Role, ...]

    def as_dict(self) -> dict:
        return {"indicator": self.indicator.as_dict(), "roles": [role.as_dict() for role in self.roles]}


@dataclass(frozen=True)
class Document:
    identifier: str
    text: str
    tokens: tuple[Token, ...]
    sentences: tuple[Segment, ...]
    relations: tuple[Relation, ...]

    def text_of(self, span: Span) -> str:
        """Devuelve el texto legible de cada segmento, sin fusionar discontinuos."""
        pieces: list[str] = []
        for part in span.segments:
            first = self.tokens[part.start]
            last = self.tokens[part.end - 1]
            pieces.append(self.text[first.start_char:last.end_char])
        return " … ".join(pieces)

    def as_dict(self) -> dict:
        return {
            "id": self.identifier,
            "text": self.text,
            "tokens": [token.as_dict() for token in self.tokens],
            "sentences": [sentence.as_list() for sentence in self.sentences],
            "relations": [relation.as_dict() for relation in self.relations],
        }


def parse_span(element: ET.Element, token_count: int) -> Span:
    """Interpreta los atributos ts/tl, incluidos los fragmentos discontinuos."""
    starts = [int(value) for value in element.attrib["ts"].split(",")]
    lengths = [int(value) for value in element.attrib["tl"].split(",")]
    if not starts or len(starts) != len(lengths):
        raise ValueError("ts y tl deben tener el mismo número de segmentos")
    segments = tuple(Segment(start, start + length) for start, length in zip(starts, lengths))
    if any(part.start < 0 or part.start >= part.end or part.end > token_count for part in segments):
        raise ValueError("fragmento fuera del rango de tokens")
    if any(left.end > right.start for left, right in zip(segments, segments[1:])):
        raise ValueError("segmentos superpuestos o desordenados")
    return Span(segments)


def parse_document(element: ET.Element) -> Document:
    identifier = element.attrib["id"]
    text = element.findtext("Text")
    annotations = element.find("Annotations")
    if text is None or annotations is None:
        raise ValueError(f"{identifier}: falta texto o anotaciones")

    tokens: list[Token] = []
    for token_element in annotations.findall("Token"):
        start = int(token_element.attrib["cs"])
        end = start + int(token_element.attrib["cl"])
        if start < 0 or end <= start or end > len(text):
            raise ValueError(f"{identifier}: offset de token inválido")
        tokens.append(Token(start, end, text[start:end]))

    sentences_list: list[Segment] = []
    for sentence in annotations.findall("Sentence"):
        parsed = parse_span(sentence, len(tokens))
        if len(parsed.segments) != 1:
            raise ValueError(f"{identifier}: oración discontinua inesperada")
        sentences_list.append(parsed.segments[0])
    sentences = tuple(sentences_list)
    relations: list[Relation] = []
    indicators: set[Span] = set()
    for relation_element in annotations.findall("RadSpRLRelation"):
        indicator = parse_span(relation_element, len(tokens))
        if indicator in indicators:
            raise ValueError(f"{identifier}: indicador duplicado")
        indicators.add(indicator)
        roles: list[Role] = []
        for role_element in relation_element:
            if role_element.tag not in ROLE_NAMES:
                raise ValueError(f"{identifier}: rol inesperado {role_element.tag}")
            roles.append(Role(
                name=role_element.tag,
                entity_type=role_element.attrib.get("type"),
                span=parse_span(role_element, len(tokens)),
            ))
        relations.append(Relation(indicator, tuple(roles)))
    return Document(identifier, text, tuple(tokens), sentences, tuple(relations))


def load_corpus(path: Path) -> list[Document]:
    """Carga el XML completo; su tamaño actual (~10 MB) cabe cómodamente en memoria."""
    root = ET.parse(path).getroot()
    documents = [parse_document(element) for element in root.findall("Document")]
    if root.attrib.get("numDocs") and int(root.attrib["numDocs"]) != len(documents):
        raise ValueError("numDocs no coincide con los documentos presentes")
    identifiers = [document.identifier for document in documents]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("identificadores de informe duplicados")
    return documents
