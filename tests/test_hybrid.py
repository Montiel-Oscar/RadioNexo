"""Pruebas de la regla híbrida preespecificada."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hybrid import combine  # noqa: E402


def frame(roles: list[dict]) -> dict:
    return {"id": "sample", "indicator": {"segments": [[2, 3]]}, "roles": roles}


def mention(name: str, start: int, end: int) -> dict:
    return {"name": name, "span": {"segments": [[start, end]]}}


class HybridTests(unittest.TestCase):
    def test_fallback_only_when_crf_role_empty(self) -> None:
        rules = [frame([mention("Trajector", 0, 1), mention("Landmark", 3, 4)])]
        crf = [frame([mention("Trajector", 0, 2)])]
        merged, info = combine(rules, crf)
        self.assertEqual(merged[0]["roles"],
                         [mention("Trajector", 0, 2), mention("Landmark", 3, 4)])
        self.assertEqual(info["fallback_mentions"], 1)

    def test_crf_multiple_mentions_are_preserved(self) -> None:
        rules = [frame([mention("Trajector", 0, 1)])]
        crf = [frame([mention("Trajector", 0, 1), mention("Trajector", 4, 5)])]
        merged, info = combine(rules, crf)
        self.assertEqual(len(merged[0]["roles"]), 2)
        self.assertEqual(info["fallback_mentions"], 0)

    def test_mismatched_indicators_rejected(self) -> None:
        rules = [frame([])]
        crf = [frame([])]
        crf[0]["id"] = "another"
        with self.assertRaises(ValueError):
            combine(rules, crf)


if __name__ == "__main__":
    unittest.main()
