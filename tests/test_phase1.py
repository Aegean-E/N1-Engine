import sys
import os
import pandas as pd
from datetime import date, datetime, timedelta
import numpy as np
import json

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

if __name__ == "__main__":
    try:
        test_database_setup()
        test_analysis_engine()
        test_insufficient_duration_warning()
        print("\nAll Phase 1 tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
