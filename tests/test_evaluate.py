"""Pruebas de la métrica exacta condicionada al indicador."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evaluate import score  # noqa: E402


GOLD = [{
    "id": "example",
    "tokens": [{"text": word} for word in ("old", "and", "new", "changes", "in", "lung")],
    "relations": [{
        "indicator": {"segments": [[4, 5]]},
        "roles": [
            {"name": "Trajector", "span": {"segments": [[0, 1], [3, 4]]}},
            {"name": "Trajector", "span": {"segments": [[2, 4]]}},
            {"name": "Landmark", "span": {"segments": [[5, 6]]}},
            {"name": "Hedge", "span": {"segments": [[1, 2]]}},
        ],
    }],
}]


class EvaluationTests(unittest.TestCase):
    def test_perfect_predictions(self) -> None:
        predictions = [{
            "id": "example", "indicator": {"segments": [[4, 5]]},
            "roles": [
                {"name": "Trajector", "span": {"segments": [[0, 1], [3, 4]]}},
                {"name": "Trajector", "span": {"segments": [[2, 4]]}},
                {"name": "Landmark", "span": {"segments": [[5, 6]]}},
            ],
        }]
        result = score(GOLD, predictions)
        self.assertEqual(result["overall_micro"]["f1"], 1.0)
        self.assertEqual(result["overall_micro"]["tp"], 3)
        self.assertEqual(result["overall_micro"]["fp"], 0)
        self.assertEqual(result["overall_micro"]["fn"], 0)

    def test_wrong_span_and_missing_role(self) -> None:
        predictions = [{
            "id": "example", "indicator": {"segments": [[4, 5]]},
            "roles": [{"name": "Trajector", "span": {"segments": [[0, 4]]}}],
        }]
        result = score(GOLD, predictions)["overall_micro"]
        self.assertEqual((result["tp"], result["fp"], result["fn"]), (0, 1, 3))
        self.assertEqual(result["f1"], 0.0)

    def test_omitted_frame_means_no_predictions(self) -> None:
        result = score(GOLD, [])["overall_micro"]
        self.assertEqual((result["tp"], result["fp"], result["fn"]), (0, 0, 3))

    def test_unknown_indicator_rejected(self) -> None:
        predictions = [{"id": "example", "indicator": {"segments": [[1, 2]]}, "roles": []}]
        with self.assertRaises(ValueError):
            score(GOLD, predictions)

    def test_duplicate_prediction_rejected(self) -> None:
        mention = {"name": "Landmark", "span": {"segments": [[5, 6]]}}
        predictions = [{"id": "example", "indicator": {"segments": [[4, 5]]},
                        "roles": [mention, mention]}]
        with self.assertRaises(ValueError):
            score(GOLD, predictions)


if __name__ == "__main__":
    unittest.main()
