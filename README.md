# Personal Experiment Engine (PEE)

## 1. Project Overview

The **Personal Experiment Engine (PEE)** is a local-first Python platform designed for rigorous N=1 self-experimentation analysis. It empowers individuals to treat their life as a laboratory, applying scientific statistical methods to personal data to determine what truly works for them.

**What PEE is:**
- A structured tool for logging life interventions (e.g., "Started Magnesium", "Quit Caffeine") and tracking daily metrics (e.g., "Sleep Quality", "Energy Level").
- A statistical analysis engine that compares baseline periods against intervention periods to detect significant changes.
- A cross-platform desktop application built with Python and PyQt6.
- A privacy-focused tool: All data is stored locally on your machine in a SQLite database.

**What PEE is NOT:**
- **Not medical advice:** PEE is a software tool for data analysis. It does not replace professional medical advice. Consult a doctor for health decisions.
- **Not a causal proof engine:** PEE identifies correlations and statistically significant shifts. However, in single-subject experiments, unmeasured confounding variables (like stress, weather, or placebo effects) can influence results.

## 2. Scientific Philosophy

PEE is built on the principles of "N=1 structured inference":
*   **Epistemic Humility:** We acknowledge the limitations of self-experimentation. Results are indicators, not absolute truths.
*   **Conservative Interpretation:** PEE favors caution. It flags small sample sizes, multiple comparisons, and insufficient data to prevent overconfidence.
*   **Reproducibility:** Analysis is deterministic and repeatable.
*   **Separation of Concerns:** Data entry is distinct from analysis to minimize observer bias.

## 3. Installation Instructions

**Prerequisites:**
- Python 3.11 or higher.

**Step-by-Step Setup:**

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd pee
    ```

2.  **Create a virtual environment (Recommended):**
    *   **Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```cmd
        python -m venv venv
        venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs essential libraries like `pandas`, `numpy`, `scipy`, `statsmodels`, `sqlalchemy`, `PyQt6`, and `matplotlib`.*

4.  **Database:**
    PEE uses a local SQLite database (`pee.db`). This file is automatically created in the root directory when you first run the application.

## 4. Running the Application

To launch the Graphical User Interface (GUI):

```bash
python run_gui.py
```

## 5. Usage Guide

### A. Interventions Tab
This is where you manage your experiments.
-   **Add Intervention:** Click "Add Intervention". Enter a name (e.g., "Blue Light Blockers"), a Start Date, and optional Dosage/Notes.
-   **Edit Intervention:** Double-click a row or select it and click "Edit Selected".
-   **Close Intervention:** If you stop an intervention, select it and click "Close (End Now)". This sets the End Date to today.
-   **Active vs. Closed:** "Active" interventions have no end date and are ongoing.

### B. Metrics Tab
Log your daily quantitative data here.
-   **Log Metric:** Select a date, enter a metric name (or choose from existing ones), and a numeric value.
    -   *Example:* Metric Name: "Sleep Quality", Value: 8.5.
-   **Visualize:** Select a metric from the dropdown to see a time-series plot of your data.

### C. Events Tab
Log qualitative or significant one-off events that might impact your metrics (confounding variables).
-   **Log Event:** Enter Date, Time, Event Name (e.g., "Sick", "Travel", "High Stress"), Severity (1-5), and Notes.
-   *Use Case:* If your sleep quality drops, check the Events tab to see if you were traveling or sick during that period.

### D. Analysis Tab
This is the core of PEE. It statistically compares your data before and during an intervention.
1.  **Select Intervention:** Choose the experiment you want to analyze.
2.  **Select Metric:** Choose the outcome metric you want to test (e.g., "Sleep Quality").
3.  **Set Windows:**
    -   **Baseline Days:** How many days *before* the intervention started should be used as the control group? (Recommended: 14+ days).
    -   **Intervention Days:** How many days *after* the intervention started should be analyzed?
4.  **Run Analysis:** Click the button to generate the report.

**Understanding the Report:**
-   **Windows:** Shows the exact dates, count (N), mean, and standard deviation for both periods.
-   **Trends:** Displays the linear trend (slope) and its p-value. A significant trend *before* the intervention suggests your baseline wasn't stable.
-   **Mean Difference:** The raw change in the average (Intervention Mean - Baseline Mean).
-   **Cohen's d:** Effect size.
    -   0.2 = Small
    -   0.5 = Medium
    -   0.8 = Large
-   **Bootstrap 95% CI:** The Confidence Interval for the mean difference. If it doesn't cross zero (e.g., [0.5, 2.3]), the change is statistically significant at the 95% level.
-   **p-values:**
    -   **Welch's t-test:** Parametric test for difference in means (assumes unequal variance). p < 0.05 is significant.
    -   **Mann-Whitney U:** Non-parametric test (doesn't assume normal distribution). Useful for small samples or ordinal data (1-10 scales).

### E. Data Management Tab
Import and export your data for backup or external analysis.
-   **Import CSV:**
    -   **Metrics CSV Format:** `date` (YYYY-MM-DD), `metric_name`, `value`.
    -   **Interventions CSV Format:** `name`, `start_date` (YYYY-MM-DD), `end_date` (optional), `dosage`, `notes`.
    -   **Events CSV Format:** `timestamp` (YYYY-MM-DD HH:MM:SS), `event_name`, `severity`, `notes`.
-   **Export CSV:** Saves your database content to CSV files.

## 6. Statistical Methods & Rigor

PEE employs several statistical checks to ensure robust results:
1.  **Linear Regression (Trends):** Checks if the metric was already changing before the intervention (non-stationary baseline).
2.  **Bootstrap Resampling:** Calculates confidence intervals by simulating 1000 "parallel universes" from your data. This is often more robust than formula-based CIs for small, skewed datasets.
3.  **Scientific Warnings:**
    -   **Small Sample Size:** Flags analysis if N < 7 days.
    -   **Multiple Comparisons:** Warns if you test too many metrics at once (increasing the risk of false positives).
    -   **Zero Variance:** Flags if the data is constant (e.g., you logged "8" for 14 days straight).

## 7. Troubleshooting

*   **"Analysis Failed":** Ensure you have at least 3 days of data for both the baseline and intervention periods.
*   **"Database Locked":** This can happen if multiple instances of PEE are open. Close other instances.
*   **"Import Failed":** Check your CSV formatting. Dates must be YYYY-MM-DD.

## 8. Developer Guide

**Directory Structure:**
```
/pee
  /core            # Business logic and database
    analysis.py    # Statistical engine
    data_manager.py# Import/Export logic
    models.py      # SQLAlchemy models
  /gui             # PyQt6 Application
    analysis.py    # Analysis widget
    ...
tests/             # Unit tests
run_gui.py         # Entry point
```

**Running Tests:**
To verify the integrity of the application:
```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
python -m pytest tests/
```

**Contributing:**
1.  Fork the repository.
2.  Create a feature branch.
3.  Write tests for your changes.
4.  Submit a Pull Request.

## 9. License

[License Name/Type] - See LICENSE file for details.
