"""
==============================================================================
Alert Service Module: alert_service.py
==============================================================================
Why this file is needed:
    A static risk status classification is not useful unless it integrates with
    notification services. This file acts as our **alert dispatch layer**.
    It converts risk classifications and demand alerts into human-readable warnings
    with standardised priority levels (High, Medium, Low) and visual status icons.
    It writes these records to `inventory_alerts.csv` sorted by urgency.

Business Alert Triggers and Priorities:
    1. 🔴 Low Stock Alert (High Priority):
       Triggered by "Out of Stock" or "Critical Stock" (safety buffer breached).
       Requires immediate purchasing action.

    2. 🔴 Low Stock Alert (Medium Priority):
       Triggered by "Low Stock" (reorder point breached).
       Requires standard reordering.

    3. 🟠 High Demand Alert (Medium Priority):
       Triggered by upcoming predicted demand surges exceeding current physical units.
       Requires proactive procurement.

    4. 🔵 Overstock Alert (Low Priority):
       Triggered by stock levels exceeding maximum storage limits.
       Requires markdown or promotion planning.

    5. 🟢 Stock Healthy (Low Priority / Notice):
       Stable status. No action required.
==============================================================================
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

# Set path relative to project root
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inventory import logger

def process_row_alert(row: pd.Series) -> dict:
    """
    Evaluates a single product row and returns an alert dictionary.
    """
    pid = row.get("ProductID", "Unknown")
    pname = row.get("ProductName", "Unknown Product")
    status = row.get("InventoryStatus", "Healthy Stock")
    high_demand = row.get("HighDemandAlert", False)
    curr_stock = int(row.get("CurrentStock", 0))
    safety_stock = int(row.get("SafetyStock", 0))
    reorder_point = int(row.get("ReorderPoint", 0))
    max_stock = int(row.get("MaximumStock", 0))
    forecast = int(row.get("ForecastDemand", 0))
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 🔴 Case 1: Out of Stock (Critical - High Priority)
    if status == "Out of Stock":
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🔴 Low Stock Alert",
            "Priority": "High",
            "Message": f"CRITICAL: {pname} is completely Out of Stock! Immediate restock order required.",
            "Timestamp": timestamp_str
        }
        
    # 🔴 Case 2: Critical Stock (Safety buffer breached - High Priority)
    elif status == "Critical Stock":
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🔴 Low Stock Alert",
            "Priority": "High",
            "Message": f"CRITICAL: {pname} has breached the Safety Stock buffer. Current stock: {curr_stock} units, Safety Stock: {safety_stock} units. Restock urgently!",
            "Timestamp": timestamp_str
        }
        
    # 🔴 Case 3: Low Stock (Reorder point breached - Medium Priority)
    elif status == "Low Stock":
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🔴 Low Stock Alert",
            "Priority": "Medium",
            "Message": f"REORDER: {pname} has breached the Reorder Point. Current stock: {curr_stock} units, Reorder Point: {reorder_point} units. Place purchase order.",
            "Timestamp": timestamp_str
        }
        
    # 🟠 Case 4: High Demand Warning (Medium Priority)
    # Triggered if forecast exceeds stock, and we haven't already raised a critical alert
    elif high_demand:
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🟠 High Demand Alert",
            "Priority": "Medium",
            "Message": f"WARNING: Predicted monthly demand ({forecast} units) for {pname} exceeds current stock ({curr_stock} units). Increase stock levels.",
            "Timestamp": timestamp_str
        }
        
    # 🔵 Case 5: Overstock (Low Priority)
    elif status == "Overstock":
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🔵 Overstock Alert",
            "Priority": "Low",
            "Message": f"NOTICE: {pname} is Overstocked. Current stock: {curr_stock} units, Maximum Stock target: {max_stock} units. Halt purchase orders.",
            "Timestamp": timestamp_str
        }
        
    # 🟢 Case 6: Stock Healthy (Low Priority / Notice)
    else:
        return {
            "ProductID": pid,
            "ProductName": pname,
            "AlertType": "🟢 Stock Healthy",
            "Priority": "Low",
            "Message": f"OK: {pname} stock levels are healthy. Current stock: {curr_stock} units.",
            "Timestamp": timestamp_str
        }

def generate_inventory_alerts(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Evaluates monitored inventory status, maps alerts, sorts them by priority,
    and exports them to inventory_alerts.csv.
    """
    logger.info("Generating real-time inventory alerts...")
    
    alerts_list = []
    for _, row in df.iterrows():
        alert = process_row_alert(row)
        alerts_list.append(alert)
        
    alerts_df = pd.DataFrame(alerts_list)
    
    # Sort alerts logically by priority (High -> Medium -> Low)
    priority_map = {"High": 0, "Medium": 1, "Low": 2}
    alerts_df["PriorityWeight"] = alerts_df["Priority"].map(priority_map)
    alerts_df = alerts_df.sort_values(by="PriorityWeight").drop(columns=["PriorityWeight"]).reset_index(drop=True)
    
    # Save to CSV
    alerts_df.to_csv(output_path, index=False)
    logger.info(f"Inventory alerts generated and saved -> {output_path}")
    
    # Log summary counts
    high_priority = alerts_df[alerts_df["Priority"] == "High"].shape[0]
    med_priority = alerts_df[alerts_df["Priority"] == "Medium"].shape[0]
    low_priority = alerts_df[alerts_df["Priority"] == "Low"].shape[0]
    
    logger.info(f"Alert priority summary: High Priority: {high_priority}, Medium: {med_priority}, Low: {low_priority}")
    
    return alerts_df

if __name__ == "__main__":
    from backend.inventory.inventory_service import get_integrated_inventory_state
    from backend.inventory.reorder_engine import compute_reorder_metrics
    from backend.inventory.stock_monitor import monitor_stock_levels
    
    state = get_integrated_inventory_state()
    enriched = compute_reorder_metrics(state)
    monitored = monitor_stock_levels(enriched)
    
    alerts_csv = PROJECT_ROOT / "inventory_alerts.csv"
    alerts = generate_inventory_alerts(monitored, alerts_csv)
    print(alerts[["ProductID", "AlertType", "Priority", "Message"]].head(10))
