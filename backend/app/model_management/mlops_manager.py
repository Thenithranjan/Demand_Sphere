import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("model_management.mlops_manager")

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports" / "model_training"

MODEL_REGISTRY_FILE = MODELS_DIR / "model_registry.json"
DATASET_REGISTRY_FILE = MODELS_DIR / "dataset_registry.json"
AUDIT_TRAIL_FILE = MODELS_DIR / "audit_trail.json"

# State Machine Transitions
VALID_TRANSITIONS = {
    "TRAINING": ["EVALUATING", "FAILED"],
    "EVALUATING": ["PENDING_APPROVAL", "ACTIVE", "REJECTED", "FAILED"],
    "PENDING_APPROVAL": ["ACTIVE", "REJECTED"],
    "ACTIVE": ["ARCHIVED", "ROLLED_BACK"],
    "REJECTED": ["ACTIVE"],
    "ROLLED_BACK": ["ACTIVE"],
    "ARCHIVED": ["ACTIVE"],
    "FAILED": []
}

def load_json_file(file_path: Path, default_factory) -> Any:
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(default_factory(), f, indent=2)
        return default_factory()
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return default_factory()

def save_json_file(file_path: Path, data: Any):
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file and rename atomically where practical
        temp_file = file_path.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        temp_file.replace(file_path)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")

# Registries Loading/Saving
def load_model_registry() -> Dict[str, Any]:
    return load_json_file(MODEL_REGISTRY_FILE, lambda: {"recommendation": {"active_version": None, "versions": {}}, "forecast": {"active_version": None, "versions": {}}})

def save_model_registry(registry: Dict[str, Any]):
    save_json_file(MODEL_REGISTRY_FILE, registry)

def load_dataset_registry() -> Dict[str, Any]:
    return load_json_file(DATASET_REGISTRY_FILE, lambda: {})

def save_dataset_registry(registry: Dict[str, Any]):
    save_json_file(DATASET_REGISTRY_FILE, registry)

def load_audit_trail() -> List[Dict[str, Any]]:
    return load_json_file(AUDIT_TRAIL_FILE, lambda: [])

def save_audit_trail(trail: List[Dict[str, Any]]):
    save_json_file(AUDIT_TRAIL_FILE, trail)

# Audit Log Appender
def write_audit_log(user_id: str, role: str, action: str, model_type: Optional[str] = None, version: Optional[str] = None, details: Optional[str] = None):
    trail = load_audit_trail()
    trail.append({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "role": role,
        "action": action,
        "model_type": model_type,
        "version": version,
        "details": details
    })
    save_audit_trail(trail)
    logger.info(f"Audit Log: {action} by {user_id} ({role}) on {model_type} {version}")

# Dataset Lineage Versioning
def register_dataset_version(db_counts: Dict[str, int], csv_paths: Dict[str, str], feature_count: int, sales_csv_path: Path) -> str:
    registry = load_dataset_registry()
    
    # Compute sales CSV md5 checksum
    checksum = "N/A"
    if sales_csv_path.exists():
        try:
            hash_md5 = hashlib.md5()
            with open(sales_csv_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            checksum = hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not compute checksum for {sales_csv_path}: {e}")

    # Generate version identifier
    v_num = len(registry) + 1
    version_id = f"dataset-v{v_num}"
    
    registry[version_id] = {
        "version": version_id,
        "created_at": datetime.now().isoformat(),
        "products_count": db_counts.get("Products", 0),
        "customers_count": db_counts.get("Customers", 0),
        "sales_count": db_counts.get("Sales", 0),
        "inventory_count": db_counts.get("Inventory", 0),
        "csv_paths": csv_paths,
        "feature_count": feature_count,
        "checksum": checksum
    }
    
    save_dataset_registry(registry)
    logger.info(f"Registered dataset version: {version_id}")
    return version_id

# Model Registry Operations
def register_model_version(
    model_type: str,
    version: str,
    dataset_version: str,
    algorithm: str,
    hyperparameters: Dict[str, Any],
    metrics: Dict[str, Any],
    trigger: str,
    triggered_by: str,
    duration: float
) -> Dict[str, Any]:
    registry = load_model_registry()
    
    version_entry = {
        "model_type": model_type,
        "version": version,
        "status": "TRAINING",
        "dataset_version": dataset_version,
        "algorithm": algorithm,
        "hyperparameters": hyperparameters,
        "metrics": metrics,
        "trigger": trigger,
        "triggered_by": triggered_by,
        "training_duration": duration,
        "training_date": datetime.now().isoformat(),
        "activation_date": None,
        "deactivation_date": None,
        "approval_user": None,
        "approval_role": None,
        "approval_date": None,
        "rejection_reason": None,
        "rollback_from": None
    }
    
    registry[model_type]["versions"][version] = version_entry
    save_model_registry(registry)
    logger.info(f"Registered model version {version} for {model_type} with status TRAINING")
    return version_entry

def validate_state_transition(current_state: str, target_state: str) -> bool:
    if current_state == target_state:
        return True
    allowed = VALID_TRANSITIONS.get(current_state, [])
    return target_state in allowed

def update_model_status(
    model_type: str,
    version: str,
    status: str,
    user: str = "system",
    role: str = "System",
    rejection_reason: Optional[str] = None,
    rollback_from: Optional[str] = None
) -> bool:
    registry = load_model_registry()
    
    if version not in registry[model_type]["versions"]:
        logger.error(f"Model version {version} not found in registry for {model_type}")
        return False
        
    entry = registry[model_type]["versions"][version]
    current_status = entry["status"]
    
    # Validate transition
    if not validate_state_transition(current_status, status):
        logger.warning(f"Invalid transition from {current_status} to {status} for model version {version}")
        return False
        
    entry["status"] = status
    if status == "ACTIVE":
        entry["activation_date"] = datetime.now().isoformat()
        entry["deactivation_date"] = None
        # Handle former active model version deactivation
        former_active = registry[model_type]["active_version"]
        if former_active and former_active != version:
            if former_active in registry[model_type]["versions"]:
                former_entry = registry[model_type]["versions"][former_active]
                former_entry["status"] = "ARCHIVED"
                former_entry["deactivation_date"] = datetime.now().isoformat()
                logger.info(f"Former active version {former_active} for {model_type} marked as ARCHIVED")
        registry[model_type]["active_version"] = version
        
        # Keep track of approval information
        if not entry["approval_date"]:
            entry["approval_user"] = user
            entry["approval_role"] = role
            entry["approval_date"] = datetime.now().isoformat()
            
    elif status == "REJECTED":
        entry["rejection_reason"] = rejection_reason
        entry["deactivation_date"] = datetime.now().isoformat()
        
    elif status == "ROLLED_BACK":
        entry["deactivation_date"] = datetime.now().isoformat()
        entry["rollback_from"] = rollback_from
        
    save_model_registry(registry)
    logger.info(f"Model version {version} status updated to {status}")
    return True

# Training Reports Generator
def generate_training_report(
    training_id: str,
    model_type: str,
    version: str,
    dataset_version: str,
    dataset_size: Dict[str, int],
    duration: float,
    algorithm: str,
    metrics: Dict[str, Any],
    old_metrics: Dict[str, Any],
    improvement: Dict[str, str],
    final_status: str
):
    report = {
        "training_id": training_id,
        "model_type": model_type,
        "version": version,
        "training_date": datetime.now().isoformat(),
        "dataset_version": dataset_version,
        "dataset_size": dataset_size,
        "training_duration_seconds": duration,
        "algorithm": algorithm,
        "metrics": metrics,
        "old_model_metrics": old_metrics,
        "new_model_metrics": metrics,
        "improvement": improvement,
        "approval_status": "Automatic" if final_status == "ACTIVE" else "Pending Approval" if final_status == "PENDING_APPROVAL" else "Rejected",
        "final_status": final_status
    }
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{model_type}_{version}_training_report.json"
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Generated MLOps training report: {report_file}")
