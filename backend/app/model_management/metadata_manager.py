"""
Model Metadata Manager
=======================
Reads and writes model metadata to Supabase Storage (``model_metadata.json``)
with a local disk fallback at ``backend/models/model_metadata.json``.
Captures the latest training snapshot: model versions, training date,
dataset sizes, and accuracy metrics.

Why maintain metadata?
    The metadata file serves as a quick "at-a-glance" summary of the current
    state of the ML system.  Without it, you'd have to:
    - Parse model filenames to find the latest version
    - Re-evaluate models to get accuracy numbers
    - Query the database to count dataset sizes

    The ``GET /api/v1/model/status`` endpoint reads directly from this file,
    making it an O(1) operation instead of a multi-second computation.

    In production ML systems, this is equivalent to a "model card" — a
    standardised summary of what the model is, when it was trained, and
    how well it performs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from . import MODELS_DIR

logger = logging.getLogger("model_management.metadata_manager")

# Local metadata file path (fallback)
METADATA_FILE = MODELS_DIR / "model_metadata.json"

# Supabase Storage path (inside the 'reports' bucket)
STORAGE_METADATA_PATH = "model_metadata.json"

# Default metadata (used when no metadata file exists yet)
DEFAULT_METADATA: Dict[str, Any] = {
    "recommendation_model_version": "v1.0",
    "forecast_model_version": "v1.0",
    "trained_on": "N/A",
    "products": 0,
    "customers": 0,
    "sales": 0,
    "inventory": 0,
    "accuracy": 0.0,
    "forecast_rmse": 0.0,
    "forecast_mae": 0.0,
}


def load_metadata() -> Dict[str, Any]:
    """
    Load current model metadata.
    Priority: Supabase Storage → local disk → defaults.

    Returns the default metadata structure if nothing is found,
    which is the case before the first training run.  This ensures the
    ``GET /api/v1/model/status`` endpoint always returns a valid response.
    """
    # 1. Try Supabase Storage first
    try:
        from app.storage import download_json
        remote_data = download_json(STORAGE_METADATA_PATH)
        if isinstance(remote_data, dict):
            logger.info("[metadata_manager] Loaded model metadata from Supabase Storage")
            return remote_data
    except Exception as exc:
        logger.warning(f"[metadata_manager] Could not load metadata from Supabase: {exc}")

    # 2. Fall back to local disk
    if not METADATA_FILE.exists():
        logger.info("No model_metadata.json found locally or remotely — returning defaults")
        return DEFAULT_METADATA.copy()

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded model metadata from local disk")
        # Auto-seed to Supabase Storage so future loads hit remote storage
        try:
            from app.storage import upload_json
            upload_json(STORAGE_METADATA_PATH, data)
        except Exception:
            pass
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read model metadata (returning defaults): {e}")
        return DEFAULT_METADATA.copy()


def save_metadata(metadata: Dict[str, Any]) -> None:
    """Persist metadata to both Supabase Storage (primary) and local disk (fallback)."""
    # 1. Upload to Supabase Storage
    try:
        from app.storage import upload_json
        upload_json(STORAGE_METADATA_PATH, metadata)
        logger.info("[metadata_manager] Model metadata synced to Supabase Storage")
    except Exception as exc:
        logger.warning(f"[metadata_manager] Could not upload metadata to Supabase: {exc}")

    # 2. Always write local disk copy
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Model metadata saved locally → {METADATA_FILE}")
    except IOError as e:
        logger.error(f"Failed to save model metadata locally: {e}")
        raise


def update_metadata(
    recommendation_version: str,
    forecast_version: str,
    dataset_sizes: Dict[str, int],
    recommendation_accuracy: float,
    forecast_rmse: float,
    forecast_mae: float,
) -> Dict[str, Any]:
    """
    Update model_metadata.json after a successful training run.

    This function is called automatically by the training service after
    models have been saved and evaluated.  It captures the complete
    snapshot of the training outcome.

    Parameters
    ----------
    recommendation_version : str
        New recommendation model version (e.g., "v1.1").
    forecast_version : str
        New forecast model version (e.g., "v1.1").
    dataset_sizes : dict
        Row counts: {"products": 500, "customers": 2300, "sales": 62000}
    recommendation_accuracy : float
        Hybrid recommendation system accuracy (Precision@K × 100).
    forecast_rmse : float
        Forecast model RMSE on the test set.
    forecast_mae : float
        Forecast model MAE on the test set.

    Returns
    -------
    dict
        The updated metadata dictionary.
    """
    metadata: Dict[str, Any] = {
        "recommendation_model_version": recommendation_version,
        "forecast_model_version": forecast_version,
        "trained_on": datetime.now().strftime("%Y-%m-%d"),
        "products": dataset_sizes.get("products", 0),
        "customers": dataset_sizes.get("customers", 0),
        "sales": dataset_sizes.get("sales", 0),
        "inventory": dataset_sizes.get("inventory", 0),
        "accuracy": round(recommendation_accuracy, 2),
        "forecast_rmse": round(forecast_rmse, 2),
        "forecast_mae": round(forecast_mae, 2),
    }

    save_metadata(metadata)
    logger.info(
        f"Metadata updated: Rec {recommendation_version}, "
        f"Forecast {forecast_version}, Accuracy {recommendation_accuracy:.2f}%"
    )
    return metadata


def get_current_versions() -> Dict[str, str]:
    """
    Quick accessor for current model version strings.
    Used by the versioning service to determine the next version number.
    """
    metadata = load_metadata()
    return {
        "recommendation": metadata.get("recommendation_model_version", "v1.0"),
        "forecast": metadata.get("forecast_model_version", "v1.0"),
    }
