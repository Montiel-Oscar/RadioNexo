"""Invariantes del resumen público y de la función de métricas."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from visual_stats import metrics


class VisualStatsTests(unittest.TestCase):
    def test_metrics(self):
        result = metrics(2, 1, 1)
        self.assertEqual(result["f1"], 2 / 3)
        self.assertEqual(metrics(0, 0, 0)["f1"], 0)

    def test_public_summary_is_aggregate_and_consistent(self):
        stats = json.loads((ROOT / "results/visualization_stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["documents"], 300)
        self.assertEqual(stats["gold_mentions"], 591)
        self.assertEqual(sum(row["gold"] for row in stats["gold_length_recall"]), 591)
        self.assertEqual(sum(stats["document_f1_comparison"]["CRF_vs_Reglas"].values()), 158)
        self.assertEqual(stats["methods"]["CRF"]["overall_micro"]["tp"], 521)
        self.assertNotIn("tokens", stats)


if __name__ == "__main__":
    unittest.main()
