"""
==============================================================================
Demand Forecasting Module Initialization: __init__.py
==============================================================================
Purpose:
    Exposes paths, shared constants, and logging configuration for the
    demand forecasting machine learning pipeline.
==============================================================================
"""

import logging
from pathlib import Path

# Paths
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"
REPORTS_DIR = PROJECT_ROOT / "reports" / "forecast"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("forecasting")
