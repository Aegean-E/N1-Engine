import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Optional, Union
from datetime import timedelta
import logging

from pee.config import (
    MIN_BASELINE_DAYS,
    MIN_INTERVENTION_DAYS,
    MIN_DATA_POINTS,
    MAX_SAFE_METRICS
)

# Setup logging
logger = logging.getLogger(__name__)

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
        logger.info(f"Starting analysis for intervention starting {start_date}")

        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(metrics['date']):
            metrics = metrics.copy()
            metrics['date'] = pd.to_datetime(metrics['date'])

        # Input Validation: Check for mixed metrics
        if 'metric_name' in metrics.columns:
            unique_metrics = metrics['metric_name'].unique()
            if len(unique_metrics) > 1:
                error_msg = f"AnalysisEngine expects a single metric. Found {len(unique_metrics)}: {unique_metrics}"
                logger.error(error_msg)
                raise ValueError(error_msg)

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
        if len(baseline_data) < MIN_DATA_POINTS or len(intervention_data) < MIN_DATA_POINTS:
            logger.warning("Insufficient data points for analysis.")
            return {
                "error": f"Insufficient data points (minimum {MIN_DATA_POINTS} required)",
                "baseline_count": len(baseline_data),
                "intervention_count": len(intervention_data)
            }

        # Warnings
        warnings = []

        # Check for insufficient sample size
        if not baseline_df.empty:
            baseline_span = (baseline_df['date'].max() - baseline_df['date'].min()).days + 1
            if baseline_span < MIN_BASELINE_DAYS:
                msg = f"Insufficient baseline duration: {baseline_span} days (recommended >= {MIN_BASELINE_DAYS})"
                warnings.append(msg)
                logger.warning(msg)

        if not intervention_df.empty:
            intervention_span = (intervention_df['date'].max() - intervention_df['date'].min()).days + 1
            if intervention_span < MIN_INTERVENTION_DAYS:
                msg = f"Insufficient intervention duration: {intervention_span} days (recommended >= {MIN_INTERVENTION_DAYS})"
                warnings.append(msg)
                logger.warning(msg)

        if intervention_days < baseline_days:
            msg = f"Intervention duration ({intervention_days} days) is shorter than baseline ({baseline_days} days). Power may be reduced."
            warnings.append(msg)
            logger.warning(msg)

        # Calculate means and std
        mean_baseline = baseline_data.mean()
        std_baseline = baseline_data.std(ddof=1)
        mean_intervention = intervention_data.mean()
        std_intervention = intervention_data.std(ddof=1)

        mean_diff = mean_intervention - mean_baseline

        # Zero variance check
        baseline_variance = 0 if np.isnan(std_baseline) else std_baseline
        intervention_variance = 0 if np.isnan(std_intervention) else std_intervention

        if baseline_variance == 0 and intervention_variance == 0:
             warnings.append("Zero variance in both baseline and intervention data.")
             logger.warning("Zero variance detected.")

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
        t_stat, p_value_t = None, None
        u_stat, p_value_u = None, None

        try:
            # Welch's t-test
            if baseline_variance == 0 and intervention_variance == 0:
                if mean_diff == 0:
                    t_stat, p_value_t = 0.0, 1.0
                else:
                    t_stat, p_value_t = np.nan, np.nan # Undefined
            else:
                 t_stat, p_value_t = stats.ttest_ind(
                    intervention_data, baseline_data, equal_var=False
                )
        except Exception as e:
            logger.error(f"T-test failed: {e}")
            warnings.append(f"T-test failed: {str(e)}")
            t_stat, p_value_t = np.nan, np.nan

        try:
            # Mann-Whitney U test
             u_stat, p_value_u = stats.mannwhitneyu(
                intervention_data, baseline_data, alternative='two-sided'
            )
        except Exception as e:
            logger.error(f"Mann-Whitney U test failed: {e}")
            warnings.append(f"Mann-Whitney U test failed: {str(e)}")
            u_stat, p_value_u = np.nan, np.nan

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
                    "statistic": float(t_stat) if t_stat is not None and not np.isnan(t_stat) else None,
                    "p_value": float(p_value_t) if p_value_t is not None and not np.isnan(p_value_t) else None
                },
                "mann_whitney_u": {
                    "statistic": float(u_stat) if u_stat is not None and not np.isnan(u_stat) else None,
                    "p_value": float(p_value_u) if p_value_u is not None and not np.isnan(p_value_u) else None
                }
            },
            "warnings": warnings
        }

    def analyze_multiple_metrics(
        self,
        metrics_map: Dict[str, pd.DataFrame],
        start_date: pd.Timestamp,
        baseline_days: int = 14,
        intervention_days: int = 14
    ) -> Dict[str, Any]:
        """
        Analyzes multiple metrics and provides a warning if too many comparisons are made.
        """
        results = {}
        warnings = []

        if len(metrics_map) > MAX_SAFE_METRICS:
            msg = f"Multiple Comparison Risk: You are testing {len(metrics_map)} metrics simultaneously. This increases false discovery rate."
            warnings.append(msg)
            logger.warning(msg)

        for metric_name, df in metrics_map.items():
            try:
                # Ensure df filters for the specific metric if mixed (safeguard)
                if 'metric_name' in df.columns:
                     df_metric = df[df['metric_name'] == metric_name]
                else:
                     df_metric = df

                results[metric_name] = self.calculate_baseline_vs_intervention(
                    df_metric, start_date, baseline_days, intervention_days
                )
            except Exception as e:
                logger.error(f"Analysis failed for {metric_name}: {e}")
                results[metric_name] = {"error": str(e)}

        return {
            "results": results,
            "global_warnings": warnings
        }
