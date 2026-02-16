import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QTextEdit

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pee.gui.analysis import AnalysisWidget

# Create QApplication instance if it doesn't exist
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

class TestAnalysisWidgetLogic(unittest.TestCase):
    def setUp(self):
        self.widget = AnalysisWidget()

    def test_display_results_formatting(self):
        results = {
            "baseline_window": {
                "start": "2023-01-01",
                "end": "2023-01-07",
                "count": 7,
                "mean": 10.0,
                "std": 1.0
            },
            "intervention_window": {
                "start": "2023-01-08",
                "end": "2023-01-14",
                "count": 7,
                "mean": 12.0,
                "std": 1.0
            },
            "analysis": {
                "mean_difference": 2.0,
                "cohens_d": 2.0,
                "t_test": {"p_value": 0.05},
                "mann_whitney_u": {"p_value": 0.06}
            },
            "warnings": ["Small sample size"]
        }

        self.widget.display_results(results, "Test Intervention", "Test Metric")

        plain_text = self.widget.results_text.toPlainText()

        self.assertIn("Test Intervention", plain_text)
        self.assertIn("Test Metric", plain_text)
        self.assertIn("Mean Difference: 2.00", plain_text)
        self.assertIn("Small sample size", plain_text)

        html_content = self.widget.results_text.toHtml()
        # PyQt converts named colors to hex
        self.assertTrue("color:#ffa500" in html_content or "color:orange" in html_content)

    def test_display_error(self):
        results = {"error": "Insufficient data"}
        self.widget.display_results(results, "Test Intervention", "Test Metric")

        plain_text = self.widget.results_text.toPlainText()
        self.assertIn("Insufficient data", plain_text)

        html_content = self.widget.results_text.toHtml()
        self.assertTrue("color:#ff0000" in html_content or "color:red" in html_content)

if __name__ == '__main__':
    unittest.main()
