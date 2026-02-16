import sys
import os
import pandas as pd
from datetime import date, datetime, timedelta
import numpy as np
import json
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pee.core.database import Base, engine, SessionLocal
from pee.core.models import Intervention, Intervention as InterventionModel # Just in case
from pee.core.analysis import AnalysisEngine

def test_database_setup():
    print("Testing Database Setup...")
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Create sample intervention
    # Check if it exists first to avoid duplicates if re-running
    existing = db.query(InterventionModel).filter_by(name="Magnesium Supplement").first()
    if not existing:
        intervention = InterventionModel(
            name="Magnesium Supplement",
            start_date=date(2023, 10, 1),
            dosage="400mg",
            notes="Taking before bed"
        )
        db.add(intervention)
        db.commit()

    saved_intervention = db.query(InterventionModel).filter_by(name="Magnesium Supplement").first()
    assert saved_intervention is not None
    assert saved_intervention.dosage == "400mg"

    db.close()
    print("Database setup test passed.")

def test_analysis_engine():
    print("Testing Analysis Engine...")
    analysis_engine = AnalysisEngine()

    start_date = pd.Timestamp("2023-10-01")

    # Generate 14 days baseline
    baseline_dates = [start_date - timedelta(days=x) for x in range(14, 0, -1)]
    # Mean approx 50
    baseline_values = np.array([48, 49, 50, 51, 52] * 3)[:14]

    # Generate 14 days intervention
    intervention_dates = [start_date + timedelta(days=x) for x in range(14)]
    # Mean approx 55
    intervention_values = np.array([53, 54, 55, 56, 57] * 3)[:14]

    data = pd.DataFrame({
        "date": baseline_dates + intervention_dates,
        "value": np.concatenate([baseline_values, intervention_values])
    })

    result = analysis_engine.calculate_baseline_vs_intervention(
        metrics=data,
        start_date=start_date,
        baseline_days=14,
        intervention_days=14
    )

    print("\nAnalysis Result:")
    print(json.dumps(result, indent=2, default=str))

    analysis = result["analysis"]

    # Expected values
    # Mean diff should be approx 5
    assert 4.5 < analysis["mean_difference"] < 5.5

    # Cohen's d
    # Std is approx 1.4. Diff is 5. d ~ 3.5
    assert analysis["cohens_d"] > 2.0

    # Significance
    assert analysis["t_test"]["p_value"] < 0.001

    print("Analysis engine test passed.")

def test_insufficient_duration_warning():
    print("Testing Insufficient Duration Warning...")
    analysis_engine = AnalysisEngine()

    start_date = pd.Timestamp("2023-10-01")

    # Generate 5 days baseline (< 7)
    baseline_dates = [start_date - timedelta(days=x) for x in range(5, 0, -1)]
    baseline_values = np.array([50] * 5)

    # Generate 14 days intervention
    intervention_dates = [start_date + timedelta(days=x) for x in range(14)]
    intervention_values = np.array([55] * 14)

    data = pd.DataFrame({
        "date": baseline_dates + intervention_dates,
        "value": np.concatenate([baseline_values, intervention_values])
    })

    result = analysis_engine.calculate_baseline_vs_intervention(
        metrics=data,
        start_date=start_date,
        baseline_days=14,
        intervention_days=14
    )

    warnings = result.get("warnings", [])
    print(f"Warnings: {warnings}")
    assert any("Insufficient baseline duration" in w for w in warnings)
    print("Insufficient duration warning test passed.")

def test_mixed_metrics_error():
    print("Testing Mixed Metrics Error...")
    analysis_engine = AnalysisEngine()
    start_date = pd.Timestamp("2023-10-01")

    data = pd.DataFrame({
        "date": [start_date - timedelta(days=1), start_date],
        "value": [10, 20],
        "metric_name": ["Metric A", "Metric B"]
    })

    try:
        analysis_engine.calculate_baseline_vs_intervention(
            metrics=data,
            start_date=start_date,
            baseline_days=1,
            intervention_days=1
        )
        assert False, "Should have raised ValueError for mixed metrics"
    except ValueError as e:
        print(f"Caught expected error: {e}")
        assert "AnalysisEngine expects a single metric" in str(e)
    print("Mixed metrics error test passed.")

def test_zero_variance():
    print("Testing Zero Variance...")
    analysis_engine = AnalysisEngine()
    start_date = pd.Timestamp("2023-10-01")

    # Constant baseline and intervention
    baseline_dates = [start_date - timedelta(days=x) for x in range(7, 0, -1)]
    baseline_values = np.array([50] * 7)

    intervention_dates = [start_date + timedelta(days=x) for x in range(7)]
    intervention_values = np.array([50] * 7)

    data = pd.DataFrame({
        "date": baseline_dates + intervention_dates,
        "value": np.concatenate([baseline_values, intervention_values])
    })

    result = analysis_engine.calculate_baseline_vs_intervention(
        metrics=data,
        start_date=start_date,
        baseline_days=7,
        intervention_days=7
    )

    print(f"Zero variance result: {json.dumps(result['analysis'], indent=2)}")
    # t-test should be 0 stat, 1.0 p-value handled in code
    assert result['analysis']['t_test']['p_value'] == 1.0
    assert result['analysis']['mean_difference'] == 0.0

    warnings = result.get("warnings", [])
    assert any("Zero variance" in w for w in warnings)
    print("Zero variance test passed.")

def test_multiple_comparison_warning():
    print("Testing Multiple Comparison Warning...")
    analysis_engine = AnalysisEngine()
    start_date = pd.Timestamp("2023-10-01")

    # Create 4 mock dataframes
    metrics_map = {}
    for i in range(4):
        metrics_map[f"Metric_{i}"] = pd.DataFrame({
             "date": [start_date - timedelta(days=1), start_date],
             "value": [10, 12]
        })

    result = analysis_engine.analyze_multiple_metrics(
        metrics_map=metrics_map,
        start_date=start_date,
        baseline_days=1,
        intervention_days=1
    )

    warnings = result.get("global_warnings", [])
    print(f"Global Warnings: {warnings}")
    assert any("Multiple Comparison Risk" in w for w in warnings)
    print("Multiple comparison warning test passed.")

def test_window_duration_exactness():
    print("Testing Window Duration Exactness...")
    analysis_engine = AnalysisEngine()
    start_date = pd.Timestamp("2023-01-01")

    # Generate daily data for a long period
    dates = pd.date_range("2022-12-01", "2023-01-31")
    values = np.ones(len(dates))
    data = pd.DataFrame({"date": dates, "value": values})

    # Test 7 days baseline, 7 days intervention
    result = analysis_engine.calculate_baseline_vs_intervention(
        metrics=data,
        start_date=start_date,
        baseline_days=7,
        intervention_days=7
    )

    # Baseline: Dec 25 - Dec 31 (7 days)
    # Intervention: Jan 1 - Jan 7 (7 days)

    print(f"Baseline Count: {result['baseline_window']['count']}")
    print(f"Intervention Count: {result['intervention_window']['count']}")

    assert result['baseline_window']['count'] == 7, f"Baseline count {result['baseline_window']['count']} != 7"
    assert result['intervention_window']['count'] == 7, f"Intervention count {result['intervention_window']['count']} != 7"

    # Test 1 day
    result = analysis_engine.calculate_baseline_vs_intervention(
        metrics=data,
        start_date=start_date,
        baseline_days=1,
        intervention_days=1
    )
    # Baseline: Dec 31 (1 day)
    # Intervention: Jan 1 (1 day)

    # Note: MIN_DATA_POINTS check might fail if count < 3.
    # The current implementation returns error if count < 3.
    # So checking count in result is tricky if it returns error dict.
    if "error" in result:
        print(f"Skipping count assertion for 1 day due to MIN_DATA_POINTS check: {result['error']}")
        # The 'baseline_count' key exists in error dict
        assert result['baseline_count'] == 1
        assert result['intervention_count'] == 1
    else:
        assert result['baseline_window']['count'] == 1
        assert result['intervention_window']['count'] == 1

    print("Window duration exactness test passed.")

if __name__ == "__main__":
    try:
        test_database_setup()
        test_analysis_engine()
        test_insufficient_duration_warning()
        test_mixed_metrics_error()
        test_zero_variance()
        test_multiple_comparison_warning()
        test_window_duration_exactness()
        print("\nAll Phase 1 tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
