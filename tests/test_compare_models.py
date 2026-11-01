"""Prueba de comparación apareada sin depender del corpus local."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compare_models import compare  # noqa: E402


class CompareTests(unittest.TestCase):
    def test_better_predictions_have_positive_delta(self) -> None:
        gold = [{"id": "one", "tokens": [{"text": "opacity"}, {"text": "in"}],
                 "relations": [{"indicator": {"segments": [[1, 2]]}, "roles": [
                     {"name": "Trajector", "span": {"segments": [[0, 1]]}},
                 ]}]},
                {"id": "two", "tokens": [{"text": "scar"}, {"text": "in"}],
                 "relations": [{"indicator": {"segments": [[1, 2]]}, "roles": [
                     {"name": "Trajector", "span": {"segments": [[0, 1]]}},
                 ]}]}]
        first = []
        second = [{"id": identifier, "indicator": {"segments": [[1, 2]]}, "roles": [
            {"name": "Trajector", "span": {"segments": [[0, 1]]}},
        ]} for identifier in ("one", "two")]
        result = compare(gold, first, second, draws=100, seed=42)
        self.assertEqual(result["delta_f1"], 1.0)
        self.assertEqual(result["paired_bootstrap_delta_95pct"], [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
