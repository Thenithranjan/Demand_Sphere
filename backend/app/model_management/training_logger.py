"""
Training Logger
================
Appends structured log entries to ``backend/models/training_logs.json``
after every training run (successful or failed).

Why maintain training logs?
    Training logs provide a full audit trail:
    - WHO triggered training (username, role)
    - WHEN it ran (start/end timestamps, duration)
    - WHY it was triggered (manual request, auto rule, etc.)
    - WHAT happened (dataset sizes, accuracy metrics, success/failure)
    - WHICH versions were produced

    This is essential for:
    1. Debugging model regressions ("when did accuracy drop?")
    2. Compliance / audit requirements
    3. Interview demonstration of MLOps maturity
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from . import MODELS_DIR

logger = logging.getLogger("model_management.training_logger")

# Path to the training logs JSON file
TRAINING_LOGS_FILE = MODELS_DIR / "training_logs.json"


def _load_logs() -> List[Dict[str, Any]]:
    """
    Load existing training logs from disk.
    Returns an empty list if the file doesn't exist or is corrupted.
    """
    if not TRAINING_LOGS_FILE.exists():
        return []
    try:
        with open(TRAINING_LOGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read training logs (will create fresh): {e}")
        return []


def _save_logs(logs: List[Dict[str, Any]]) -> None:
    """Persist the full logs list to disk."""
    try:
        with open(TRAINING_LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, default=str)
        logger.info(f"Training log saved → {TRAINING_LOGS_FILE}")
    except IOError as e:
        logger.error(f"Failed to save training logs: {e}")


def append_training_log(
    start_time: datetime,
    end_time: datetime,
    user: str,
    role: str,
    reason: str,
    dataset_sizes: Dict[str, int],
    metrics: Dict[str, Any],
    status: str,
    recommendation_version: str,
    forecast_version: str,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Append a single training log entry after a training run completes.

    Parameters
    ----------
    start_time : datetime
        When the training run began.
    end_time : datetime
        When the training run finished (success or failure).
    user : str
        Username of the person who triggered training.
    role : str
        Role of the triggering user (Admin, Store Manager, etc.).
    reason : str
        Why training was triggered (manual, automatic, data_drift, time_based).
    dataset_sizes : dict
        Row counts per table: {"products": 500, "customers": 2300, ...}
    metrics : dict
        Model performance metrics (accuracy, rmse, mae, etc.).
    status : str
        "success" or "failed".
    recommendation_version : str
        Version string of the recommendation model (e.g., "v1.1").
    forecast_version : str
        Version string of the forecast model (e.g., "v1.1").
    error_message : str, optional
        Error details if status is "failed".

    Returns
    -------
    dict
        The log entry that was appended.
    """
    # Calculate duration
    duration_seconds = (end_time - start_time).total_seconds()

    # Build the log entry
    entry: Dict[str, Any] = {
        "training_id": f"TRN-{start_time.strftime('%Y%m%d-%H%M%S')}",
        "training_start_time": start_time.isoformat(),
        "training_end_time": end_time.isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "duration_human": _format_duration(duration_seconds),
        "user": user,
        "role": role,
        "reason": reason,
        "dataset_sizes": dataset_sizes,
        "metrics": metrics,
        "status": status,
        "recommendation_model_version": recommendation_version,
        "forecast_model_version": forecast_version,
    }

    # Only include error_message if the run failed
    if error_message:
        entry["error_message"] = error_message

    # Append to existing logs
    logs = _load_logs()
    logs.append(entry)
    _save_logs(logs)

    logger.info(
        f"Training log appended: {entry['training_id']} | "
        f"Status: {status} | Duration: {entry['duration_human']}"
    )
    return entry


def get_training_history() -> List[Dict[str, Any]]:
    """
    Retrieve the full training history (all past runs).
    Returns most recent first.
    """
    logs = _load_logs()
    # Return in reverse chronological order (newest first)
    return list(reversed(logs))


def _format_duration(seconds: float) -> str:
    """Convert seconds to a human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.0f}s"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds:.0f}s"
