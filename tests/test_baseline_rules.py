"""Pruebas pequeñas de la línea base sin depender del corpus descargado."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baseline_rules import fit, predict  # noqa: E402
from evaluate import score  # noqa: E402


def example(identifier: str, with_gold: bool = True) -> dict:
    words = ("Small", "opacity", "in", "the", "left", "lower", "lung", ".")
    roles = [
        {"name": "Trajector", "span": {"segments": [[0, 2]]}},
        {"name": "Landmark", "span": {"segments": [[4, 7]]}},
    ] if with_gold else []
    return {
        "id": identifier, "tokens": [{"text": word} for word in words],
        "sentences": [[0, len(words)]],
        "relations": [{"indicator": {"segments": [[2, 3]]}, "roles": roles}],
    }


class BaselineTests(unittest.TestCase):
    def test_predicts_exact_roles_with_oracle_indicator(self) -> None:
        lexicon, sides = fit([example("train")])
        target = example("dev")
        result = score([target], predict(target, lexicon, sides))
        self.assertEqual(result["overall_micro"]["f1"], 1.0)

    def test_target_gold_roles_are_not_used(self) -> None:
        lexicon, sides = fit([example("train")])
        with_roles = example("dev", with_gold=True)
        without_roles = example("dev", with_gold=False)
        self.assertEqual(predict(with_roles, lexicon, sides),
                         predict(without_roles, lexicon, sides))

    def test_no_lexicon_match_means_no_role(self) -> None:
        lexicon, sides = fit([example("train")])
        target = example("dev", with_gold=False)
        target["tokens"][0]["text"] = "Unknown"
        target["tokens"][1]["text"] = "finding"
        predicted = predict(target, lexicon, sides)[0]["roles"]
        self.assertFalse(any(role["name"] == "Trajector" for role in predicted))


if __name__ == "__main__":
    unittest.main()
