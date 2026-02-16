import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout,
    QLineEdit, QDateEdit, QSpinBox, QTextEdit, QTimeEdit
)
from PyQt6.QtCore import QDate, QTime
from sqlalchemy.orm import Session

from pee.core.database import SessionLocal
from pee.core.models import EventEntry
from pee.gui.utils import show_error, show_info

logger = logging.getLogger(__name__)

class EventsWidget(QWidget):
    """Widget for logging events."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.time_input = QTimeEdit(QTime.currentTime())

        self.event_name_input = QLineEdit()

        self.severity_input = QSpinBox()
        self.severity_input.setRange(1, 5)
        self.severity_input.setValue(1)
        self.severity_input.setToolTip("1 (Low) - 5 (High)")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)

        self.log_button = QPushButton("Log Event")
        self.log_button.clicked.connect(self.log_event)

        self.form_layout.addRow("Date:", self.date_input)
        self.form_layout.addRow("Time:", self.time_input)
        self.form_layout.addRow("Event Name:", self.event_name_input)
        self.form_layout.addRow("Severity (1-5):", self.severity_input)
        self.form_layout.addRow("Notes:", self.notes_input)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.log_button)
        self.layout.addStretch()

    def log_event(self) -> None:
        """Logs a new event to the database."""
        name = self.event_name_input.text()
        if not name:
            show_error(self, "Validation Error", "Event name is required.")
            return

        date_val = self.date_input.date().toPyDate()
        time_val = self.time_input.time().toPyTime()
        timestamp = datetime.combine(date_val, time_val)

        severity = self.severity_input.value()
        notes = self.notes_input.toPlainText()

        db = SessionLocal()
        try:
            event = EventEntry(
                timestamp=timestamp,
                event_name=name,
                severity=severity,
                notes=notes
            )
            db.add(event)
            db.commit()
        except Exception as e:
            db.rollback()
            show_error(self, "Failed to log event", str(e))
            return
        finally:
            db.close()

        show_info(self, "Event logged successfully.")

        # Clear inputs
        self.event_name_input.clear()
        self.notes_input.clear()
        self.severity_input.setValue(1)
