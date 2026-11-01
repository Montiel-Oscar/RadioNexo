"""Pruebas del esquema BIO y del contexto condicionado al indicador."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from train_crf import decode, features, labels  # noqa: E402


class CrfRepresentationTests(unittest.TestCase):
    def test_multiple_mentions_round_trip(self) -> None:
        document = {
            "tokens": [{"text": word} for word in
                       ("effusion", "and", "opacity", "in", "left", "lung")],
            "sentences": [[0, 6]],
        }
        relation = {"indicator": {"segments": [[3, 4]]}, "roles": [
            {"name": "Trajector", "span": {"segments": [[0, 1]]}},
            {"name": "Trajector", "span": {"segments": [[2, 3]]}},
        ]}
        xseq, left, right = features(document, relation)
        yseq, skipped = labels(document, relation, "Trajector", left, right)
        self.assertEqual(len(xseq), 6)
        self.assertEqual(decode(yseq, left), [(0, 1), (2, 3)])
        self.assertFalse(skipped)

    def test_features_do_not_consult_gold_roles(self) -> None:
        document = {"tokens": [{"text": word} for word in ("opacity", "in", "lung")],
                    "sentences": [[0, 3]]}
        relation = {"indicator": {"segments": [[1, 2]]}, "roles": []}
        xseq = features(document, relation)
        relation["roles"] = [{"name": "Trajector", "span": {"segments": [[0, 1]]}}]
        self.assertEqual(xseq, features(document, relation))

    def test_discontinuous_role_is_split_and_reported(self) -> None:
        document = {"tokens": [{"text": word} for word in
                               ("old", "and", "new", "changes", "in", "lung")],
                    "sentences": [[0, 6]]}
        relation = {"indicator": {"segments": [[4, 5]]}, "roles": [
            {"name": "Trajector", "span": {"segments": [[0, 1], [3, 4]]}},
        ]}
        tags, skipped = labels(document, relation, "Trajector", 0, 6)
        self.assertEqual(decode(tags, 0), [(0, 1), (3, 4)])
        self.assertEqual(skipped["discontinuous_mentions_split"], 1)


if __name__ == "__main__":
    unittest.main()
