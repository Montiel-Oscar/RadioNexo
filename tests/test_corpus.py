"""Pruebas de offsets, roles múltiples y fragmentos discontinuos."""

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from corpus import load_corpus, parse_document  # noqa: E402


SAMPLE = """<Document id="example">
<Text>old and new changes in lung</Text>
<Annotations>
  <Token cs="0" cl="3"/><Token cs="4" cl="3"/>
  <Token cs="8" cl="3"/><Token cs="12" cl="7"/>
  <Token cs="20" cl="2"/><Token cs="23" cl="4"/>
  <Sentence ts="0" tl="6"/>
  <RadSpRLRelation ts="4" tl="1">
    <Trajector ts="0,3" tl="1,1" type="Disorder"/>
    <Trajector ts="2" tl="2" type="Disorder"/>
    <Landmark ts="5" tl="1" type="Anatomy"/>
  </RadSpRLRelation>
</Annotations></Document>"""


class CorpusTests(unittest.TestCase):
    def test_discontinuous_and_multiple_roles(self) -> None:
        document = parse_document(ET.fromstring(SAMPLE))
        self.assertEqual(len(document.tokens), 6)
        self.assertEqual(len(document.relations), 1)
        relation = document.relations[0]
        self.assertEqual(document.text_of(relation.indicator), "in")
        self.assertEqual(document.text_of(relation.roles[0].span), "old … changes")
        self.assertEqual(document.text_of(relation.roles[1].span), "new changes")
        self.assertEqual(document.text_of(relation.roles[2].span), "lung")
        self.assertEqual(relation.roles[0].span.as_dict(), {"segments": [[0, 1], [3, 4]]})
        self.assertEqual(len(document.as_dict()["relations"][0]["roles"]), 3)

    def test_out_of_range_role_fails(self) -> None:
        broken = SAMPLE.replace('ts="5" tl="1" type="Anatomy"',
                                'ts="6" tl="1" type="Anatomy"')
        with self.assertRaises(ValueError):
            parse_document(ET.fromstring(broken))

    def test_real_corpus_and_split_when_available(self) -> None:
        raw = ROOT / "data/raw/Rad-SpRL.xml"
        if not raw.exists():
            self.skipTest("La copia local del corpus no está presente")
        documents = load_corpus(raw)
        self.assertEqual(len(documents), 2000)
        self.assertEqual(sum(len(doc.relations) for doc in documents), 2028)

        manifest = json.loads((ROOT / "data/splits/radsprl_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_sha256"], sha256(raw.read_bytes()).hexdigest())
        splits = manifest["splits"]
        self.assertEqual([len(splits[key]) for key in ("train", "dev", "test")], [1400, 300, 300])
        all_ids = [identifier for values in splits.values() for identifier in values]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertEqual(set(all_ids), {doc.identifier for doc in documents})


if __name__ == "__main__":
    unittest.main()
