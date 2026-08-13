"""
Model Management API Router
=============================
Exposes REST endpoints for the AI Model Management & Retraining Pipeline.

Endpoints:
    GET  /api/v1/model/status            — Current model versions and metrics
    POST /api/v1/model/retrain/manual    — Trigger manual retraining (Admin/Manager only)
    POST /api/v1/model/retrain/automatic — Evaluate auto-retrain rules and trigger if needed
    GET  /api/v1/model/progress          — Live training progress
    GET  /api/v1/model/history           — Previous training run history

Security:
    Retraining endpoints are restricted to Admin and Store Manager roles.
    The role is extracted from the existing mock-JWT token format:
        Authorization: Bearer mock-jwt-{base64(username:role:userId)}

    Employees receive a 403 Forbidden response.

Why separate from existing routers?
    This module is an ADDITIVE extension.  Placing it in its own router
    file ensures zero risk of modifying existing endpoint behaviour.
    It follows the same API_PREFIX (/api/v1) convention for consistency.
"""

import base64
import logging
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from ..database import get_db

logger = logging.getLogger("model_management.router")

# ═══════════════════════════════════════════════════════════════════════════════
# Router Configuration
# ═══════════════════════════════════════════════════════════════════════════════
router = APIRouter(
    prefix="/model",
    tags=["AI Model Management"],
    responses={
        403: {"description": "Forbidden — insufficient privileges"},
        409: {"description": "Conflict — training already in progress"},
        500: {"description": "Internal server error"},
    },
)

# ═══════════════════════════════════════════════════════════════════════════════
# Authentication Helpers
# ═══════════════════════════════════════════════════════════════════════════════
# Roles that are permitted to trigger model retraining.
# Employee is explicitly excluded as per the specification.
TRAINING_ALLOWED_ROLES = {"Admin", "Store Manager"}


def _extract_user_from_token(
    authorization: Optional[str] = Header(None),
) -> Tuple[str, str, str]:
    """
    Extract username, role, and user_id from the mock-JWT token.

    The existing login system (routers/users.py) generates tokens in the format:
        mock-jwt-{base64(username:role:userId)}

    This function decodes that token to extract the user's identity.

    Parameters
    ----------
    authorization : str, optional
        The Authorization header value (e.g., "Bearer mock-jwt-...").

    Returns
    -------
    Tuple[str, str, str]
        (username, role, user_id)

    Raises
    ------
    HTTPException 401
        If the Authorization header is missing or the token is invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required. Please log in first.",
        )

    # Strip "Bearer " prefix if present
    token = authorization
    if token.lower().startswith("bearer "):
        token = token[7:]

    # Strip "mock-jwt-" prefix
    if not token.startswith("mock-jwt-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format. Expected mock-jwt-{encoded} format.",
        )

    encoded_part = token[len("mock-jwt-"):]

    try:
        decoded = base64.b64decode(encoded_part).decode("utf-8")
        parts = decoded.split(":")
        if len(parts) < 3:
            raise ValueError("Token must contain username:role:userId")

        username = parts[0]
        role = parts[1]
        user_id = parts[2]
        return username, role, user_id

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )


def require_training_role(
    authorization: Optional[str] = Header(None),
) -> Tuple[str, str, str]:
    """
    FastAPI dependency that enforces Admin / Store Manager role for retraining.

    This is used as a Depends() on the retraining endpoints.  It first
    extracts the user identity, then checks if their role is permitted.

    Returns
    -------
    Tuple[str, str, str]
        (username, role, user_id) if authorised.

    Raises
    ------
    HTTPException 403
        If the user's role is not in TRAINING_ALLOWED_ROLES.
    """
    username, role, user_id = _extract_user_from_token(authorization)

    if role not in TRAINING_ALLOWED_ROLES:
        logger.warning(
            f"Training denied for user '{username}' with role '{role}' — "
            f"required: {TRAINING_ALLOWED_ROLES}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Your role '{role}' is not authorised to trigger "
                f"model retraining. Only {', '.join(TRAINING_ALLOWED_ROLES)} can "
                f"perform this action."
            ),
        )

    return username, role, user_id


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 1: GET /model/status
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/status")
def get_model_status():
    """
    Returns the current state of all AI models.

    Response includes:
        - Recommendation and Forecast model versions
        - Last training date
        - Training dataset sizes (products, customers, sales)
        - Model accuracy metrics (Precision@K, RMSE, MAE)
        - Current training status (idle, running, completed, failed)

    This endpoint reads from ``model_metadata.json`` (O(1) file read)
    rather than re-evaluating models on every request.
    """
    from ..model_management.metadata_manager import load_metadata
    from ..model_management.training_progress import TrainingProgress
    from ..model_management.model_version import list_model_versions

    metadata = load_metadata()
    progress = TrainingProgress.get_instance()
    versions = list_model_versions()

    return {
        "recommendation_model_version": metadata.get("recommendation_model_version", "v1.0"),
        "forecast_model_version": metadata.get("forecast_model_version", "v1.0"),
        "last_training_date": metadata.get("trained_on", "N/A"),
        "training_dataset_size": {
            "products": metadata.get("products", 0),
            "customers": metadata.get("customers", 0),
            "sales": metadata.get("sales", 0),
            "inventory": metadata.get("inventory", 0),
        },
        "recommendation_accuracy": metadata.get("accuracy", 0.0),
        "forecast_accuracy": {
            "rmse": metadata.get("forecast_rmse", 0.0),
            "mae": metadata.get("forecast_mae", 0.0),
        },
        "current_training_status": progress.get_status()["status"],
        "available_versions": versions,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 2: POST /model/retrain/manual
# ═══════════════════════════════════════════════════════════════════════════════
@router.post("/retrain/manual", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_retraining(
    auth: Tuple[str, str, str] = Depends(require_training_role),
    db: Session = Depends(get_db),
):
    """
    Triggers a manual model retraining run.

    Requires Admin or Store Manager role.
    Returns 202 Accepted immediately — training runs in the background.
    Poll ``GET /api/v1/model/progress`` for live updates.

    Returns 403 Forbidden if the user's role is Employee.
    Returns 409 Conflict if another training run is already in progress.
    """
    username, role, user_id = auth

    try:
        from ..model_management.training_service import start_manual_retraining
        result = await start_manual_retraining(user=username, role=role, db=db)
        logger.info(f"Manual retraining triggered by {username} ({role})")
        return result

    except RuntimeError as e:
        # Training already in progress
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start manual retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start retraining: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 3: POST /model/retrain/automatic
# ═══════════════════════════════════════════════════════════════════════════════
@router.post("/retrain/automatic", status_code=status.HTTP_202_ACCEPTED)
async def trigger_automatic_retraining(
    auth: Tuple[str, str, str] = Depends(require_training_role),
    db: Session = Depends(get_db),
):
    """
    Evaluates automatic retraining rules and triggers if conditions are met.

    Rules evaluated:
        1. Data Growth: Has any table grown >10% since last training?
        2. Time Staleness: Have >7 days passed since last training?

    If NO rules are triggered, returns 200 with a message explaining why.
    If rules ARE triggered, starts retraining and returns 202 Accepted.

    Requires Admin or Store Manager role.
    """
    username, role, user_id = auth

    try:
        from ..model_management.scheduler import evaluate_retraining_rules
        from ..model_management.training_service import start_automatic_retraining

        # Evaluate rules
        should_retrain, reasons = evaluate_retraining_rules(db)

        if not should_retrain:
            return {
                "message": "Automatic retraining not needed at this time",
                "reasons": reasons,
                "status": "skipped",
            }

        # Rules triggered — start retraining
        result = await start_automatic_retraining(
            user=username, role=role, db=db, reasons=reasons
        )
        logger.info(
            f"Automatic retraining triggered by {username} ({role}) — "
            f"reasons: {reasons}"
        )
        return result

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start automatic retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate/start automatic retraining: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 4: GET /model/progress
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/progress")
def get_training_progress():
    """
    Returns the current training progress.

    Response includes:
        - current_stage: Human-readable stage name
        - percentage: 0–100
        - status: idle | running | completed | failed
        - started_at: ISO timestamp
        - error_message: Present only if status is "failed"

    This endpoint is designed to be polled by the frontend (e.g., every 2s)
    to display a live progress bar during retraining.
    """
    from ..model_management.training_progress import TrainingProgress

    progress = TrainingProgress.get_instance()
    return progress.get_status()


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 5: GET /model/history
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/history")
def get_training_history():
    """
    Returns the complete training history (all past runs).

    Each entry includes:
        - Training timestamps (start, end, duration)
        - Triggering user and role
        - Reason for training (manual, automatic)
        - Dataset sizes at time of training
        - Model accuracy metrics
        - Model versions produced
        - Success/failure status

    Results are returned in reverse chronological order (newest first).
    """
    from ..model_management.training_logger import get_training_history

    history = get_training_history()
    return {
        "total_runs": len(history),
        "history": history,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint 6: POST /model/verify-password
# ═══════════════════════════════════════════════════════════════════════════════
from pydantic import BaseModel

class VerifyPasswordRequest(BaseModel):
    password: str

@router.post("/verify-password")
def verify_training_password(
    payload: VerifyPasswordRequest,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Verify the training authorization password.
    Requires Admin or Store Manager role.
    """
    if payload.password == "trainmodel":
        return {"status": "success", "message": "Authorized"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect training authorization password"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints 7 & 8: GET & PUT /model/training-settings & /model/settings
# ═══════════════════════════════════════════════════════════════════════════════
from ..model_management.settings_manager import load_settings, save_settings

class TrainingSettingsSchema(BaseModel):
    enabled: bool = True
    sales_threshold: int
    customer_threshold: int
    product_threshold: int = 50
    training_interval_months: int
    check_interval_hours: int = 24
    min_precision: float = 0.0
    max_rmse: float = 100.0
    approval_mode: str = "automatic"

# Compatibility schema for old frontend calling /settings
class LegacySettingsSchema(BaseModel):
    sales_threshold: int
    customers_threshold: int
    time_threshold_months: int

@router.get("/training-settings")
def get_training_settings(auth: Tuple[str, str, str] = Depends(require_training_role)):
    """
    Get retraining configurations.
    Requires Admin or Store Manager role.
    """
    settings = load_settings()
    return {
        "enabled": settings.get("enabled", True),
        "sales_threshold": settings.get("sales_threshold", 1000),
        "customer_threshold": settings.get("customer_threshold", 500),
        "customers_threshold": settings.get("customer_threshold", 500),  # frontend compatibility
        "product_threshold": settings.get("product_threshold", 50),
        "training_interval_months": settings.get("training_interval_months", 1),
        "time_threshold_months": settings.get("training_interval_months", 1),  # frontend compatibility
        "check_interval_hours": settings.get("check_interval_hours", 24),
        "min_precision": settings.get("min_precision", 0.0),
        "max_rmse": settings.get("max_rmse", 100.0),
        "approval_mode": settings.get("approval_mode", "automatic")
    }

@router.put("/training-settings")
def update_training_settings(
    settings: TrainingSettingsSchema,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Update retraining configurations.
    Requires Admin or Store Manager role.
    """
    new_settings = settings.dict()
    # Populate duplicate fields for safety
    new_settings["customers_threshold"] = new_settings["customer_threshold"]
    new_settings["time_threshold_months"] = new_settings["training_interval_months"]
    save_settings(new_settings)
    
    # Audit log settings change
    from ..model_management.mlops_manager import write_audit_log
    username, role, _ = auth
    write_audit_log(username, role, "TRAINING_SETTINGS_CHANGED", details=f"Settings updated: {new_settings}")
    
    return {"status": "success", "message": "Settings updated successfully", "settings": new_settings}

# Backward compatibility routes
@router.get("/settings")
def get_legacy_settings(auth: Tuple[str, str, str] = Depends(require_training_role)):
    settings = load_settings()
    return {
        "sales_threshold": settings.get("sales_threshold", 1000),
        "customers_threshold": settings.get("customer_threshold", 500),
        "time_threshold_months": settings.get("training_interval_months", 1)
    }

@router.put("/settings")
def update_legacy_settings(
    settings: LegacySettingsSchema,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    current = load_settings()
    current["sales_threshold"] = settings.sales_threshold
    current["customer_threshold"] = settings.customers_threshold
    current["customers_threshold"] = settings.customers_threshold
    current["training_interval_months"] = settings.time_threshold_months
    current["time_threshold_months"] = settings.time_threshold_months
    save_settings(current)
    return {"status": "success", "message": "Settings updated successfully", "settings": current}


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints 9 & 10: GET /model/dataset-status & POST /model/sync-datasets
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/dataset-status")
def get_dataset_sync_status(
    auth: Tuple[str, str, str] = Depends(require_training_role),
    db: Session = Depends(get_db)
):
    """
    Compare MySQL row counts versus CSV row counts.
    Requires Admin or Store Manager role.
    """
    from ..model_management.dataset_sync import get_dataset_status
    try:
        return get_dataset_status(db)
    except Exception as e:
        logger.error(f"Failed to get dataset status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dataset status: {str(e)}"
        )

@router.post("/sync-datasets")
def sync_datasets_endpoint(
    auth: Tuple[str, str, str] = Depends(require_training_role),
    db: Session = Depends(get_db)
):
    """
    Manually trigger database-to-CSV dataset synchronization.
    Requires Admin or Store Manager role.
    """
    from ..model_management.dataset_sync import sync_datasets_from_db, get_dataset_status
    try:
        # Perform sync
        sync_datasets_from_db(db)
        
        # Read the current status detail to construct return stats
        status_details = get_dataset_status(db)
        
        # Write AUDIT trail sync
        from ..model_management.mlops_manager import write_audit_log
        username, role, _ = auth
        write_audit_log(username, role, "DATASET_SYNCHRONIZED", details="Dataset manual synchronization triggered")
        
        return {
            "status": "success",
            "message": "Datasets synchronized successfully",
            "products_added": status_details.get("Products", {}).get("difference", 0),
            "customers_added": status_details.get("Customers", {}).get("difference", 0),
            "sales_added": status_details.get("Sales", {}).get("difference", 0),
            "inventory_updated": status_details.get("Inventory", {}).get("difference", 0),
            "total_products": status_details.get("Products", {}).get("database_count", 0),
            "total_customers": status_details.get("Customers", {}).get("database_count", 0),
            "total_sales": status_details.get("Sales", {}).get("database_count", 0)
        }
    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synchronization failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints 11 - 16: MLOps Model Versioning, Rollback & Approvals APIs
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/versions/{model_type}")
def get_versions_endpoint(
    model_type: str,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    List all model versions and status states for a specific type.
    Requires Admin or Store Manager role.
    """
    if model_type not in ["recommendation", "forecast"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid model_type")
        
    from ..model_management.mlops_manager import load_model_registry
    registry = load_model_registry()
    versions_dict = registry.get(model_type, {}).get("versions", {})
    
    result = []
    for v_name, v_data in versions_dict.items():
        result.append({
            "version": v_name,
            "status": v_data.get("status", "ARCHIVED"),
            "trained_on": v_data.get("training_date"),
            "dataset_version": v_data.get("dataset_version"),
            "metrics": v_data.get("metrics", {})
        })
    return result

@router.get("/{model_type}/{version}")
def get_version_details_endpoint(
    model_type: str,
    version: str,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Get complete metadata and hyperparams of a specific model version.
    Requires Admin or Store Manager role.
    """
    if model_type not in ["recommendation", "forecast"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid model_type")
        
    from ..model_management.mlops_manager import load_model_registry
    registry = load_model_registry()
    versions = registry.get(model_type, {}).get("versions", {})
    if version not in versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model version {version} not found")
        
    return versions[version]

@router.post("/{model_type}/{version}/approve")
def approve_model_endpoint(
    model_type: str,
    version: str,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Approve and activate a model version.
    Requires Admin or Store Manager role.
    """
    username, role, _ = auth
    if model_type not in ["recommendation", "forecast"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid model_type")
        
    from ..model_management.mlops_manager import load_model_registry, update_model_status, write_audit_log
    registry = load_model_registry()
    versions = registry.get(model_type, {}).get("versions", {})
    if version not in versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")
        
    current_status = versions[version].get("status")
    if current_status not in ["PENDING_APPROVAL", "REJECTED", "EVALUATING", "ARCHIVED"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot approve model in state {current_status}")
        
    # Transition status
    success = update_model_status(model_type, version, "ACTIVE", username, role)
    if not success:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to transition status to ACTIVE")
        
    # Copy model file to active root path
    import shutil
    src_pkl = MODELS_DIR / model_type / version / "model.pkl"
    dest_pkl = MODELS_DIR / f"{model_type}_model.pkl"
    
    if not src_pkl.exists():
        # Fallback to flat files
        flat_pkl = MODELS_DIR / f"{model_type}_model_{version}.pkl"
        if flat_pkl.exists():
            src_pkl = flat_pkl
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model binary not found")
            
    try:
        shutil.copy2(src_pkl, dest_pkl)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to activate model file: {e}")
        
    # Update active metadata
    from ..model_management.metadata_manager import load_metadata, save_metadata
    metadata = load_metadata()
    metadata[f"{model_type}_model_version"] = version
    
    v_meta = versions[version]
    metrics_dict = v_meta.get("metrics", {})
    if model_type == "recommendation":
        metadata["accuracy"] = metrics_dict.get("precision_at_k", 0.0)
    else:
        metadata["forecast_rmse"] = metrics_dict.get("rmse", 0.0)
        metadata["forecast_mae"] = metrics_dict.get("mae", 0.0)
    save_metadata(metadata)
    
    # Reload active model
    from ..model_management.model_loader import reload_models
    reload_models()
    
    # Logs
    write_audit_log(username, role, "MODEL_APPROVED", model_type, version)
    write_audit_log(username, role, "MODEL_ACTIVATED", model_type, version)
    
    # Update training report
    try:
        report_file = MODELS_DIR.parent / "reports" / "model_training" / f"{model_type}_{version}_training_report.json"
        if report_file.exists():
            with open(report_file, "r") as f:
                rep = json.load(f)
            rep["final_status"] = "ACTIVE"
            rep["approval_status"] = "Manual Approved"
            with open(report_file, "w") as f:
                json.dump(rep, f, indent=2)
    except Exception:
        pass
        
    return {"status": "success", "message": f"Model {model_type} {version} approved and activated successfully"}

class RejectModelRequest(BaseModel):
    reason: str

@router.post("/{model_type}/{version}/reject")
def reject_model_endpoint(
    model_type: str,
    version: str,
    payload: RejectModelRequest,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Reject a model version.
    Requires Admin or Store Manager role.
    """
    username, role, _ = auth
    if model_type not in ["recommendation", "forecast"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid model_type")
        
    from ..model_management.mlops_manager import load_model_registry, update_model_status, write_audit_log
    registry = load_model_registry()
    versions = registry.get(model_type, {}).get("versions", {})
    if version not in versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")
        
    current_status = versions[version].get("status")
    if current_status not in ["PENDING_APPROVAL", "EVALUATING", "ACTIVE"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot reject model in state {current_status}")
        
    success = update_model_status(model_type, version, "REJECTED", username, role, rejection_reason=payload.reason)
    if not success:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to transition status to REJECTED")
        
    write_audit_log(username, role, "MODEL_REJECTED", model_type, version, details=payload.reason)
    
    # Update training report
    try:
        report_file = MODELS_DIR.parent / "reports" / "model_training" / f"{model_type}_{version}_training_report.json"
        if report_file.exists():
            with open(report_file, "r") as f:
                rep = json.load(f)
            rep["final_status"] = "REJECTED"
            rep["approval_status"] = f"Manual Rejected: {payload.reason}"
            with open(report_file, "w") as f:
                json.dump(rep, f, indent=2)
    except Exception:
        pass
        
    return {"status": "success", "message": f"Model {model_type} {version} rejected"}

@router.post("/{model_type}/rollback/{version}")
def rollback_model_endpoint(
    model_type: str,
    version: str,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Roll back the currently active model to a previous valid version.
    Requires Admin or Store Manager role.
    """
    username, role, _ = auth
    if model_type not in ["recommendation", "forecast"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid model_type")
        
    from ..model_management.mlops_manager import load_model_registry, update_model_status, write_audit_log
    registry = load_model_registry()
    versions = registry.get(model_type, {}).get("versions", {})
    if version not in versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rollback target version {version} not found")
        
    target_status = versions[version].get("status")
    if target_status == "FAILED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot roll back to a FAILED model version")
        
    import shutil
    src_pkl = MODELS_DIR / model_type / version / "model.pkl"
    dest_pkl = MODELS_DIR / f"{model_type}_model.pkl"
    
    if not src_pkl.exists():
        flat_pkl = MODELS_DIR / f"{model_type}_model_{version}.pkl"
        if flat_pkl.exists():
            src_pkl = flat_pkl
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model binary file missing")
            
    former_active = registry[model_type].get("active_version")
    
    if former_active and former_active != version:
        update_model_status(model_type, former_active, "ROLLED_BACK", username, role, rollback_from=version)
        
    update_model_status(model_type, version, "ACTIVE", username, role)
    
    try:
        shutil.copy2(src_pkl, dest_pkl)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to copy rollback model binary: {e}")
        
    # Update active metadata
    from ..model_management.metadata_manager import load_metadata, save_metadata
    metadata = load_metadata()
    metadata[f"{model_type}_model_version"] = version
    v_meta = versions[version]
    metrics_dict = v_meta.get("metrics", {})
    if model_type == "recommendation":
        metadata["accuracy"] = metrics_dict.get("precision_at_k", 0.0)
    else:
        metadata["forecast_rmse"] = metrics_dict.get("rmse", 0.0)
        metadata["forecast_mae"] = metrics_dict.get("mae", 0.0)
    save_metadata(metadata)
    
    # Reload
    from ..model_management.model_loader import reload_models
    reload_models()
    
    write_audit_log(username, role, "MODEL_ROLLED_BACK", model_type, version, details=f"Rolled back from {former_active}")
    write_audit_log(username, role, "MODEL_ACTIVATED", model_type, version)
    
    return {"status": "success", "message": f"Successfully rolled back to version {version}"}

@router.get("/history")
def get_training_history_endpoint(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    trigger_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    version: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    auth: Tuple[str, str, str] = Depends(require_training_role)
):
    """
    Get complete training history with filters and pagination.
    Requires Admin or Store Manager role.
    """
    from ..model_management.training_logger import get_training_history
    history = get_training_history()
    
    filtered = []
    for entry in history:
        if model_type:
            if model_type == "recommendation" and entry.get("recommendation_version") in ["N/A", None]:
                continue
            if model_type == "forecast" and entry.get("forecast_version") in ["N/A", None]:
                continue
                
        if status and entry.get("status") != status:
            continue
            
        if trigger_type and entry.get("reason") != trigger_type:
            continue
            
        if version:
            if entry.get("recommendation_version") != version and entry.get("forecast_version") != version:
                continue
                
        if date_from:
            try:
                entry_date = entry.get("training_start_time", "").split(" ")[0]
                if entry_date < date_from:
                    continue
            except Exception:
                pass
                
        if date_to:
            try:
                entry_date = entry.get("training_start_time", "").split(" ")[0]
                if entry_date > date_to:
                    continue
            except Exception:
                pass
                
        filtered.append(entry)
        
    total = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_items = filtered[start_idx:end_idx]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "history": page_items
    }

