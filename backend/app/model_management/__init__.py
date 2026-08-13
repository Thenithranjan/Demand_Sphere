"""
AI Model Management Package
============================
Enterprise-level MLOps module for the Retail Product Recommendation System.

This package provides:
    - Manual and automatic model retraining
    - Database-to-CSV dataset synchronisation
    - Feature engineering orchestration
    - Model versioning with no-overwrite policy
    - Training logs and metadata persistence
    - Live training progress tracking
    - Hot model reloading without server restart

Architecture:
    This module is ADDITIVE-ONLY — it does not modify any existing code.
    It delegates to the existing recommendation and forecasting pipelines
    for feature engineering and model training, wrapping them with
    enterprise concerns (versioning, logging, progress, security).

Why this module exists:
    In production ML systems, training a model once is never enough.
    New sales transactions, new products, and shifting customer behaviour
    require periodic retraining.  This module automates that lifecycle
    while maintaining full auditability (logs, versions, metadata).
"""

import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared path constants used across all submodules
# ---------------------------------------------------------------------------
# PROJECT_ROOT is the top-level Retail-Product-Recommendation directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Directory where trained model files (.pkl, .joblib) are stored
MODELS_DIR = PROJECT_ROOT / "backend" / "models"

# Directory where processed CSV datasets are stored
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist at import time
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Package-level logger
logger = logging.getLogger("model_management")
