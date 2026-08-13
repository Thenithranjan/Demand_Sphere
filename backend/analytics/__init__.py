"""
==============================================================================
Analytics Module Initialization: __init__.py
==============================================================================
Purpose:
    Exposes shared configurations, visualization constants, and styling
    utilities across all Exploratory Data Analysis (EDA) submodules.

Design Style:
    Ensures all generated plots share a consistent visual theme.
==============================================================================
"""

import os
import logging
from pathlib import Path
import matplotlib.pyplot as plt

# Define absolute paths for data and reports
ANALYTICS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ANALYTICS_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports" / "eda"

# Create output directories if they do not exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Shared Color Palette (Custom Textile Brand Colors)
# Primary: Deep Indigo (Trust, elegance)
# Secondary: Amber/Gold (Festival, premium sales)
# Accent: Emerald (Profits, safety stock)
# Highlight: Crimson/Rose (Low stock, alerts)
# Complementary: Teal & Charcoal (Neutral grids and backgrounds)
COLORS = {
    "primary": "#1E3A8A",      # Deep Blue
    "secondary": "#D97706",    # Warm Gold/Amber
    "accent": "#059669",       # Rich Emerald
    "danger": "#E11D48",       # Crimson Red
    "teal": "#0D9488",         # Deep Teal
    "neutral_dark": "#374151", # Charcoal Gray
    "neutral_light": "#F3F4F6"# Off-white
}

# Configure analytics logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("analytics")

def set_plot_style() -> None:
    """
    Sets a consistent, premium styling standard for all Matplotlib visualisations.
    Overrides defaults to ensure proper typography, clean axes, and professional spacing.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    
    # Customise global parameters
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#E5E7EB"  # Subtle gray borders
    plt.rcParams["grid.color"] = "#F3F4F6"      # Very light grid lines
    plt.rcParams["grid.linestyle"] = "-"
    plt.rcParams["axes.labelcolor"] = COLORS["neutral_dark"]
    plt.rcParams["xtick.color"] = COLORS["neutral_dark"]
    plt.rcParams["ytick.color"] = COLORS["neutral_dark"]
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["legend.frameon"] = True
    plt.rcParams["legend.facecolor"] = "white"
    plt.rcParams["legend.edgecolor"] = "#E5E7EB"
