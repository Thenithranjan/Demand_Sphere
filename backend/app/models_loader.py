"""
Machine Learning Model Loader
==============================
Handles loading and in-memory caching of the recommendation and demand forecasting models.
Ensures that expensive file read operations occur only once during application startup.
"""

import os
import pickle
import io
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import joblib

logger = logging.getLogger("models_loader")

# Base directory for models
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# Singleton cache variables
_recommendation_model_cache: Optional[Dict[str, Any]] = None
_forecast_model_cache: Optional[Dict[str, Any]] = None


def load_recommendation_model() -> Dict[str, Any]:
    """
    Loads the recommendation model artifacts from recommendation_model.pkl.
    Uses in-memory caching (Singleton pattern) to avoid reloading.

    Returns:
        Dict[str, Any]: Dictionary containing Collaborative and Content-Based artifacts.
    """
    global _recommendation_model_cache
    if _recommendation_model_cache is not None:
        return _recommendation_model_cache

    model_path = MODELS_DIR / "recommendation_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Recommendation model file not found at: {model_path}")

    logger.info(f"Loading recommendation model from {model_path}...")
    with open(model_path, "rb") as f:
        _recommendation_model_cache = pickle.load(f)

    logger.info("Recommendation model successfully loaded into memory cache.")
    return _recommendation_model_cache


def load_forecast_model() -> Dict[str, Any]:
    """
    Loads the forecasting model artifacts from forecast_model.pkl.
    Uses in-memory caching (Singleton pattern) to avoid reloading.

    Returns:
        Dict[str, Any]: Dictionary containing XGBoost models and category encoders.
    """
    global _forecast_model_cache
    if _forecast_model_cache is not None:
        return _forecast_model_cache

    model_path = MODELS_DIR / "forecast_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Forecasting model file not found at: {model_path}")

    logger.info(f"Loading forecasting model from {model_path}...")
    with open(model_path, "rb") as f:
        artifacts = pickle.load(f)

    # To load XGBoost joblib objects safely across all OS environments,
    # we write the bytes back to temporary files and load them using joblib.
    loaded_artifacts = {}
    temp_dir = tempfile.gettempdir()

    # Load Quantity XGBoost Model
    qty_temp_path = os.path.join(temp_dir, "qty_model.joblib")
    with open(qty_temp_path, "wb") as f:
        f.write(artifacts["forecast_quantity_xgb_bytes"])
    loaded_artifacts["forecast_quantity_xgb"] = joblib.load(qty_temp_path)
    try:
        os.remove(qty_temp_path)
    except Exception:
        pass

    # Load Revenue XGBoost Model
    rev_temp_path = os.path.join(temp_dir, "rev_model.joblib")
    with open(rev_temp_path, "wb") as f:
        f.write(artifacts["forecast_revenue_xgb_bytes"])
    loaded_artifacts["forecast_revenue_xgb"] = joblib.load(rev_temp_path)
    try:
        os.remove(rev_temp_path)
    except Exception:
        pass

    # Load Encoders (already pickled/joblib bytes)
    enc_temp_path = os.path.join(temp_dir, "encoders.joblib")
    with open(enc_temp_path, "wb") as f:
        f.write(artifacts["forecasting_encoders_bytes"])
    loaded_artifacts["forecasting_encoders"] = joblib.load(enc_temp_path)
    try:
        os.remove(enc_temp_path)
    except Exception:
        pass

    _forecast_model_cache = loaded_artifacts
    logger.info("Forecasting model successfully loaded into memory cache.")
    return _forecast_model_cache
