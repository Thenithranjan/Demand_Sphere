"""
Model Versioning Service
=========================
Handles saving new model artifacts under versioned filenames while
ensuring old versions are never deleted.

Versioning scheme:
    v1.0 → v1.1 → v1.2 → ... → v1.9 → v2.0 → v2.1 → ...

Why version models?
    In production ML, you MUST be able to:
    1. **Roll back** to a previous model if the new one performs worse.
    2. **Audit** which model version was serving predictions at any point in time.
    3. **Compare** accuracy across versions to track improvement trends.

    Overwriting models destroys this capability.  By keeping every version,
    the system maintains a full history — similar to Git commits for code.

Naming convention:
    recommendation_model_v1.0.pkl   ← first version
    recommendation_model_v1.1.pkl   ← after first retraining
    recommendation_model.pkl        ← always the LATEST (symlink/copy)

    The "unversioned" file (recommendation_model.pkl) is always a copy of
    the latest version.  This ensures backward compatibility with the
    existing models_loader.py which expects files at fixed paths.
"""

import json
import logging
import pickle
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from . import MODELS_DIR
from .metadata_manager import get_current_versions, load_metadata

logger = logging.getLogger("model_management.model_version")


def _bump_version(current_version: str) -> str:
    """
    Increment a version string by one minor version.
    "v1.0" → "v1.1", "v1.9" → "v2.0"
    """
    version_str = current_version.lstrip("v")
    try:
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        logger.warning(f"Could not parse version '{current_version}', defaulting to v1.1")
        return "v1.1"

    minor += 1
    if minor > 9:
        major += 1
        minor = 0

    return f"v{major}.{minor}"


def save_versioned_models(
    recommendation_artifacts: Dict[str, Any],
    forecast_artifacts: Dict[str, Any],
    activate: bool = True,
    recommendation_metrics: Optional[Dict[str, Any]] = None,
    forecast_metrics: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Save newly trained model artifacts under versioned directories.
    Structure:
        models/recommendation/{version}/model.pkl, metadata.json, metrics.json
        models/forecast/{version}/model.pkl, metadata.json, metrics.json
    """
    # Get current versions and compute next versions
    current = get_current_versions()
    new_rec_version = _bump_version(current["recommendation"])
    new_forecast_version = _bump_version(current["forecast"])

    # ─────────────────────────────────────────────────────────────────────────
    # Save Recommendation Model (versioned folder)
    # ─────────────────────────────────────────────────────────────────────────
    rec_dir = MODELS_DIR / "recommendation" / new_rec_version
    rec_dir.mkdir(parents=True, exist_ok=True)
    rec_pkl_path = rec_dir / "model.pkl"
    rec_current_path = MODELS_DIR / "recommendation_model.pkl"

    # Write pkl
    with open(rec_pkl_path, "wb") as f:
        pickle.dump(recommendation_artifacts, f)
    logger.info(f"Saved recommendation model → {rec_pkl_path}")

    # Write metrics.json & metadata.json inside the version directory
    rec_met = recommendation_metrics or {}
    with open(rec_dir / "metrics.json", "w") as f:
        json.dump(rec_met, f, indent=2)
        
    # Write metadata.json
    rec_meta_summary = {
        "model_type": "recommendation",
        "version": new_rec_version,
        "trained_on": Path(MODELS_DIR / "model_metadata.json").stat().st_mtime if Path(MODELS_DIR / "model_metadata.json").exists() else None
    }
    with open(rec_dir / "metadata.json", "w") as f:
        json.dump(rec_meta_summary, f, indent=2)

    # Legacy flat file copy for backward compatibility
    rec_flat_path = MODELS_DIR / f"recommendation_model_{new_rec_version}.pkl"
    try:
        shutil.copy2(rec_pkl_path, rec_flat_path)
    except Exception as e:
        logger.warning(f"Could not copy flat model fallback: {e}")

    if activate:
        shutil.copy2(rec_pkl_path, rec_current_path)
        logger.info(f"Copied recommendation model → {rec_current_path} (current)")
    else:
        logger.info(f"Activation skipped — old recommendation model remains active.")

    # ─────────────────────────────────────────────────────────────────────────
    # Save Forecast Model (versioned folder)
    # ─────────────────────────────────────────────────────────────────────────
    forecast_dir = MODELS_DIR / "forecast" / new_forecast_version
    forecast_dir.mkdir(parents=True, exist_ok=True)
    forecast_pkl_path = forecast_dir / "model.pkl"
    forecast_current_path = MODELS_DIR / "forecast_model.pkl"

    with open(forecast_pkl_path, "wb") as f:
        pickle.dump(forecast_artifacts, f)
    logger.info(f"Saved forecast model → {forecast_pkl_path}")

    # Write metrics.json & metadata.json
    fc_met = forecast_metrics or {}
    with open(forecast_dir / "metrics.json", "w") as f:
        json.dump(fc_met, f, indent=2)
        
    forecast_meta_summary = {
        "model_type": "forecast",
        "version": new_forecast_version,
        "trained_on": Path(MODELS_DIR / "model_metadata.json").stat().st_mtime if Path(MODELS_DIR / "model_metadata.json").exists() else None
    }
    with open(forecast_dir / "metadata.json", "w") as f:
        json.dump(forecast_meta_summary, f, indent=2)

    # Legacy flat file copy
    forecast_flat_path = MODELS_DIR / f"forecast_model_{new_forecast_version}.pkl"
    try:
        shutil.copy2(forecast_pkl_path, forecast_flat_path)
    except Exception as e:
        logger.warning(f"Could not copy flat model fallback: {e}")

    if activate:
        shutil.copy2(forecast_pkl_path, forecast_current_path)
        logger.info(f"Copied forecast model → {forecast_current_path} (current)")
    else:
        logger.info(f"Activation skipped — old forecast model remains active.")

    return new_rec_version, new_forecast_version


def list_model_versions() -> Dict[str, list]:
    """
    List all versioned models. Scan both versioned subdirectories and flat files.
    """
    rec_versions = set()
    forecast_versions = set()

    # Scan directories
    rec_path = MODELS_DIR / "recommendation"
    if rec_path.exists():
        for item in rec_path.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                rec_versions.add(item.name)

    forecast_path = MODELS_DIR / "forecast"
    if forecast_path.exists():
        for item in forecast_path.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                forecast_versions.add(item.name)

    # Scan flat legacy files
    for file in MODELS_DIR.glob("recommendation_model_v*.pkl"):
        version = file.stem.replace("recommendation_model_", "")
        rec_versions.add(version)

    for file in MODELS_DIR.glob("forecast_model_v*.pkl"):
        version = file.stem.replace("forecast_model_", "")
        forecast_versions.add(version)

    # Simple sorting function: e.g. "v1.1" -> (1, 1)
    def parse_version_tuple(v: str):
        try:
            parts = v.lstrip("v").split(".")
            return tuple(int(x) for x in parts)
        except Exception:
            return (0, 0)

    return {
        "recommendation": sorted(list(rec_versions), key=parse_version_tuple),
        "forecast": sorted(list(forecast_versions), key=parse_version_tuple),
    }
