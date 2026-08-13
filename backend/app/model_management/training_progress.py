"""
Training Progress Tracker
==========================
Thread-safe singleton that tracks the current stage and percentage of a
training run.  The FastAPI endpoint ``GET /api/v1/model/progress`` reads
from this tracker to provide live feedback to the frontend / admin user.

Why thread-safe?
    Training runs inside a background thread (via ``asyncio.to_thread``).
    Simultaneously, HTTP requests may read the progress.  Without a lock,
    the reader could see a partially-updated state (e.g., stage updated
    but percentage not yet changed).  ``threading.Lock`` prevents this.

Why a singleton?
    There can only be ONE training run at a time.  A singleton ensures
    all parts of the pipeline write to the same progress object, and all
    API readers see the same state.
"""

import threading
from datetime import datetime
from typing import Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════════════════════
# Training Stage Definitions
# ═══════════════════════════════════════════════════════════════════════════════
# Each stage has a human-readable name and a percentage value.
# These are ordered — the pipeline advances through them sequentially.
TRAINING_STAGES = [
    {"stage": "Preparing Dataset",          "percentage": 5},
    {"stage": "Synchronizing CSV",          "percentage": 15},
    {"stage": "Feature Engineering",        "percentage": 30},
    {"stage": "Training Recommendation",    "percentage": 50},
    {"stage": "Training Forecast",          "percentage": 65},
    {"stage": "Evaluating Models",          "percentage": 75},
    {"stage": "Saving Models",              "percentage": 85},
    {"stage": "Updating Metadata",          "percentage": 90},
    {"stage": "Reloading Models",           "percentage": 95},
    {"stage": "Completed",                  "percentage": 100},
]


class TrainingProgress:
    """
    Thread-safe progress tracker for model training runs.

    Usage (inside the training thread):
        progress = TrainingProgress.get_instance()
        progress.start()
        progress.update("Synchronizing CSV")
        ...
        progress.complete()

    Usage (inside API endpoint):
        progress = TrainingProgress.get_instance()
        return progress.get_status()
    """

    # Singleton instance
    _instance: Optional["TrainingProgress"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialise with idle state.  Use get_instance() instead of direct construction."""
        self._lock = threading.Lock()
        self._current_stage: str = "Idle"
        self._percentage: int = 0
        self._status: str = "idle"          # idle | running | completed | failed
        self._started_at: Optional[str] = None
        self._completed_at: Optional[str] = None
        self._error_message: Optional[str] = None
        self._triggered_by: Optional[str] = None
        self._trigger_reason: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "TrainingProgress":
        """
        Returns the singleton TrainingProgress instance.
        Thread-safe via double-checked locking.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = TrainingProgress()
        return cls._instance

    # ───────────────────────────────────────────────────────────────────────────
    # Writer Methods (called from the training thread)
    # ───────────────────────────────────────────────────────────────────────────
    def start(self, triggered_by: str = "system", reason: str = "manual") -> None:
        """Mark the beginning of a new training run."""
        with self._lock:
            self._current_stage = "Preparing Dataset"
            self._percentage = 5
            self._status = "running"
            self._started_at = datetime.now().isoformat()
            self._completed_at = None
            self._error_message = None
            self._triggered_by = triggered_by
            self._trigger_reason = reason

    def update(self, stage: str) -> None:
        """
        Advance to the named stage.  The percentage is looked up from
        TRAINING_STAGES automatically.
        """
        # Find the matching stage definition
        stage_info = next(
            (s for s in TRAINING_STAGES if s["stage"] == stage),
            None,
        )
        with self._lock:
            self._current_stage = stage
            if stage_info:
                self._percentage = stage_info["percentage"]
            self._status = "running"

    def complete(self) -> None:
        """Mark training as successfully completed."""
        with self._lock:
            self._current_stage = "Completed"
            self._percentage = 100
            self._status = "completed"
            self._completed_at = datetime.now().isoformat()
            self._error_message = None

    def fail(self, error_message: str) -> None:
        """Mark training as failed with an error message."""
        with self._lock:
            self._status = "failed"
            self._completed_at = datetime.now().isoformat()
            self._error_message = error_message

    def reset(self) -> None:
        """Reset to idle state (called before a new run starts)."""
        with self._lock:
            self._current_stage = "Idle"
            self._percentage = 0
            self._status = "idle"
            self._started_at = None
            self._completed_at = None
            self._error_message = None
            self._triggered_by = None
            self._trigger_reason = None

    # ───────────────────────────────────────────────────────────────────────────
    # Reader Methods (called from API endpoints)
    # ───────────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current training progress as a JSON-serialisable dict.
        Thread-safe — acquires the lock before reading.
        """
        with self._lock:
            return {
                "current_stage": self._current_stage,
                "percentage": self._percentage,
                "status": self._status,
                "started_at": self._started_at,
                "completed_at": self._completed_at,
                "error_message": self._error_message,
                "triggered_by": self._triggered_by,
                "trigger_reason": self._trigger_reason,
            }

    def is_running(self) -> bool:
        """Check if a training run is currently in progress."""
        with self._lock:
            return self._status == "running"
