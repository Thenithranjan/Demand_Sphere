"""
Feature Engineering Pipeline
==============================
Orchestrates the feature engineering stage by delegating to the existing
recommendation and forecasting feature builders.

Why delegate instead of reimplementing?
    The existing codebase already contains well-tested, production-quality
    feature engineering logic:
    - ``content_based.build_content_model()`` — TF-IDF + cosine similarity
    - ``collaborative.build_collaborative_model()`` — interaction matrix + item similarity
    - ``prepare_data.prepare_forecasting_data()`` — time-series grid + ordinal encoding

    Reimplementing this logic would:
    1. Violate the DRY principle (Don't Repeat Yourself)
    2. Create maintenance burden (two copies to keep in sync)
    3. Risk introducing bugs in a reimplementation

    Instead, this module acts as an ORCHESTRATOR that calls the existing
    functions in the correct order and reports progress.

Why is feature engineering a separate stage?
    Feature engineering is computationally expensive (TF-IDF vectorisation,
    cosine similarity matrix computation, interaction matrix building).
    Isolating it as a discrete pipeline stage allows:
    - Progress tracking (users can see "Feature Engineering — 30%")
    - Error isolation (if FE fails, we know exactly where to look)
    - Future extensibility (can add new feature steps without touching training)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np

from .training_progress import TrainingProgress
from . import PROJECT_ROOT

logger = logging.getLogger("model_management.feature_pipeline")

# Ensure project root is on sys.path for importing backend subpackages
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_feature_engineering(
    progress: TrainingProgress,
) -> Dict[str, Any]:
    """
    Execute the full feature engineering pipeline.

    This function:
    1. Builds the content-based model (TF-IDF + cosine similarity)
    2. Builds the collaborative filtering model (interaction matrix + item similarity)
    3. Prepares the forecasting feature dataset (time-series grid + encoding)

    All three steps delegate to existing, tested functions.

    Parameters
    ----------
    progress : TrainingProgress
        Progress tracker to update the current stage.

    Returns
    -------
    dict
        Contains the built artifacts needed for subsequent training steps:
        - "content_similarity": np.ndarray
        - "content_pid_to_idx": dict
        - "content_idx_to_pid": dict
        - "collab_item_similarity": np.ndarray
        - "collab_interaction_matrix": np.ndarray
        - "collab_c2i": dict, "collab_i2c": dict
        - "collab_p2i": dict, "collab_i2p": dict

    Raises
    ------
    RuntimeError
        If any feature engineering step fails.
    """
    progress.update("Feature Engineering")
    artifacts: Dict[str, Any] = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Content-Based Feature Engineering
    # ─────────────────────────────────────────────────────────────────────────
    # Builds TF-IDF vectors from product attributes and computes the
    # pairwise cosine similarity matrix.  Saves artifacts to disk.
    logger.info("Running content-based feature engineering...")
    try:
        from backend.recommendation.content_based import build_content_model

        sim_matrix, pid_to_idx, idx_to_pid, products_df = build_content_model()
        artifacts["content_similarity"] = sim_matrix
        artifacts["content_pid_to_idx"] = pid_to_idx
        artifacts["content_idx_to_pid"] = idx_to_pid
        artifacts["products_df"] = products_df
        logger.info(
            f"Content-based model built: "
            f"{sim_matrix.shape[0]}×{sim_matrix.shape[1]} similarity matrix"
        )
    except Exception as e:
        error_msg = f"Content-based feature engineering failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Collaborative Filtering Feature Engineering
    # ─────────────────────────────────────────────────────────────────────────
    # Builds the customer-product interaction matrix from sales history
    # and computes item-item cosine similarity.
    logger.info("Running collaborative filtering feature engineering...")
    try:
        from backend.recommendation.collaborative import build_collaborative_model

        (
            item_sim, interact_mat,
            c2i, i2c, p2i, i2p,
            _products_df,
        ) = build_collaborative_model()

        artifacts["collab_item_similarity"] = item_sim
        artifacts["collab_interaction_matrix"] = interact_mat
        artifacts["collab_c2i"] = c2i
        artifacts["collab_i2c"] = i2c
        artifacts["collab_p2i"] = p2i
        artifacts["collab_i2p"] = i2p
        logger.info(
            f"Collaborative model built: "
            f"{item_sim.shape[0]}×{item_sim.shape[1]} item similarity, "
            f"{interact_mat.shape[0]} customers × {interact_mat.shape[1]} products"
        )
    except Exception as e:
        error_msg = f"Collaborative filtering feature engineering failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Forecasting Feature Engineering
    # ─────────────────────────────────────────────────────────────────────────
    # Builds the Product × Month grid, aggregates sales, engineers temporal
    # features, shifts targets, and encodes categoricals.
    logger.info("Running forecasting feature engineering...")
    try:
        from backend.forecasting.prepare_data import prepare_forecasting_data

        grid_df, encoders = prepare_forecasting_data()
        artifacts["forecast_grid_df"] = grid_df
        artifacts["forecast_encoders"] = encoders
        logger.info(f"Forecasting features prepared: {grid_df.shape[0]} rows")
    except Exception as e:
        error_msg = f"Forecasting feature engineering failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    logger.info("Feature engineering pipeline completed successfully")
    return artifacts
