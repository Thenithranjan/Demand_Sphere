"""
Training Settings Manager
=========================
Loads and saves automated retraining configuration in ``backend/models/training_settings.json``.
Ensures settings are persisted and shared between the background scheduler and APIs.
"""

import json
import logging
from typing import Dict, Any
from . import MODELS_DIR

logger = logging.getLogger("model_management.settings_manager")

SETTINGS_FILE = MODELS_DIR / "training_settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "sales_threshold": 1000,
    "customer_threshold": 500,
    "product_threshold": 50,
    "training_interval_months": 1,
    "check_interval_hours": 24,
    "min_precision": 0.0,
    "max_rmse": 100.0,
    "approval_mode": "automatic",
}

def load_settings() -> Dict[str, Any]:
    """Load settings from training_settings.json, falling back to defaults."""
    if not SETTINGS_FILE.exists():
        logger.info("No training_settings.json found — creating with defaults")
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Ensure all default keys exist
        updated = False
        for k, v in DEFAULT_SETTINGS.items():
            if k not in data:
                data[k] = v
                updated = True
        
        if updated:
            save_settings(data)
            
        return data
    except Exception as e:
        logger.warning(f"Could not read training settings (returning defaults): {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to training_settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Training settings persisted to disk → {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save training settings: {e}")
        raise
