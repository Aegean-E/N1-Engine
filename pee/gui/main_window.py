import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget
)

from pee.gui.interventions import InterventionsWidget
from pee.gui.metrics import MetricsWidget
from pee.gui.events import EventsWidget
from pee.gui.analysis import AnalysisWidget
from pee.core.database import Base, engine

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """The main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Experiment Engine (PEE)")
        self.resize(1000, 800)

        # Ensure DB tables exist
        Base.metadata.create_all(bind=engine)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.interventions_tab = InterventionsWidget()
        self.metrics_tab = MetricsWidget()
        self.events_tab = EventsWidget()
        self.analysis_tab = AnalysisWidget()

        self.tabs.addTab(self.interventions_tab, "Interventions")
        self.tabs.addTab(self.metrics_tab, "Metrics")
        self.tabs.addTab(self.events_tab, "Events")
        self.tabs.addTab(self.analysis_tab, "Analysis")

        # Connect tab change to refresh data if needed
        self.tabs.currentChanged.connect(self.on_tab_change)

    def on_tab_change(self, index: int) -> None:
        """Handles tab change events to refresh data in the selected tab."""
        widget = self.tabs.widget(index)
        if widget == self.analysis_tab:
            self.analysis_tab.refresh_data()
        elif widget == self.interventions_tab:
             self.interventions_tab.refresh_table()
        elif widget == self.metrics_tab:
             self.metrics_tab.refresh_metric_names()
