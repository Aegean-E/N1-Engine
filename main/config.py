# main/config.py
import os

# Scientific constraints
MIN_BASELINE_DAYS = 7
MIN_INTERVENTION_DAYS = 7
MIN_DATA_POINTS = 3
MAX_SAFE_METRICS = 3  # Suggests multiple comparison correction if exceeded
 
# Database
DATABASE_URL = os.getenv("N1_DATABASE_URL", "sqlite:///./main.db")
