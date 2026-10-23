"""B5 measured zero is not absent data; empty axes cannot imply zero values."""
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gazette_render as g


class MissingSnapshotTests(unittest.TestCase):
    def test_no_rated_events_is_not_measured_zero_percent(self):
        self.assertEqual(g.severity_summary([]), (None, None))
        self.assertEqual(g.severity_summary([{"severity": "Unrated"}]), (None, None))
        self.assertEqual(g.severity_summary([{"severity": "High"}, {"severity": "Unrated"}]), (1, 100.0))

    def test_zero_high_critical_with_actual_ratings_is_measured_zero(self):
        self.assertEqual(g.severity_summary([{"severity": "Low"}, {"severity": "Medium"}]), (0, 0.0))
        self.assertEqual(g.severity_summary([{"severity": "Critical"}, {"severity": "Low"}]), (1, 50.0))

    def test_empty_plot_does_not_show_artificial_zero_to_one_ticks(self):
        fig, ax = plt.subplots()
        try:
            g._no_plot_data(ax)
            self.assertEqual(len(ax.get_xticks()), 0)
            self.assertEqual(len(ax.get_yticks()), 0)
            self.assertEqual([item.get_text() for item in ax.texts], ["No verified snapshot"])
        finally:
            plt.close(fig)

    def test_measured_financial_zero_is_retained(self):
        original = {"pulse": {"valid": True, "mega_caps": [{"t": "SYN", "pct": 0.0}]}}
        self.assertEqual(g.prepare(original)["pulse"]["mega_caps"], [{"t": "SYN", "pct": 0.0}])
        self.assertEqual(g.pct(0), "+0.00%")


if __name__ == "__main__":
    unittest.main()
