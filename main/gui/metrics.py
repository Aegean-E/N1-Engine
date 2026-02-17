import logging
from datetime import date
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout,
    QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox
)
from PyQt6.QtCore import QDate
from sqlalchemy.orm import Session
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
 
from main.core.database import SessionLocal
from main.core.models import MetricEntry
from main.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class MetricsWidget(QWidget):
    """Widget for logging and visualizing metrics."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Input Form
        self.input_group = QGroupBox("Log Metric")
        self.input_layout = QFormLayout()

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.metric_name_input = QComboBox()
        self.metric_name_input.setEditable(True)
        # self.refresh_metric_names() # Called at end of init

        self.value_input = QDoubleSpinBox()
        self.value_input.setRange(-10000.0, 10000.0)
        self.value_input.setDecimals(2)

        self.log_button = QPushButton("Log Metric")
        self.log_button.clicked.connect(self.log_metric)

        self.input_layout.addRow("Date:", self.date_input)
        self.input_layout.addRow("Metric Name:", self.metric_name_input)
        self.input_layout.addRow("Value:", self.value_input)
        self.input_layout.addRow(self.log_button)
        self.input_group.setLayout(self.input_layout)
        self.layout.addWidget(self.input_group)

        # Plot
        self.plot_group = QGroupBox("Visualize Metric")
        self.plot_layout = QVBoxLayout()
        self.metric_selector = QComboBox()
        self.metric_selector.currentTextChanged.connect(self.update_plot)
        self.plot_layout.addWidget(self.metric_selector)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.plot_layout.addWidget(self.canvas)
        self.plot_group.setLayout(self.plot_layout)
        self.layout.addWidget(self.plot_group)

        self.refresh_metric_names()

    def refresh_metric_names(self) -> None:
        """Loads available metric names from the database into combo boxes."""
        db = SessionLocal()
        try:
            metrics = db.query(MetricEntry.metric_name).distinct().all()
            metric_names: List[str] = [m[0] for m in metrics]
        except Exception as e:
            show_error(self, "Failed to load metric names", str(e))
            return
        finally:
            db.close()

        # Update input combo
        current_text = self.metric_name_input.currentText()
        self.metric_name_input.clear()
        self.metric_name_input.addItems(metric_names)
        self.metric_name_input.setCurrentText(current_text)

        # Update selector combo
        current_selector = self.metric_selector.currentText()
        self.metric_selector.clear()
        self.metric_selector.addItems(metric_names)
        if current_selector in metric_names:
            self.metric_selector.setCurrentText(current_selector)

        self.update_plot()

    def log_metric(self) -> None:
        """Logs a new metric entry to the database."""
        name = self.metric_name_input.currentText()
        if not name:
            show_error(self, "Validation Error", "Metric name is required.")
            return

        date_val = self.date_input.date().toPyDate()
        value = self.value_input.value()

        db = SessionLocal()
        try:
            metric = MetricEntry(
                date=date_val,
                metric_name=name,
                value=value
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            db.rollback()
            show_error(self, "Failed to log metric", str(e))
            return
        finally:
            db.close()

        show_info(self, "Metric logged successfully.")
        self.refresh_metric_names()

    def update_plot(self) -> None:
        """Updates the time-series plot for the selected metric."""
        metric_name = self.metric_selector.currentText()
        if not metric_name:
            return

        db = SessionLocal()
        try:
            entries = db.query(MetricEntry).filter(MetricEntry.metric_name == metric_name).order_by(MetricEntry.date).all()
            if not entries:
                # Should we clear the plot if no entries? Yes.
                dates = []
                values = []
            else:
                dates = [e.date for e in entries]
                values = [e.value for e in entries]
        except Exception as e:
            logger.error(f"Plot update failed: {e}")
            return
        finally:
            db.close()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if dates:
            ax.plot(dates, values, marker='o')
        ax.set_title(f"Time Series: {metric_name}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.grid(True)
        self.figure.tight_layout()
        self.canvas.draw()
