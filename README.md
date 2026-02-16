# Personal Experiment Engine (PEE)

## 1. Project Overview

The **Personal Experiment Engine (PEE)** is a local-first Python platform designed for rigorous N=1 self-experimentation analysis.

**What PEE is:**
- A structured tool for logging interventions and tracking metrics.
- An analysis engine for comparing baseline periods against intervention periods.
- A framework built on standard scientific Python libraries (Pandas, SciPy, NumPy).
- **NEW:** A cross-platform desktop GUI for easy interaction.

**What PEE is NOT:**
- **Not medical advice:** PEE is a software tool, not a doctor. Consult a professional for health decisions.
- **Not a causal proof engine:** PEE provides statistical insights, but correlation does not imply causation, especially in single-subject designs.

**Scientific Positioning:**
PEE facilitates "N=1 structured inference," allowing individuals to apply scientific rigor to their personal data, moving beyond intuition to data-driven insights.

## 2. Design Philosophy

*   **Epistemic Humility:** We acknowledge the limitations of single-subject experiments. Results are indicators, not absolute truths.
*   **Conservative Interpretation:** PEE favors caution. We flag small sample sizes, potential confounds, and multiple comparisons to prevent overconfidence.
*   **Reproducibility:** Analysis should be repeatable. By using code and versioned data, PEE ensures that results can be verified.
*   **Separation of Concerns:** Logging (data entry) is distinct from Inference (analysis), ensuring that the act of recording data does not bias the interpretation.

## 3. Architecture

The codebase is organized as follows:

```
/pee
  /core
    analysis.py       # Statistical logic and hypothesis testing
    database.py       # Database connection and session management
    models.py         # SQLAlchemy data models (Intervention, MetricEntry, EventEntry)
  /gui                # Desktop GUI (PyQt6)
    main_window.py
    interventions.py
    metrics.py
    events.py
    analysis.py
    utils.py
  /api                # API endpoints (Phase 4)
  /utils              # Utility functions
tests/                # Unit and integration tests
config.py             # Configuration and constants
run_gui.py            # Entry point for GUI
```

## 4. Installation Instructions

**Prerequisites:**
- Python 3.11+

**Setup:**

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd pee
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install PyQt6 matplotlib  # Required for GUI
    ```

4.  **Database:**
    PEE uses SQLite (`pee.db`). The database file will be created automatically in the root directory upon first run.

## 5. GUI Usage

To launch the graphical user interface:

```bash
python run_gui.py
```

### Features

1.  **Interventions:**
    - View, add, and manage interventions.
    - Fields: Name, Start Date, Dosage, Notes.
    - ![Interventions Screenshot Placeholder](https://via.placeholder.com/800x400?text=Interventions+Tab)

2.  **Metrics:**
    - Log daily metrics (e.g., Sleep Quality, Mood, Blood Pressure).
    - Visualize time-series data with interactive plots.
    - ![Metrics Screenshot Placeholder](https://via.placeholder.com/800x400?text=Metrics+Tab)

3.  **Events:**
    - Log significant events (e.g., Illness, Stress, Diet Cheat).
    - Severity rating (1-5) and notes.
    - ![Events Screenshot Placeholder](https://via.placeholder.com/800x400?text=Events+Tab)

4.  **Analysis:**
    - Select an intervention and a metric to analyze.
    - Define baseline and intervention windows (days).
    - View statistical results:
        - Mean Difference, Cohen's d.
        - **NEW:** Linear Trend (slope, p-value) for each period.
        - **NEW:** Bootstrap 95% Confidence Interval for the difference.
        - T-test and Mann-Whitney U test p-values.
    - **Scientific Rigor:** Warnings are displayed for small sample sizes, zero variance, etc.
    - Export reports to JSON or **NEW: HTML**.
    - ![Analysis Screenshot Placeholder](https://via.placeholder.com/800x400?text=Analysis+Tab)

5.  **Data Management (NEW):**
    - Import Metrics, Interventions, and Events from CSV files.
    - Export your data to CSV for backup or external analysis.
    - Located in the "Data Management" tab.

## 6. Minimal Programmatic Usage Example

This example demonstrates creating an intervention, logging metrics, and running a basic analysis via code.

```python
import pandas as pd
from datetime import date
from pee.core.database import SessionLocal, engine, Base
from pee.core.models import Intervention, MetricEntry
from pee.core.analysis import AnalysisEngine

# Initialize DB
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Create Intervention
intervention = Intervention(
    name="Blue Light Blocking Glasses",
    start_date=date(2023, 11, 1),
    notes="Wearing 2 hours before bed"
)
db.add(intervention)
db.commit()

# 2. Log Metrics (Mock Data)
# In practice, you would load this from a CSV or API
data = []
# Baseline (Oct 15 - Oct 31)
for d in pd.date_range("2023-10-15", "2023-10-31"):
    db.add(MetricEntry(date=d.date(), metric_name="Sleep Quality", value=7.0))
# Intervention (Nov 1 - Nov 14)
for d in pd.date_range("2023-11-01", "2023-11-14"):
    db.add(MetricEntry(date=d.date(), metric_name="Sleep Quality", value=8.0))
db.commit()

# 3. Run Analysis
engine = AnalysisEngine()
metrics_df = pd.read_sql(
    db.query(MetricEntry.date, MetricEntry.value, MetricEntry.metric_name)
    .filter(MetricEntry.metric_name == "Sleep Quality").statement,
    db.bind
)

result = engine.calculate_baseline_vs_intervention(
    metrics=metrics_df,
    start_date=pd.Timestamp("2023-11-01"),
    baseline_days=14,
    intervention_days=14
)

# 4. Interpret Output
print(result['analysis'])
# check 'warnings' key for any flags
```

## 7. Statistical Disclaimer

*   **Multiple Comparison Risk:** Testing many metrics simultaneously increases the chance of finding a "significant" result by random chance. PEE warns if you analyze >3 metrics at once.
*   **Small Sample Size:** PEE flags analyses with fewer than 7 days of data. Results from short periods are highly volatile and should be treated with extreme skepticism.
*   **Correlation ≠ Causation:** An observed change after an intervention does not prove the intervention caused the change. External factors (seasonality, lifestyle changes, placebo effect) may be responsible.
*   **Single-Subject Limitations:** Results apply *only* to you (N=1) and cannot be generalized to others.

## 8. Development Roadmap

*   **Phase 1 (Complete):** Core architecture, database models, basic statistical engine (t-test, Mann-Whitney U), standard deviation pooling.
*   **Phase 2:** Lag detection (time-series analysis), automated reporting, improved data ingestion.
*   **Phase 3:** Causal graphs, Bayesian updating, counterfactual reasoning support.
*   **Phase 4:** API layer, web interface, mobile companion app.
