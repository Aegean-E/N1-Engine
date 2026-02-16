import logging
from typing import Dict, Any, Optional
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QDateEdit, QDialogButtonBox,
    QMenu, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate, QPoint
from PyQt6.QtGui import QAction
from sqlalchemy.orm import Session

from pee.core.database import get_db
from pee.core.models import Intervention
from pee.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class InterventionDialog(QDialog):
    """Dialog for adding or editing an intervention."""
    def __init__(self, parent: Optional[QWidget] = None, intervention_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Intervention Details")
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.start_date_input = QDateEdit(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        # End date is optional, so we need a way to represent "None".
        # We handle closing separately, so here we focus on core properties.

        self.dosage_input = QLineEdit()
        self.notes_input = QLineEdit()

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Start Date:", self.start_date_input)
        self.layout.addRow("Dosage:", self.dosage_input)
        self.layout.addRow("Notes:", self.notes_input)

        # Populate if editing
        if intervention_data:
            self.name_input.setText(intervention_data.get("name", ""))
            if intervention_data.get("start_date"):
                self.start_date_input.setDate(intervention_data["start_date"])
            self.dosage_input.setText(intervention_data.get("dosage", ""))
            self.notes_input.setText(intervention_data.get("notes", ""))

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self) -> Dict[str, Any]:
        """Returns the data entered in the dialog."""
        return {
            "name": self.name_input.text(),
            "start_date": self.start_date_input.date().toPyDate(),
            "dosage": self.dosage_input.text(),
            "notes": self.notes_input.text()
        }

class InterventionsWidget(QWidget):
    """Widget for managing interventions."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5) # Name, Start, End, Dosage, Notes
        self.table.setHorizontalHeaderLabels(["Name", "Start Date", "End Date", "Dosage", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_selected_intervention)

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Intervention")
        self.add_button.clicked.connect(self.add_intervention)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.clicked.connect(self.edit_selected_intervention)
        button_layout.addWidget(self.edit_button)

        self.close_button = QPushButton("Close Selected (End Now)")
        self.close_button.clicked.connect(self.close_selected_intervention)
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)

        self.refresh_table()

    def refresh_table(self) -> None:
        """Refreshes the interventions table from the database."""
        self.table.setRowCount(0)
        db: Session = next(get_db())
        try:
            interventions = db.query(Intervention).all()
            self.table.setRowCount(len(interventions))
            for i, intervention in enumerate(interventions):
                self.table.setItem(i, 0, QTableWidgetItem(intervention.name))
                self.table.setItem(i, 1, QTableWidgetItem(str(intervention.start_date)))
                self.table.setItem(i, 2, QTableWidgetItem(str(intervention.end_date) if intervention.end_date else "Active"))
                self.table.setItem(i, 3, QTableWidgetItem(intervention.dosage or ""))
                self.table.setItem(i, 4, QTableWidgetItem(intervention.notes or ""))

                # Store ID in the first item
                self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, intervention.id)
        except Exception as e:
            show_error(self, "Failed to load interventions", str(e))
        finally:
            db.close()

    def add_intervention(self) -> None:
        """Opens the dialog to add a new intervention."""
        dialog = InterventionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"]:
                show_error(self, "Validation Error", "Name is required.")
                return

            db: Session = next(get_db())
            try:
                intervention = Intervention(
                    name=data["name"],
                    start_date=data["start_date"],
                    dosage=data["dosage"],
                    notes=data["notes"]
                )
                db.add(intervention)
                db.commit()
                self.refresh_table()
            except Exception as e:
                db.rollback()
                show_error(self, "Failed to add intervention", str(e))
            finally:
                db.close()

    def edit_selected_intervention(self) -> None:
        """Opens dialog to edit the selected intervention."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        intervention_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        db: Session = next(get_db())
        try:
            intervention = db.query(Intervention).get(intervention_id)
            if not intervention:
                show_error(self, "Error", "Intervention not found.")
                return

            data = {
                "name": intervention.name,
                "start_date": intervention.start_date,
                "dosage": intervention.dosage,
                "notes": intervention.notes
            }

            dialog = InterventionDialog(self, intervention_data=data)
            if dialog.exec():
                new_data = dialog.get_data()
                if not new_data["name"]:
                    show_error(self, "Validation Error", "Name is required.")
                    return

                intervention.name = new_data["name"]
                intervention.start_date = new_data["start_date"]
                intervention.dosage = new_data["dosage"]
                intervention.notes = new_data["notes"]

                db.commit()
                self.refresh_table()

        except Exception as e:
            db.rollback()
            show_error(self, "Failed to edit intervention", str(e))
        finally:
            db.close()

    def close_selected_intervention(self) -> None:
        """Sets the end date of the selected intervention to today."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            show_info(self, "Please select an intervention to close.")
            return

        row = selected_rows[0].row()
        intervention_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        db: Session = next(get_db())
        try:
            intervention = db.query(Intervention).get(intervention_id)
            if not intervention:
                show_error(self, "Error", "Intervention not found.")
                return

            if intervention.end_date:
                show_info(self, "Intervention is already closed.")
                return

            intervention.end_date = date.today()
            db.commit()
            self.refresh_table()
            show_info(self, f"Intervention '{intervention.name}' closed.")

        except Exception as e:
            db.rollback()
            show_error(self, "Failed to close intervention", str(e))
        finally:
            db.close()

    def show_context_menu(self, pos: QPoint) -> None:
        """Shows context menu for table items."""
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        close_action = QAction("Close (End Now)", self)

        edit_action.triggered.connect(self.edit_selected_intervention)
        close_action.triggered.connect(self.close_selected_intervention)

        menu.addAction(edit_action)
        menu.addAction(close_action)

        menu.exec(self.table.mapToGlobal(pos))
