import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout,
    QSpinBox, QGroupBox
)
from main.core.settings_manager import settings_manager
from main.gui.utils import show_info

logger = logging.getLogger(__name__)

class SettingsWidget(QWidget):
    """Widget for managing application settings."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.settings_group = QGroupBox("Analysis Settings")
        self.form_layout = QFormLayout()

        self.min_baseline_days = QSpinBox()
        self.min_baseline_days.setRange(1, 90)
        self.form_layout.addRow("Minimum Baseline Days (for warnings):", self.min_baseline_days)

        self.min_intervention_days = QSpinBox()
        self.min_intervention_days.setRange(1, 90)
        self.form_layout.addRow("Minimum Intervention Days (for warnings):", self.min_intervention_days)

        self.min_data_points = QSpinBox()
        self.min_data_points.setRange(2, 20)
        self.form_layout.addRow("Minimum Data Points for Analysis:", self.min_data_points)

        self.max_safe_metrics = QSpinBox()
        self.max_safe_metrics.setRange(1, 20)
        self.form_layout.addRow("Multiple Comparison Warning Threshold:", self.max_safe_metrics)

        self.settings_group.setLayout(self.form_layout)
        self.layout.addWidget(self.settings_group)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

        self.layout.addStretch()

        self.load_settings()

    def load_settings(self):
        """Loads settings from the manager and updates the UI."""
        settings_manager.load_settings() # Ensure we have the latest from disk
        self.min_baseline_days.setValue(settings_manager.get("min_baseline_days", 7))
        self.min_intervention_days.setValue(settings_manager.get("min_intervention_days", 7))
        self.min_data_points.setValue(settings_manager.get("min_data_points", 3))
        self.max_safe_metrics.setValue(settings_manager.get("max_safe_metrics", 3))
        logger.info("Settings loaded into UI.")

    def save_settings(self):
        """Saves settings from the UI to the manager and file."""
        settings_manager.set("min_baseline_days", self.min_baseline_days.value())
        settings_manager.set("min_intervention_days", self.min_intervention_days.value())
        settings_manager.set("min_data_points", self.min_data_points.value())
        settings_manager.set("max_safe_metrics", self.max_safe_metrics.value())
        settings_manager.save_settings()
        show_info(self, "Settings have been saved.")