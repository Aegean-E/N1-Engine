import pytest
import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
from main.core.analysis import AnalysisEngine
from main.core.data_manager import DataManager
from main.core.models import MetricEntry, Intervention, EventEntry
from main.core.database import Base
from main.core.reporting import ReportGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup in-memory DB for testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_calculate_trend():
    engine = AnalysisEngine()

    # Test positive trend
    dates = pd.date_range("2023-01-01", periods=10)
    values = np.linspace(10, 20, 10)
    series = pd.Series(values, index=dates)

    result = engine.calculate_trend(series)
    assert result['slope'] is not None
    assert result['slope'] > 0
    assert result['p_value'] < 0.05

    # Test no trend
    values_flat = np.ones(10) * 10
    series_flat = pd.Series(values_flat, index=dates)
    result_flat = engine.calculate_trend(series_flat)
    assert result_flat['slope'] == 0

def test_bootstrap_ci():
    engine = AnalysisEngine()

    # Group 2 significantly higher than Group 1
    g1 = pd.Series(np.random.normal(10, 1, 100))
    g2 = pd.Series(np.random.normal(15, 1, 100))

    ci = engine.bootstrap_ci(g1, g2, n_bootstraps=100)
    assert ci['lower'] > 0
    assert ci['upper'] > 0
    assert ci['upper'] > ci['lower']

def test_data_manager_import_export(db_session, tmp_path):
    dm = DataManager(db=db_session)

    # Create a CSV
    csv_file = tmp_path / "metrics.csv"
    csv_content = "date,metric_name,value\n2023-01-01,Sleep,8.0\n2023-01-02,Sleep,7.5"
    csv_file.write_text(csv_content)

    # Import
    res = dm.import_from_csv(str(csv_file), 'metrics')
    assert res['success'] is True

    # Verify in DB
    entries = db_session.query(MetricEntry).all()
    assert len(entries) == 2
    assert entries[0].metric_name == "Sleep"

    # Export
    export_file = tmp_path / "export_metrics.csv"
    res_export = dm.export_to_csv(str(export_file), 'metrics')
    assert res_export['success'] is True
    assert export_file.exists()

    content = export_file.read_text()
    assert "Sleep" in content
    assert "8.0" in content

def test_report_generator(tmp_path):
    results = {
        "analysis": {
            "mean_difference": 2.0,
            "cohens_d": 1.5,
            "bootstrap_ci": {"lower": 1.0, "upper": 3.0}
        },
        "baseline_window": {
            "start": "2023-01-01", "end": "2023-01-10", "count": 10, "mean": 5.0, "std": 1.0,
            "trend": {"slope": 0.1, "p_value": 0.04}
        },
        "intervention_window": {
            "start": "2023-01-11", "end": "2023-01-20", "count": 10, "mean": 7.0, "std": 1.0,
            "trend": {"slope": -0.1, "p_value": 0.04}
        },
        "warnings": ["Small sample"]
    }

    report_file = tmp_path / "report.html"
    success = ReportGenerator.generate_html_report(results, str(report_file), "Test Int", "Test Metric")

    assert success is True
    assert report_file.exists()
    content = report_file.read_text()
    assert "Test Int" in content
    # Allow for flexible whitespace
    assert "Mean Difference" in content
    assert "2.00" in content
    assert "Bootstrap 95% CI" in content
