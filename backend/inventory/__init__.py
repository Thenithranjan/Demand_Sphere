"""
==============================================================================
Inventory Module Initialization: __init__.py
==============================================================================
Purpose:
    Exposes directory configurations, absolute paths, and shared logger
    for the Smart Inventory Optimization module.
==============================================================================
"""

import logging
from pathlib import Path

# Paths
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports" / "inventory"

# Ensure reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("inventory")
