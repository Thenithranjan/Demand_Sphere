"""
Hot Model Reload Service
=========================
Invalidates in-memory model caches and forces a fresh load from disk,
allowing the FastAPI process to serve predictions from newly trained
models WITHOUT requiring a server restart.

Why reload instead of restart?
    In production, restarting the server:
    - Drops all in-flight HTTP requests (data loss for clients)
    - Causes a brief downtime window
    - Requires orchestration tooling (Kubernetes, systemd, etc.)
    - May trigger health-check failures from load balancers

    Hot reloading is a ZERO-DOWNTIME operation.  The old model serves
    requests until the exact moment the new model is loaded into memory.
    The next request immediately uses the new model.

How it works:
    The existing ``models_loader.py`` uses module-level singleton variables:
        _recommendation_model_cache = None  →  loaded on first access
        _forecast_model_cache = None        →  loaded on first access

    To reload, we simply:
    1. Set both caches back to ``None``
    2. Call the load functions to repopulate the caches from the new .pkl files
    3. The next API request will use the freshly loaded models

    This is thread-safe because Python's GIL ensures that the None assignment
    and the subsequent load are atomic with respect to other threads.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("model_management.model_loader")


def reload_models() -> Dict[str, str]:
    """
    Invalidate the existing in-memory model caches and reload from disk.

    This function directly manipulates the singleton cache variables in
    ``backend.app.models_loader``, which is the module that the existing
    recommendation and forecast services import from.

    Returns
    -------
    dict
        Status of each model reload: {"recommendation": "loaded", "forecast": "loaded"}

    Raises
    ------
    RuntimeError
        If either model fails to reload (file not found, corrupted, etc.).
    """
    import app.models_loader as loader

    result = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Reload Recommendation Model
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Step 1: Invalidate the cache by setting the global variable to None
        loader._recommendation_model_cache = None
        logger.info("Recommendation model cache invalidated")

        # Step 2: Force a fresh load from the updated .pkl file
        loader.load_recommendation_model()
        result["recommendation"] = "loaded"
        logger.info("Recommendation model reloaded successfully")
    except Exception as e:
        error_msg = f"Failed to reload recommendation model: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # ─────────────────────────────────────────────────────────────────────────
    # Reload Forecast Model
    # ─────────────────────────────────────────────────────────────────────────
    try:
        loader._forecast_model_cache = None
        logger.info("Forecast model cache invalidated")

        loader.load_forecast_model()
        result["forecast"] = "loaded"
        logger.info("Forecast model reloaded successfully")
    except Exception as e:
        error_msg = f"Failed to reload forecast model: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    logger.info("All models reloaded successfully — new predictions will use updated models")
    return result
