import logging
from datetime import date
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout,
    QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox, QLabel,
    QTableWidget, QHeaderView, QTableWidgetItem, QDialog, QLineEdit, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import QDate, Qt
from sqlalchemy.orm import Session
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
 
from main.core.database import SessionLocal
from main.core.models import MetricEntry, MetricDefinition, Intervention
from main.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class LoggingWidget(QWidget):
    """Widget for logging metrics."""
    def __init__(self):
        self.current_intervention_id: Optional[int] = None
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Input Form
        self.input_group = QGroupBox("Log a Metric Value")
        self.input_layout = QFormLayout()

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.metric_name_input = QComboBox()
        self.metric_name_input.setEditable(False)

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

        # Plot (moved from MetricsWidget)
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

    def set_current_intervention(self, intervention_id: Optional[int]):
        """Sets the currently active intervention for logging and viewing."""
        self.current_intervention_id = intervention_id
        is_enabled = intervention_id is not None

        self.input_group.setEnabled(is_enabled)
        self.plot_group.setEnabled(is_enabled)

        if is_enabled:
            self.input_group.setTitle("Log Metric for Selected Intervention")
            self.plot_group.setTitle("Visualize Metric for Selected Intervention")
            self.refresh_combos()
        else:
            self.input_group.setTitle("Log a Metric Value (No Intervention Selected)")
            self.plot_group.setTitle("Visualize Metric (No Intervention Selected)")
            self.metric_name_input.clear()
            self.metric_selector.clear()
            self.update_plot()

    def refresh_combos(self) -> None:
        """Loads dropdown contents from the database."""
        db = SessionLocal()
        try:
            # Populate logging dropdown from definitions
            definitions = db.query(MetricDefinition.name).order_by(MetricDefinition.name).all()
            defined_names: List[str] = [d[0] for d in definitions]

            # Populate visualization dropdown from data logged for this intervention
            if self.current_intervention_id is not None:
                logged_metrics = db.query(MetricEntry.metric_name).filter(
                    MetricEntry.intervention_id == self.current_intervention_id
                ).distinct().order_by(MetricEntry.metric_name).all()
                logged_metric_names: List[str] = [m[0] for m in logged_metrics]
            else:
                logged_metric_names = []

        except Exception as e:
            show_error(self, "Failed to load dropdown lists", str(e))
            return
        finally:
            db.close()

        # Update input combo (for logging)
        current_input_text = self.metric_name_input.currentText()
        self.metric_name_input.clear()
        self.metric_name_input.addItems(defined_names)
        if current_input_text in defined_names:
            self.metric_name_input.setCurrentText(current_input_text)

        # Update selector combo (for plotting)
        current_selector_text = self.metric_selector.currentText()
        self.metric_selector.clear()
        self.metric_selector.addItems(logged_metric_names)
        if current_selector_text in logged_metric_names:
            self.metric_selector.setCurrentText(current_selector_text)
        self.update_plot()

    def log_metric(self) -> None:
        """Logs a new metric entry to the database."""
        name = self.metric_name_input.currentText()
        if not name:
            show_error(self, "Validation Error", "Metric name is required. Please define metrics in the 'Metric Setup' tab first.")
            return

        date_val = self.date_input.date().toPyDate()
        intervention_id = self.current_intervention_id
        if intervention_id is None:
            show_error(self, "Error", "No intervention selected to log against.")
            return

        value = self.value_input.value()

        db = SessionLocal()
        try:
            metric = MetricEntry(
                date=date_val,
                metric_name=name,
                value=value,
                intervention_id=intervention_id
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
        self.refresh_combos()

    def update_plot(self) -> None:
        """Updates the time-series plot for the selected metric."""
        metric_name = self.metric_selector.currentText()
        if not metric_name or self.current_intervention_id is None:
            self.figure.clear()
            self.canvas.draw()
            return

        db = SessionLocal()
        try:
            entries = db.query(MetricEntry).filter(
                MetricEntry.metric_name == metric_name,
                MetricEntry.intervention_id == self.current_intervention_id
            ).order_by(MetricEntry.date).all()

            if not entries:
                dates = []
                values = []
            else:
                dates = [e.date for e in entries]
                values = [e.value for e in entries]
        except Exception as e:
            logger.error(f"Plot update failed: {e}")
            self.figure.clear()
            self.canvas.draw()
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


class MetricDefinitionDialog(QDialog):
    """Dialog for adding or editing a metric definition."""
    def __init__(self, parent: Optional[QWidget] = None, metric_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Metric Definition")
        self.setMinimumWidth(400)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.unit_input = QLineEdit()

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.description_input)
        self.layout.addRow("Unit:", self.unit_input)

        if metric_data:
            self.name_input.setText(metric_data.get("name", ""))
            self.description_input.setPlainText(metric_data.get("description", ""))
            self.unit_input.setText(metric_data.get("unit", ""))

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self) -> Dict[str, Any]:
        return {
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "unit": self.unit_input.text()
        }

class MetricDefinitionWidget(QWidget):
    """Widget for defining and managing metrics."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Description", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_metric)
        self.layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Metric")
        self.add_button.clicked.connect(self.add_metric)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.clicked.connect(self.edit_metric)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_metric)
        button_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_layout)

        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            definitions = db.query(MetricDefinition).all()
            self.table.setRowCount(len(definitions))
            for i, definition in enumerate(definitions):
                self.table.setItem(i, 0, QTableWidgetItem(definition.name))
                self.table.setItem(i, 1, QTableWidgetItem(definition.description or ""))
                self.table.setItem(i, 2, QTableWidgetItem(definition.unit or ""))
                self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, definition.id)
        except Exception as e:
            show_error(self, "Failed to load metric definitions", str(e))
        finally:
            db.close()

    def add_metric(self):
        dialog = MetricDefinitionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"]:
                show_error(self, "Validation Error", "Metric name is required.")
                return
            
            db = SessionLocal()
            try:
                metric_def = MetricDefinition(**data)
                db.add(metric_def)
                db.commit()
                self.refresh_table()
            except Exception as e:
                db.rollback()
                show_error(self, "Failed to add metric definition", str(e))
            finally:
                db.close()

    def edit_metric(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        metric_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        db = SessionLocal()
        try:
            metric_def = db.query(MetricDefinition).get(metric_id)
            if not metric_def:
                show_error(self, "Error", "Metric definition not found.")
                return
            
            dialog = MetricDefinitionDialog(self, metric_data=metric_def.__dict__)
            if dialog.exec():
                data = dialog.get_data()
                if not data["name"]:
                    show_error(self, "Validation Error", "Metric name is required.")
                    return
                
                metric_def.name = data["name"]
                metric_def.description = data["description"]
                metric_def.unit = data["unit"]
                db.commit()
                self.refresh_table()
        except Exception as e:
            db.rollback()
            show_error(self, "Failed to edit metric definition", str(e))
        finally:
            db.close()

    def delete_metric(self):
        # This is a destructive action, maybe add a confirmation dialog later.
        # Also, consider what happens to MetricEntry data that uses this name.
        # For now, we just delete the definition.
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        metric_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        db = SessionLocal()
        try:
            metric_def = db.query(MetricDefinition).get(metric_id)
            if metric_def:
                db.delete(metric_def)
                db.commit()
                self.refresh_table()
        except Exception as e:
            db.rollback()
            show_error(self, "Failed to delete metric definition", str(e))
        finally:
            db.close()
