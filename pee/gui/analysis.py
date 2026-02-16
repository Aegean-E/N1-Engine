import logging
import json
import pandas as pd
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout, QComboBox,
    QSpinBox, QTextEdit, QFileDialog, QGroupBox
)
from sqlalchemy.orm import Session

from pee.core.database import get_db
from pee.core.models import Intervention, MetricEntry
from pee.core.analysis import AnalysisEngine
from pee.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class AnalysisWidget(QWidget):
    """Widget for running analysis and displaying results."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Controls
        self.control_group = QGroupBox("Analysis Settings")
        self.form_layout = QFormLayout()

        self.intervention_combo = QComboBox()
        self.metric_combo = QComboBox()

        self.baseline_days = QSpinBox()
        self.baseline_days.setRange(1, 365)
        self.baseline_days.setValue(14)

        self.intervention_days = QSpinBox()
        self.intervention_days.setRange(1, 365)
        self.intervention_days.setValue(14)

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)

        self.form_layout.addRow("Intervention:", self.intervention_combo)
        self.form_layout.addRow("Metric:", self.metric_combo)
        self.form_layout.addRow("Baseline Days:", self.baseline_days)
        self.form_layout.addRow("Intervention Days:", self.intervention_days)
        self.form_layout.addRow(self.run_button)

        self.control_group.setLayout(self.form_layout)
        self.layout.addWidget(self.control_group)

        # Results
        self.results_group = QGroupBox("Results")
        self.results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_layout.addWidget(self.results_text)

        self.save_button = QPushButton("Save Report (JSON)")
        self.save_button.clicked.connect(self.save_report)
        self.save_button.setEnabled(False)
        self.results_layout.addWidget(self.save_button)

        self.results_group.setLayout(self.results_layout)
        self.layout.addWidget(self.results_group)

        self.refresh_data()
        self.current_results: Optional[Dict[str, Any]] = None

    def refresh_data(self) -> None:
        """Reloads interventions and metrics from the database."""
        db: Session = next(get_db())
        try:
            # Interventions
            interventions = db.query(Intervention).all()
            self.intervention_combo.clear()
            for i in interventions:
                self.intervention_combo.addItem(f"{i.name} ({i.start_date})", i.id)

            # Metrics
            metrics = db.query(MetricEntry.metric_name).distinct().all()
            self.metric_combo.clear()
            for m in metrics:
                self.metric_combo.addItem(m[0])

        except Exception as e:
            show_error(self, "Failed to load analysis options", str(e))
        finally:
            db.close()

    def run_analysis(self) -> None:
        """Runs the analysis based on selected inputs."""
        intervention_id = self.intervention_combo.currentData()
        metric_name = self.metric_combo.currentText()

        if not intervention_id or not metric_name:
             show_error(self, "Input Error", "Please select an intervention and a metric.")
             return

        b_days = self.baseline_days.value()
        i_days = self.intervention_days.value()

        db: Session = next(get_db())
        try:
            intervention = db.query(Intervention).get(intervention_id)
            if not intervention:
                show_error(self, "Error", "Intervention not found.")
                return

            # Fetch metric data
            entries = db.query(MetricEntry).filter(
                MetricEntry.metric_name == metric_name
            ).order_by(MetricEntry.date).all()

            if not entries:
                show_error(self, "Error", "No data found for this metric.")
                return

            df = pd.DataFrame([{
                "date": e.date,
                "value": e.value,
                "metric_name": e.metric_name
            } for e in entries])

            # Ensure date is datetime64[ns]
            df['date'] = pd.to_datetime(df['date'])

            engine = AnalysisEngine()
            start_date = pd.to_datetime(intervention.start_date)

            results = engine.calculate_baseline_vs_intervention(
                metrics=df,
                start_date=start_date,
                baseline_days=b_days,
                intervention_days=i_days
            )

            self.display_results(results, intervention.name, metric_name)
            self.current_results = results
            self.current_results["intervention"] = intervention.name
            self.current_results["metric"] = metric_name
            self.save_button.setEnabled(True)

        except Exception as e:
            show_error(self, "Analysis Failed", str(e))
        finally:
            db.close()

    def display_results(self, results: Dict[str, Any], intervention_name: str, metric_name: str) -> None:
        """Displays the analysis results in the text area."""
        text = f"<h1>Analysis Report</h1>"
        text += f"<h3>Intervention: {intervention_name}</h3>"
        text += f"<h3>Metric: {metric_name}</h3>"

        if "error" in results:
            text += f"<p style='color:red'><b>Error:</b> {results['error']}</p>"
            if "baseline_count" in results:
                 text += f"<p>Baseline Count: {results['baseline_count']}</p>"
                 text += f"<p>Intervention Count: {results['intervention_count']}</p>"
            self.results_text.setHtml(text)
            return

        # Windows
        bw = results.get("baseline_window", {})
        iw = results.get("intervention_window", {})

        text += "<h4>Windows</h4>"
        text += f"<b>Baseline:</b> {bw.get('start')} to {bw.get('end')} (N={bw.get('count')}, Mean={bw.get('mean'):.2f}, Std={bw.get('std'):.2f})<br>"
        text += f"<b>Intervention:</b> {iw.get('start')} to {iw.get('end')} (N={iw.get('count')}, Mean={iw.get('mean'):.2f}, Std={iw.get('std'):.2f})<br>"

        # Stats
        an = results.get("analysis", {})
        text += "<h4>Statistics</h4>"
        text += f"<b>Mean Difference:</b> {an.get('mean_difference'):.2f}<br>"
        text += f"<b>Cohen's d:</b> {an.get('cohens_d'):.2f}<br>"

        tt = an.get("t_test", {})
        u = an.get("mann_whitney_u", {})

        p_t = tt.get("p_value")
        p_u = u.get("p_value")

        text += f"<b>T-Test p-value:</b> {p_t:.4f} " if p_t is not None else "<b>T-Test:</b> N/A "
        text += f"<b>Mann-Whitney U p-value:</b> {p_u:.4f}<br>" if p_u is not None else "<b>Mann-Whitney U:</b> N/A<br>"

        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            text += "<h4>Warnings (Scientific Rigor)</h4>"
            text += "<ul>"
            for w in warnings:
                text += f"<li style='color:orange'>{w}</li>"
            text += "</ul>"

        self.results_text.setHtml(text)

    def save_report(self) -> None:
        """Saves the current report to a JSON file."""
        if not self.current_results:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Report", "report.json", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.current_results, f, indent=4, default=str)
                show_info(self, f"Report saved to {filename}")
            except Exception as e:
                show_error(self, "Failed to save report", str(e))
