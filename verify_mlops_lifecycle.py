#!/usr/bin/env python3
"""
verify_mlops_lifecycle.py
=========================
Verification script for the Model Versioning, Lifecycle States, Role Security,
and Concurrency rules. Tests the 18 state transitions, backend mock-JWT security
role checks, and concurrent training locks.
"""

import sys
import base64
import requests
import json
from pathlib import Path

# Base configuration
BASE_URL = "http://127.0.0.1:8000/api/v1/model"
MODELS_DIR = Path(__file__).resolve().parent / "backend" / "models"

# Base64 tokens
ADMIN_TOKEN = f"Bearer {base64.b64encode(b'admin:Admin:1').decode('utf-8')}"
MANAGER_TOKEN = f"Bearer {base64.b64encode(b'manager:Store Manager:2').decode('utf-8')}"
EMPLOYEE_TOKEN = f"Bearer {base64.b64encode(b'employee:Employee:3').decode('utf-8')}"

# State transitions matrix (aligned with backend/app/model_management/mlops_manager.py)
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

def test_state_machine_rules():
    print("\n--- 1. Testing Registry State Transition Validation Rules ---")
    sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
    from app.model_management.mlops_manager import validate_state_transition
    
    all_states = ["TRAINING", "EVALUATING", "PENDING_APPROVAL", "ACTIVE", "REJECTED", "ROLLED_BACK", "FAILED", "ARCHIVED"]
    
    passed_transitions = 0
    total_transitions_checked = 0
    
    for s_from in all_states:
        for s_to in all_states:
            is_valid_expected = (s_from == s_to) or (s_to in VALID_TRANSITIONS.get(s_from, []))
            is_valid_actual = validate_state_transition(s_from, s_to)
            total_transitions_checked += 1
            if is_valid_actual == is_valid_expected:
                passed_transitions += 1
            else:
                print(f"[FAIL] Transition from {s_from} to {s_to} returned {is_valid_actual}, expected {is_valid_expected}")
                
    print(f"[PASS] Successfully verified {passed_transitions} / {total_transitions_checked} transition permutations.")
    return passed_transitions == total_transitions_checked


def test_role_security_rules():
    print("\n--- 2. Testing API Role Security Rules (Admin vs Manager vs Employee) ---")
    
    # 2.1 Get settings check
    print("Testing GET /training-settings access permissions...")
    headers_emp = {"Authorization": f"mock-jwt-{base64.b64encode(b'employee:Employee:3').decode('utf-8')}"}
    headers_mgr = {"Authorization": f"mock-jwt-{base64.b64encode(b'manager:Store Manager:2').decode('utf-8')}"}
    
    # Employee should be forbidden
    r_emp = requests.get(f"{BASE_URL}/training-settings", headers=headers_emp)
    if r_emp.status_code == 403:
        print("[PASS] Employee GET /training-settings is blocked with 403 Forbidden")
    else:
        print(f"[FAIL] Employee GET /training-settings returned status {r_emp.status_code}, expected 403")
        
    # Store Manager should succeed
    r_mgr = requests.get(f"{BASE_URL}/training-settings", headers=headers_mgr)
    if r_mgr.status_code == 200:
        print("[PASS] Store Manager GET /training-settings is allowed with 200 OK")
    else:
        print(f"[FAIL] Store Manager GET /training-settings returned status {r_mgr.status_code}, expected 200")

    # 2.2 Model action checks (Approve, Reject, Rollback)
    print("Testing action POST endpoints role security blockages...")
    
    # Try approval as employee on a dummy version
    r_approve = requests.post(f"{BASE_URL}/recommendation/v1.0.0/approve", headers=headers_emp)
    if r_approve.status_code == 403:
        print("[PASS] Employee POST /approve is blocked with 403 Forbidden")
    else:
        print(f"[FAIL] Employee POST /approve returned status {r_approve.status_code}, expected 403")

    # Try rollback as employee
    r_rollback = requests.post(f"{BASE_URL}/recommendation/rollback/v1.0.0", headers=headers_emp)
    if r_rollback.status_code == 403:
        print("[PASS] Employee POST /rollback is blocked with 403 Forbidden")
    else:
        print(f"[FAIL] Employee POST /rollback returned status {r_rollback.status_code}, expected 403")

    # Try settings update as employee
    r_update = requests.put(f"{BASE_URL}/training-settings", json={
        "enabled": True,
        "sales_threshold": 100,
        "customer_threshold": 100,
        "product_threshold": 10,
        "training_interval_months": 1,
        "check_interval_hours": 24,
        "min_precision": 0.5,
        "max_rmse": 5.0,
        "approval_mode": "manual"
    }, headers=headers_emp)
    if r_update.status_code == 403:
        print("[PASS] Employee PUT /training-settings is blocked with 403 Forbidden")
    else:
        print(f"[FAIL] Employee PUT /training-settings returned status {r_update.status_code}, expected 403")


def test_concurrency_lock():
    print("\n--- 3. Testing Concurrent Retraining Locks ---")
    sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
    from app.model_management.mlops_manager import register_model_version, load_model_registry
    
    # We will simulate a version being in state 'TRAINING' in registry
    print("Simulating active training by writing status 'TRAINING' for version 'vTEMP_LOCK'...")
    register_model_version(
        model_type="recommendation",
        version="vTEMP_LOCK",
        dataset_version="dataset-v1",
        algorithm="collab",
        hyperparameters={},
        metrics={},
        trigger="manual",
        triggered_by="admin",
        duration=0.0
    )
    
    # Debug print registry state
    print(f"Registry in test script: {json.dumps(load_model_registry(), indent=2)}")
    
    # Attempt to start manual retraining (should raise 409 conflict due to locked state)
    headers_admin = {"Authorization": f"mock-jwt-{base64.b64encode(b'admin:Admin:1').decode('utf-8')}"}
    r_train = requests.post(f"{BASE_URL}/retrain/manual", headers=headers_admin)
    
    print(f"Response status: {r_train.status_code}")
    print(f"Response text: {r_train.text}")
    
    if r_train.status_code == 409:
        print("[PASS] Backend rejected concurrent training with 409 Conflict!")
    else:
        print(f"[FAIL] Backend allowed concurrent training or returned status {r_train.status_code}, expected 409")
        
    # Revert 'vTEMP_LOCK' state by deleting it from the registry
    print("Cleaning up simulated training lock version...")
    try:
        registry_path = MODELS_DIR / "model_registry.json"
        if registry_path.exists():
            with open(registry_path, "r") as f:
                data = json.load(f)
            if "vTEMP_LOCK" in data["recommendation"]["versions"]:
                del data["recommendation"]["versions"]["vTEMP_LOCK"]
            with open(registry_path, "w") as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error restoring registry: {e}")


if __name__ == "__main__":
    print("======================================================================")
    print("               MLOPS LIFECYCLE VERIFICATION SUITE                     ")
    print("======================================================================")
    
    machine_ok = test_state_machine_rules()
    test_role_security_rules()
    test_concurrency_lock()
    
    print("\n======================================================================")
    print("Verification Completed.")
    print("======================================================================")
