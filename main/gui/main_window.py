import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QSplitter
)
from PyQt6.QtCore import Qt
from typing import Optional
 
from main.gui.interventions import InterventionsWidget
from main.gui.metrics import MetricDefinitionWidget, LoggingWidget
from main.gui.events import EventsWidget
from main.gui.analysis import AnalysisWidget
from main.gui.data_management import DataManagementWidget
from main.gui.summarizer import SummarizerWidget
from main.gui.settings import SettingsWidget
from main.core.database import Base, engine

logger = logging.getLogger(__name__)

class WorkspaceWidget(QWidget):
    """A widget that encapsulates the main experiment workflow."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Top part: Interventions list
        self.interventions_widget = InterventionsWidget()

        # Bottom part: Tabs for the selected intervention
        self.intervention_tabs = QTabWidget()
        self.metric_setup_tab = MetricDefinitionWidget()
        self.logging_tab = LoggingWidget()
        self.events_tab = EventsWidget()
        self.analysis_tab = AnalysisWidget()

        self.intervention_tabs.addTab(self.metric_setup_tab, "Metric Setup")
        self.intervention_tabs.addTab(self.logging_tab, "Logging")
        self.intervention_tabs.addTab(self.events_tab, "Events")
        self.intervention_tabs.addTab(self.analysis_tab, "Analysis")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.interventions_widget)
        splitter.addWidget(self.intervention_tabs)
        splitter.setSizes([250, 550])  # Initial sizes

        self.layout.addWidget(splitter)

        self.interventions_widget.interventionSelected.connect(self.on_intervention_selected)
        self.on_intervention_selected(None)

    def on_intervention_selected(self, intervention_id: Optional[int]):
        """Propagates the selected intervention to child tabs."""
        is_selected = intervention_id is not None

        # Enable/disable tabs individually. Metric Setup is always enabled.
        for i in range(self.intervention_tabs.count()):
            widget = self.intervention_tabs.widget(i)
            if isinstance(widget, MetricDefinitionWidget):
                self.intervention_tabs.setTabEnabled(i, True)
            else:
                self.intervention_tabs.setTabEnabled(i, is_selected)

        self.logging_tab.set_current_intervention(intervention_id)
        self.events_tab.set_current_intervention(intervention_id)
        self.analysis_tab.set_current_intervention(intervention_id)

    def refresh_workspace(self):
        """Refreshes the data in the workspace view."""
        self.interventions_widget.refresh_table()
        self.metric_setup_tab.refresh_table()
        current_id = self.interventions_widget.get_selected_intervention_id()
        self.on_intervention_selected(current_id)

class MainWindow(QMainWindow):
    """The main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Experiment Engine")
        self.resize(1000, 800)

        # Ensure DB tables exist
        Base.metadata.create_all(bind=engine)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()

        self.workspace_tab = WorkspaceWidget()
        self.summarizer_tab = SummarizerWidget()
        self.data_tab = DataManagementWidget()
        self.settings_tab = SettingsWidget()

        self.tabs.addTab(self.workspace_tab, "Workspace")
        self.tabs.addTab(self.summarizer_tab, "Summarizer")
        self.tabs.addTab(self.data_tab, "Data Management")
        self.tabs.addTab(self.settings_tab, "Settings")

        self.layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.on_tab_change)

    def on_tab_change(self, index: int) -> None:
        """Handles tab change events to refresh data in the selected tab."""
        widget = self.tabs.widget(index)
        if widget == self.workspace_tab:
            self.workspace_tab.refresh_workspace()
        elif widget == self.summarizer_tab:
             self.summarizer_tab.refresh_interventions()
        elif widget == self.settings_tab:
             widget.load_settings()
