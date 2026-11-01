"""La demostración usa sólo frases inventadas y no necesita el corpus."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demo import document_from_sentence, describe


class DemoTests(unittest.TestCase):
    def test_indicator_and_surface(self):
        document = document_from_sentence(1, "opacity in the left lung .", "in")
        self.assertEqual(document["relations"][0]["indicator"]["segments"], [[1, 2]])
        frame = {
            "roles": [
                {"name": "Trajector", "span": {"segments": [[0, 1]]}},
                {"name": "Landmark", "span": {"segments": [[2, 5]]}},
            ]
        }
        self.assertEqual(describe(document, frame), "Trajector: opacity | Landmark: the left lung")

    def test_ambiguous_indicator_rejected(self):
        with self.assertRaises(ValueError):
            document_from_sentence(2, "in the lung and in the chest", "in")


if __name__ == "__main__":
    unittest.main()
