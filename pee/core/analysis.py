import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Optional
from datetime import timedelta

class AnalysisEngine:
    """
    Engine for analyzing experiment data.
    """
    def __init__(self):
        pass

    def calculate_baseline_vs_intervention(
        self,
        metrics: pd.DataFrame,
        start_date: pd.Timestamp,
        baseline_days: int = 14,
        intervention_days: int = 14
    ) -> Dict[str, Any]:
        """
        Analyzes metric data comparing a baseline period to an intervention period.

        Args:
            metrics: DataFrame containing 'date' and 'value' columns.
            start_date: The start date of the intervention.
            baseline_days: Number of days before start_date to include in baseline.
            intervention_days: Number of days after start_date to include in intervention.

        Returns:
            Dictionary containing analysis results.
        """
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(metrics['date']):
            metrics = metrics.copy()
            metrics['date'] = pd.to_datetime(metrics['date'])

        # Define windows
        baseline_start = start_date - timedelta(days=baseline_days)
        intervention_end = start_date + timedelta(days=intervention_days)

        # Filter data
        baseline_df = metrics[
            (metrics['date'] >= baseline_start) &
            (metrics['date'] < start_date)
        ].dropna(subset=['value'])

        intervention_df = metrics[
            (metrics['date'] >= start_date) &
            (metrics['date'] < intervention_end)
        ].dropna(subset=['value'])

        baseline_data = baseline_df['value']
        intervention_data = intervention_df['value']

        # Check for insufficient data points
        if len(baseline_data) < 3 or len(intervention_data) < 3:
            return {
                "error": "Insufficient data points (minimum 3 required)",
                "baseline_count": len(baseline_data),
                "intervention_count": len(intervention_data)
            }

        # Check for insufficient sample size (duration < 7 days)
        warnings = []

        if not baseline_df.empty:
            baseline_span = (baseline_df['date'].max() - baseline_df['date'].min()).days + 1
            if baseline_span < 7:
                warnings.append(f"Insufficient baseline duration: {baseline_span} days (recommended >= 7)")

        if not intervention_df.empty:
            intervention_span = (intervention_df['date'].max() - intervention_df['date'].min()).days + 1
            if intervention_span < 7:
                warnings.append(f"Insufficient intervention duration: {intervention_span} days (recommended >= 7)")

        # Calculate means and std
        mean_baseline = baseline_data.mean()
        std_baseline = baseline_data.std(ddof=1)
        mean_intervention = intervention_data.mean()
        std_intervention = intervention_data.std(ddof=1)

        mean_diff = mean_intervention - mean_baseline

        # Cohen's d
        # Pooled standard deviation
        n1 = len(baseline_data)
        n2 = len(intervention_data)

        if n1 + n2 - 2 > 0:
            pooled_std = np.sqrt(
                ((n1 - 1) * std_baseline**2 + (n2 - 1) * std_intervention**2) / (n1 + n2 - 2)
            )
        else:
            pooled_std = 0

        cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0.0

        # Statistical Tests
        # Two-sided t-test
        # Welch's t-test is generally safer (equal_var=False)
        t_stat, p_value_t = stats.ttest_ind(
            intervention_data, baseline_data, equal_var=False
        )

        # Mann-Whitney U test
        u_stat, p_value_u = stats.mannwhitneyu(
            intervention_data, baseline_data, alternative='two-sided'
        )

        return {
            "baseline_window": {
                "start": baseline_start.strftime("%Y-%m-%d"),
                "end": (start_date - timedelta(days=1)).strftime("%Y-%m-%d"),
                "count": int(n1),
                "mean": float(mean_baseline),
                "std": float(std_baseline) if not np.isnan(std_baseline) else 0.0
            },
            "intervention_window": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": (intervention_end - timedelta(days=1)).strftime("%Y-%m-%d"),
                "count": int(n2),
                "mean": float(mean_intervention),
                "std": float(std_intervention) if not np.isnan(std_intervention) else 0.0
            },
            "analysis": {
                "mean_difference": float(mean_diff),
                "cohens_d": float(cohens_d),
                "t_test": {
                    "statistic": float(t_stat),
                    "p_value": float(p_value_t)
                },
                "mann_whitney_u": {
                    "statistic": float(u_stat),
                    "p_value": float(p_value_u)
                }
            },
            "warnings": warnings
        }
