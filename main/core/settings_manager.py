import json
import os
import logging

# Default values, can be imported from config.py to keep them central
from main.config import (
    MIN_BASELINE_DAYS,
    MIN_INTERVENTION_DAYS,
    MIN_DATA_POINTS,
    MAX_SAFE_METRICS
)

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.defaults = {
            "min_baseline_days": MIN_BASELINE_DAYS,
            "min_intervention_days": MIN_INTERVENTION_DAYS,
            "min_data_points": MIN_DATA_POINTS,
            "max_safe_metrics": MAX_SAFE_METRICS,
        }
        self.settings = self.defaults.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    user_settings = json.load(f)
                # Merge, ensuring all default keys are present
                self.settings.update(user_settings)
                # Ensure no stale keys from an old settings file are kept
                self.settings = {k: self.settings[k] for k in self.defaults if k in self.settings}
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Could not load settings file '{self.settings_file}': {e}. Using defaults.")
                self.settings = self.defaults.copy()
        else:
            # If no file, just use defaults
            self.settings = self.defaults.copy()
        return self.settings

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Settings saved to '{self.settings_file}'.")
        except IOError as e:
            logger.error(f"Could not save settings to '{self.settings_file}': {e}.")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        if key in self.defaults:
            self.settings[key] = value
        else:
            logger.warning(f"Attempted to set an unknown setting: '{key}'")

# Global instance
settings_manager = SettingsManager()