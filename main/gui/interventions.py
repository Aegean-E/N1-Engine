import logging
from typing import Dict, Any, Optional
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QDateEdit, QDialogButtonBox, QCheckBox,
    QMenu, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate, QPoint, pyqtSignal
from PyQt6.QtGui import QAction
from sqlalchemy.orm import Session
 
from main.core.database import SessionLocal
from main.core.models import Intervention
from main.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class DateTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem for sorting dates, including None values."""
    def __lt__(self, other: QTableWidgetItem) -> bool:
        # Get the date objects stored in the UserRole
        d1 = self.data(Qt.ItemDataRole.UserRole)
        d2 = other.data(Qt.ItemDataRole.UserRole)

        # Handle None (representing active/no end date)
        if d1 is None and d2 is None:
            return False  # Equal
        if d1 is None:
            return False  # None is considered "greater" than any date, so it comes last when sorting ascending
        if d2 is None:
            return True   # Any date is "less" than None

        # If both are dates, compare them
        if isinstance(d1, date) and isinstance(d2, date):
            return d1 < d2
        
        # Fallback to string comparison if types are unexpected
        return super().__lt__(other)

class InterventionDialog(QDialog):
    """Dialog for adding or editing an intervention."""
    def __init__(self, parent: Optional[QWidget] = None, intervention_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Intervention Details")
        self.setMinimumWidth(400)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.start_date_input = QDateEdit(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)

        self.projected_end_date_checkbox = QCheckBox("Set Projected End Date")
        self.projected_end_date_input = QDateEdit(QDate.currentDate())
        self.projected_end_date_input.setCalendarPopup(True)
        self.projected_end_date_input.setEnabled(False)
        self.projected_end_date_checkbox.toggled.connect(self.projected_end_date_input.setEnabled)

        self.end_date_checkbox = QCheckBox("Set Actual End Date")
        self.end_date_input = QDateEdit(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setEnabled(False)
        self.end_date_checkbox.toggled.connect(self.end_date_input.setEnabled)

        self.notes_input = QLineEdit()

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Start Date:", self.start_date_input)
        self.layout.addRow(self.projected_end_date_checkbox, self.projected_end_date_input)
        self.layout.addRow(self.end_date_checkbox, self.end_date_input)
        self.layout.addRow("Notes:", self.notes_input)

        # Populate if editing
        if intervention_data:
            self.name_input.setText(intervention_data.get("name", ""))
            if intervention_data.get("start_date"):
                self.start_date_input.setDate(intervention_data["start_date"])
            if intervention_data.get("projected_end_date"):
                self.projected_end_date_checkbox.setChecked(True)
                self.projected_end_date_input.setDate(intervention_data["projected_end_date"])
            if intervention_data.get("end_date"):
                self.end_date_checkbox.setChecked(True)
                self.end_date_input.setDate(intervention_data["end_date"])
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
            "projected_end_date": self.projected_end_date_input.date().toPyDate() if self.projected_end_date_checkbox.isChecked() else None,
            "end_date": self.end_date_input.date().toPyDate() if self.end_date_checkbox.isChecked() else None,
            "notes": self.notes_input.text()
        }

class InterventionsWidget(QWidget):
    interventionSelected = pyqtSignal(object)  # Emits int ID or None

    """Widget for managing interventions."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6) # Name, Status, Start, Projected End, End, Notes
        self.table.setHorizontalHeaderLabels(["Name", "Status", "Start Date", "Projected End Date", "End Date", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.edit_selected_intervention)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
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

    def on_selection_changed(self):
        """Emits the ID of the currently selected intervention."""
        intervention_id = self.get_selected_intervention_id()
        self.interventionSelected.emit(intervention_id)

    def get_selected_intervention_id(self) -> Optional[int]:
        """Helper to get the ID of the selected row."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def refresh_table(self) -> None:
        """Refreshes the interventions table from the database."""
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            self.table.setSortingEnabled(False) # Disable sorting during population for performance
            interventions = db.query(Intervention).all()
            self.table.setRowCount(len(interventions))
            for i, intervention in enumerate(interventions):
                # Column 0: Name
                name_item = QTableWidgetItem(intervention.name)
                name_item.setData(Qt.ItemDataRole.UserRole, intervention.id) # Store ID for actions
                self.table.setItem(i, 0, name_item)

                # Column 1: Status
                today = date.today()
                if intervention.end_date and intervention.end_date <= today:
                    status_str = "Closed"
                elif intervention.projected_end_date:
                    status_str = "Active (Projected)"
                else:
                    status_str = "Active"
                status_item = QTableWidgetItem(status_str)
                self.table.setItem(i, 1, status_item)

                # Column 2: Start Date
                start_date_item = DateTableWidgetItem(str(intervention.start_date))
                start_date_item.setData(Qt.ItemDataRole.UserRole, intervention.start_date)
                self.table.setItem(i, 2, start_date_item)

                # Column 3: Projected End Date
                projected_end_date_str = str(intervention.projected_end_date) if intervention.projected_end_date else ""
                projected_end_date_item = DateTableWidgetItem(projected_end_date_str)
                projected_end_date_item.setData(Qt.ItemDataRole.UserRole, intervention.projected_end_date)
                self.table.setItem(i, 3, projected_end_date_item)

                # Column 4: End Date
                end_date_str = str(intervention.end_date) if intervention.end_date else ""
                end_date_item = DateTableWidgetItem(end_date_str)
                end_date_item.setData(Qt.ItemDataRole.UserRole, intervention.end_date)
                self.table.setItem(i, 4, end_date_item)

                # Column 5: Notes
                notes_item = QTableWidgetItem(intervention.notes or "")
                self.table.setItem(i, 5, notes_item)
        except Exception as e:
            show_error(self, "Failed to load interventions", str(e))
        finally:
            db.close()
            self.table.setSortingEnabled(True)

    def add_intervention(self) -> None:
        """Opens the dialog to add a new intervention."""
        dialog = InterventionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"]:
                show_error(self, "Validation Error", "Name is required.")
                return
            
            if data.get("end_date") and data["end_date"] < data["start_date"]:
                show_error(self, "Validation Error", "End date cannot be before start date.")
                return
            if data.get("projected_end_date") and data["projected_end_date"] < data["start_date"]:
                show_error(self, "Validation Error", "Projected end date cannot be before start date.")
                return

            db = SessionLocal()
            try:
                intervention = Intervention(
                    name=data["name"],
                    start_date=data["start_date"],
                    projected_end_date=data.get("projected_end_date"),
                    end_date=data.get("end_date"),
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

        # 1. Fetch data
        db = SessionLocal()
        try:
            intervention = db.query(Intervention).get(intervention_id)
            if not intervention:
                show_error(self, "Error", "Intervention not found.")
                return

            data = {
                "name": intervention.name,
                "start_date": intervention.start_date,
                "projected_end_date": intervention.projected_end_date,
                "end_date": intervention.end_date,
                "notes": intervention.notes
            }
        finally:
            db.close()

        # 2. Dialog interaction (outside session)
        dialog = InterventionDialog(self, intervention_data=data)
        if dialog.exec():
            new_data = dialog.get_data()
            if not new_data["name"]:
                show_error(self, "Validation Error", "Name is required.")
                return
            
            if new_data.get("end_date") and new_data["end_date"] < new_data["start_date"]:
                show_error(self, "Validation Error", "End date cannot be before start date.")
                return
            if new_data.get("projected_end_date") and new_data["projected_end_date"] < new_data["start_date"]:
                show_error(self, "Validation Error", "Projected end date cannot be before start date.")
                return

            # 3. Update
            db = SessionLocal()
            try:
                intervention = db.query(Intervention).get(intervention_id)
                if intervention:
                    intervention.name = new_data["name"]
                    intervention.start_date = new_data["start_date"]
                    intervention.projected_end_date = new_data.get("projected_end_date")
                    intervention.end_date = new_data.get("end_date")
                    intervention.notes = new_data["notes"]

                    db.commit()
                    self.refresh_table()
                else:
                    show_error(self, "Error", "Intervention no longer exists.")
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

        db = SessionLocal()
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
