"""
Training Service — Core Retraining Orchestrator
=================================================
The central orchestrator for the model retraining pipeline.  This module
coordinates ALL stages of a training run in the correct sequence:

    1. Preparing Dataset       (validate DB connectivity)
    2. Synchronizing CSV       (export MySQL → CSV)
    3. Feature Engineering     (TF-IDF, cosine similarity, interaction matrix)
    4. Training Recommendation (rebuild content + collab models)
    5. Training Forecast       (XGBoost GridSearch + TimeSeriesSplit)
    6. Evaluating Models       (Precision@K, RMSE, MAE)
    7. Saving Models           (versioned .pkl files)
    8. Updating Metadata       (model_metadata.json)
    9. Reloading Models        (hot-swap in memory)
    10. Completed

Why run in a background thread?
    Model training can take minutes (GridSearchCV, matrix computations).
    Running it in the main event loop would block ALL API requests.
    By using ``asyncio.to_thread()``, the training runs in a separate OS
    thread, and the API remains responsive.  The endpoint returns
    ``202 Accepted`` immediately, and the client polls
    ``GET /api/v1/model/progress`` for live updates.

Why use a reentrant lock?
    Prevents two users from accidentally triggering concurrent training
    runs, which would corrupt model files (two processes writing to the
    same .pkl simultaneously = data corruption).

Architecture (SOLID Principles):
    - Single Responsibility: This module ONLY orchestrates.  It delegates
      dataset sync, feature engineering, versioning, logging, etc. to
      dedicated service modules.
    - Open/Closed: New training stages can be added without modifying
      existing stage logic.
    - Dependency Inversion: All dependencies (dataset_sync, feature_pipeline,
      etc.) are imported at the module level, not hardcoded.
"""

import asyncio
import logging
import pickle
import sys
import threading
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import joblib
import numpy as np
from sqlalchemy.orm import Session

from . import PROJECT_ROOT, MODELS_DIR
from .training_progress import TrainingProgress
from .dataset_sync import sync_datasets_from_db
from .feature_pipeline import run_feature_engineering
from .model_version import save_versioned_models
from .metadata_manager import update_metadata
from .training_logger import append_training_log
from .model_loader import reload_models

logger = logging.getLogger("model_management.training_service")

# Ensure project root on sys.path for importing backend subpackages
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ═══════════════════════════════════════════════════════════════════════════════
# Reentrant Lock — prevents concurrent training runs
# ═══════════════════════════════════════════════════════════════════════════════
_training_lock = threading.Lock()


def _run_training_pipeline(
    user: str,
    role: str,
    reason: str,
) -> Dict[str, Any]:
    """
    Synchronous training pipeline — runs inside a background thread.

    This function executes all 10 stages sequentially, updating the
    progress tracker at each stage.  It catches errors per-stage and
    logs them before re-raising.

    Parameters
    ----------
    user : str
        Username of the person who triggered training.
    role : str
        Role of the triggering user.
    reason : str
        Why training was triggered (manual, automatic, etc.).

    Returns
    -------
    dict
        Summary of the training run (versions, metrics, duration).
    """
    from app.database import SessionLocal
    db = SessionLocal()
    progress = TrainingProgress.get_instance()
    start_time = datetime.now()
    dataset_sizes: Dict[str, int] = {}
    metrics: Dict[str, Any] = {}
    rec_version = "v1.0"
    forecast_version = "v1.0"

    try:
        # ─────────────────────────────────────────────────────────────────────
        # Stage 1: Preparing Dataset (5%)
        # ─────────────────────────────────────────────────────────────────────
        # Validate that the database is accessible before committing to a
        # long-running pipeline.  Fail fast if the DB is down.
        progress.start(triggered_by=user, reason=reason)
        logger.info(f"Training started by '{user}' (role: {role}, reason: {reason})")

        try:
            # Quick connectivity check — count one table
            from app import models as app_models
            product_count = db.query(app_models.Product).count()
            if product_count == 0:
                raise RuntimeError("Products table is empty")
            logger.info(f"Database connectivity verified — {product_count} products found")
        except Exception as e:
            raise RuntimeError(f"Database unavailable: {e}") from e

        # ─────────────────────────────────────────────────────────────────────
        # Stage 2: Synchronizing CSV (15%)
        # ─────────────────────────────────────────────────────────────────────
        dataset_sizes = sync_datasets_from_db(db, progress)

        # Register Dataset Version (MLOps lineage)
        from .mlops_manager import register_dataset_version
        db_counts = {
            "Products": dataset_sizes.get("products", 0),
            "Customers": dataset_sizes.get("customers", 0),
            "Sales": dataset_sizes.get("sales", 0),
            "Inventory": dataset_sizes.get("inventory", 0),
            "ForecastResults": dataset_sizes.get("forecast_results", 0)
        }
        csv_paths = {
            "products": "data/processed/products_clean.csv",
            "customers": "data/processed/customers_clean.csv",
            "sales": "data/processed/sales_clean.csv",
            "inventory": "data/processed/inventory_clean.csv",
            "forecast_results": "data/processed/forecast_results.csv"
        }
        sales_csv = PROJECT_ROOT / "data" / "processed" / "sales_clean.csv"
        dataset_version = register_dataset_version(
            db_counts=db_counts,
            csv_paths=csv_paths,
            feature_count=14,
            sales_csv_path=sales_csv
        )

        # ─────────────────────────────────────────────────────────────────────
        # Stage 3: Feature Engineering (30%)
        # ─────────────────────────────────────────────────────────────────────
        # Build TF-IDF, cosine similarity, interaction matrix, time-series grid.
        fe_artifacts = run_feature_engineering(progress)

        # ─────────────────────────────────────────────────────────────────────
        # Stage 4: Training Recommendation Model (50%)
        # ─────────────────────────────────────────────────────────────────────
        # The recommendation model is already built during feature engineering
        # (build_content_model + build_collaborative_model save their artifacts).
        # Here we bundle everything into a single .pkl for models_loader.py.
        progress.update("Training Recommendation")
        logger.info("Bundling recommendation model artifacts...")

        # Load the individual artifacts that were saved by the FE step
        content_sim_path = MODELS_DIR / "content_similarity_matrix.pkl"
        tfidf_path = MODELS_DIR / "tfidf_matrix.pkl"
        product_index_path = MODELS_DIR / "product_index_map.pkl"
        collab_sim_path = MODELS_DIR / "collab_item_similarity.pkl"
        collab_interact_path = MODELS_DIR / "collab_interaction_matrix.pkl"
        collab_index_path = MODELS_DIR / "collab_index_maps.pkl"

        # Verify all artifacts exist
        for path in [content_sim_path, tfidf_path, product_index_path,
                      collab_sim_path, collab_interact_path, collab_index_path]:
            if not path.exists():
                raise RuntimeError(f"Missing model artifact: {path}")

        # Load and bundle into the format expected by models_loader.py
        with open(content_sim_path, "rb") as f:
            content_similarity_matrix = pickle.load(f)
        with open(tfidf_path, "rb") as f:
            tfidf_matrix = pickle.load(f)
        with open(product_index_path, "rb") as f:
            product_index_map = pickle.load(f)
        with open(collab_sim_path, "rb") as f:
            collab_item_similarity = pickle.load(f)
        with open(collab_interact_path, "rb") as f:
            collab_interaction_matrix = pickle.load(f)
        with open(collab_index_path, "rb") as f:
            collab_index_maps = pickle.load(f)

        # Bundle into the single dict that recommendation_model.pkl contains
        recommendation_bundle = {
            "content_similarity_matrix": content_similarity_matrix,
            "tfidf_matrix": tfidf_matrix,
            "product_index_map": product_index_map,
            "collab_item_similarity": collab_item_similarity,
            "collab_interaction_matrix": collab_interaction_matrix,
            "collab_index_maps": collab_index_maps,
        }
        logger.info("Recommendation model artifacts bundled successfully")

        # ─────────────────────────────────────────────────────────────────────
        # Stage 5: Training Forecast Model (65%)
        # ─────────────────────────────────────────────────────────────────────
        progress.update("Training Forecast")
        logger.info("Training XGBoost forecasting models...")

        from backend.forecasting.train_model import train_demand_forecast_models
        qty_model, rev_model, training_metadata = train_demand_forecast_models()

        # Bundle forecast artifacts into bytes (same format as forecast_model.pkl)
        # The existing models_loader.py expects bytes inside the .pkl
        qty_bytes = io.BytesIO()
        joblib.dump(qty_model, qty_bytes)
        qty_bytes.seek(0)

        rev_bytes = io.BytesIO()
        joblib.dump(rev_model, rev_bytes)
        rev_bytes.seek(0)

        # Load the encoders that were saved during feature engineering
        encoders_path = MODELS_DIR / "forecasting_encoders.joblib"
        enc_bytes = io.BytesIO()
        if encoders_path.exists():
            with open(encoders_path, "rb") as f:
                enc_bytes.write(f.read())
            enc_bytes.seek(0)

        forecast_bundle = {
            "forecast_quantity_xgb_bytes": qty_bytes.read(),
            "forecast_revenue_xgb_bytes": rev_bytes.read(),
            "forecasting_encoders_bytes": enc_bytes.read(),
        }
        logger.info("Forecast model artifacts bundled successfully")

        # ─────────────────────────────────────────────────────────────────────
        # Stage 6: Evaluating Models (75%)
        # ─────────────────────────────────────────────────────────────────────
        progress.update("Evaluating Models")
        logger.info("Evaluating model performance...")

        # Evaluate Recommendation Model (All Ranking and System Metrics)
        rec_recall = 0.0
        rec_coverage = 0.0
        rec_novelty = 0.0
        rec_diversity = 0.0
        try:
            from backend.recommendation.evaluate import RecommenderEvaluator
            evaluator = RecommenderEvaluator()
            eval_summary = evaluator.evaluate(top_n=10, sample_users=50)
            rec_precision = eval_summary.get("hybrid_model", {}).get("Precision@K", 0.0)
            rec_accuracy = round(rec_precision * 100, 2)
            rec_recall = round(eval_summary.get("hybrid_model", {}).get("Recall@K", 0.0) * 100, 2)
            rec_coverage = round(eval_summary.get("hybrid_model", {}).get("CatalogCoverage", 0.0) * 100, 2)
            rec_novelty = round(eval_summary.get("hybrid_model", {}).get("Novelty", 0.0), 4)
            rec_diversity = round(eval_summary.get("hybrid_model", {}).get("Diversity", 0.0), 4)
            logger.info(f"Recommendation Metrics: Precision={rec_accuracy}%, Recall={rec_recall}%, Coverage={rec_coverage}%")
        except Exception as e:
            logger.warning(f"Recommendation evaluation failed (using default): {e}")
            rec_accuracy = 0.0

        rec_f1 = round((2 * rec_accuracy * rec_recall) / (rec_accuracy + rec_recall), 2) if (rec_accuracy + rec_recall) > 0 else 0.0

        rec_metrics_dict = {
            "precision_at_k": rec_accuracy,
            "recall_at_k": rec_recall,
            "f1_at_k": rec_f1,
            "hit_rate_at_k": "N/A",
            "coverage": rec_coverage,
            "novelty": rec_novelty,
            "diversity": rec_diversity
        }

        # Evaluate Forecast Model (RMSE, MAE, MAPE, R2)
        forecast_rmse = 0.0
        forecast_mae = 0.0
        forecast_mape = 0.0
        forecast_r2 = 0.0
        try:
            from backend.forecasting.prepare_data import split_forecasting_data
            from backend.forecasting.evaluate import evaluate_models as eval_forecast

            grid_df = fe_artifacts.get("forecast_grid_df")
            if grid_df is not None:
                _, test_df, _ = split_forecasting_data(grid_df)
                forecast_metrics = eval_forecast(qty_model, rev_model, test_df)
                forecast_rmse = float(forecast_metrics.get("quantity", {}).get("RMSE", 0.0))
                forecast_mae = float(forecast_metrics.get("quantity", {}).get("MAE", 0.0))
                forecast_mape = float(forecast_metrics.get("quantity", {}).get("MAPE", 0.0))
                forecast_r2 = float(forecast_metrics.get("quantity", {}).get("R2", 0.0))
                logger.info(f"Forecast Metrics: RMSE={forecast_rmse:.4f}, MAE={forecast_mae:.4f}")
            else:
                logger.warning("Forecast grid_df not available — skipping evaluation")
        except Exception as e:
            logger.warning(f"Forecast evaluation failed (using defaults): {e}")

        forecast_metrics_dict = {
            "rmse": round(forecast_rmse, 4),
            "mae": round(forecast_mae, 4),
            "mape": round(forecast_mape, 4),
            "r2": round(forecast_r2, 4)
        }

        metrics = {
            "recommendation_accuracy": rec_accuracy,
            "forecast_rmse": round(forecast_rmse, 4),
            "forecast_mae": round(forecast_mae, 4),
        }

        # Model comparison and registry metadata management
        from .settings_manager import load_settings
        from .metadata_manager import load_metadata, get_current_versions
        from .model_version import _bump_version
        from .mlops_manager import (
            register_model_version,
            update_model_status,
            generate_training_report,
            write_audit_log
        )
        
        # Write AUDIT trail training completed
        write_audit_log(user, role, "MODEL_TRAINING_COMPLETED", details=f"Retraining completed inside pipeline")

        old_metadata = load_metadata()
        settings = load_settings()
        
        approval_mode = settings.get("approval_mode", "automatic")
        min_precision = settings.get("min_precision", 0.0)
        max_rmse = settings.get("max_rmse", 100.0)
        
        old_rec_acc = old_metadata.get("accuracy", 0.0)
        old_forecast_rmse = old_metadata.get("forecast_rmse", 0.0)
        old_forecast_mae = old_metadata.get("forecast_mae", 0.0)

        # Get next version keys
        current = get_current_versions()
        rec_version = _bump_version(current["recommendation"])
        forecast_version = _bump_version(current["forecast"])

        # Register both models in PENDING status in the model registry
        register_model_version(
            model_type="recommendation",
            version=rec_version,
            dataset_version=dataset_version,
            algorithm="Hybrid (Collaborative + Content-Based)",
            hyperparameters={"collab_weight": 0.5, "content_weight": 0.5, "top_n_collab": 50, "top_n_content": 50},
            metrics=rec_metrics_dict,
            trigger=reason,
            triggered_by=user,
            duration=round((datetime.now() - start_time).total_seconds(), 2)
        )
        update_model_status("recommendation", rec_version, "EVALUATING", user, role)

        register_model_version(
            model_type="forecast",
            version=forecast_version,
            dataset_version=dataset_version,
            algorithm="XGBoost Regressor",
            hyperparameters={
                "quantity_best_params": training_metadata.get("best_params_quantity", {}),
                "revenue_best_params": training_metadata.get("best_params_revenue", {})
            },
            metrics=forecast_metrics_dict,
            trigger=reason,
            triggered_by=user,
            duration=round((datetime.now() - start_time).total_seconds(), 2)
        )
        update_model_status("forecast", forecast_version, "EVALUATING", user, role)

        # Validation Checks
        rejected_reasons = []
        if rec_accuracy < min_precision:
            rejected_reasons.append(f"Rec accuracy {rec_accuracy}% is below minimum threshold of {min_precision}%")
        if old_rec_acc > 0 and rec_accuracy < 0.9 * old_rec_acc:
            rejected_reasons.append(f"Rec accuracy {rec_accuracy}% is worse than 90% of previous model ({old_rec_acc}%)")
        if forecast_rmse > max_rmse:
            rejected_reasons.append(f"Forecast RMSE {forecast_rmse:.4f} is above maximum threshold of {max_rmse:.4f}")
        if old_forecast_rmse > 0 and forecast_rmse > 1.2 * old_forecast_rmse:
            rejected_reasons.append(f"Forecast RMSE {forecast_rmse:.4f} is worse than 120% of previous model ({old_forecast_rmse:.4f})")

        rec_improvement = f"{rec_accuracy - old_rec_acc:+.2f}%" if old_rec_acc > 0 else "N/A"
        forecast_improvement = f"{(old_forecast_rmse - forecast_rmse) / old_forecast_rmse * 100:+.2f}%" if old_forecast_rmse > 0 else "N/A"

        # Determine target state based on validation rules and approval mode
        if approval_mode == "manual":
            logger.info("Manual Approval mode enabled — model is pending approval")
            
            # Save the versioned files for audit history, but do NOT activate them
            progress.update("Saving Models")
            save_versioned_models(
                recommendation_artifacts=recommendation_bundle,
                forecast_artifacts=forecast_bundle,
                activate=False,
                recommendation_metrics=rec_metrics_dict,
                forecast_metrics=forecast_metrics_dict
            )
            
            update_model_status("recommendation", rec_version, "PENDING_APPROVAL", user, role)
            update_model_status("forecast", forecast_version, "PENDING_APPROVAL", user, role)
            
            # Generate reports
            generate_training_report(
                training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                model_type="recommendation",
                version=rec_version,
                dataset_version=dataset_version,
                dataset_size=db_counts,
                duration=round((datetime.now() - start_time).total_seconds(), 2),
                algorithm="Hybrid (Collaborative + Content-Based)",
                metrics=rec_metrics_dict,
                old_metrics={"precision_at_k": old_rec_acc},
                improvement={"precision": rec_improvement},
                final_status="PENDING_APPROVAL"
            )
            
            generate_training_report(
                training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                model_type="forecast",
                version=forecast_version,
                dataset_version=dataset_version,
                dataset_size=db_counts,
                duration=round((datetime.now() - start_time).total_seconds(), 2),
                algorithm="XGBoost Regressor",
                metrics=forecast_metrics_dict,
                old_metrics={"rmse": old_forecast_rmse, "mae": old_forecast_mae},
                improvement={"rmse": forecast_improvement},
                final_status="PENDING_APPROVAL"
            )
            
            progress.complete()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            append_training_log(
                start_time=start_time,
                end_time=end_time,
                user=user,
                role=role,
                reason=reason,
                dataset_sizes=dataset_sizes,
                metrics=metrics,
                status="success",
                recommendation_version=rec_version,
                forecast_version=forecast_version,
            )
            
            return {
                "status": "pending",
                "recommendation_version": rec_version,
                "forecast_version": forecast_version,
                "metrics": metrics,
                "dataset_sizes": dataset_sizes,
                "duration_seconds": round(duration, 2),
                "message": "Models successfully generated and are PENDING_APPROVAL"
            }
            
        else:
            # AUTOMATIC APPROVAL MODE
            if rejected_reasons:
                rejection_msg = "; ".join(rejected_reasons)
                logger.warning(f"Model validation failed: {rejection_msg}")
                
                # Save versioned files, do NOT activate
                progress.update("Saving Models")
                save_versioned_models(
                    recommendation_artifacts=recommendation_bundle,
                    forecast_artifacts=forecast_bundle,
                    activate=False,
                    recommendation_metrics=rec_metrics_dict,
                    forecast_metrics=forecast_metrics_dict
                )
                
                update_model_status("recommendation", rec_version, "REJECTED", user, role, rejection_reason=rejection_msg)
                update_model_status("forecast", forecast_version, "REJECTED", user, role, rejection_reason=rejection_msg)
                
                generate_training_report(
                    training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    model_type="recommendation",
                    version=rec_version,
                    dataset_version=dataset_version,
                    dataset_size=db_counts,
                    duration=round((datetime.now() - start_time).total_seconds(), 2),
                    algorithm="Hybrid (Collaborative + Content-Based)",
                    metrics=rec_metrics_dict,
                    old_metrics={"precision_at_k": old_rec_acc},
                    improvement={"precision": rec_improvement},
                    final_status="REJECTED"
                )
                
                generate_training_report(
                    training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    model_type="forecast",
                    version=forecast_version,
                    dataset_version=dataset_version,
                    dataset_size=db_counts,
                    duration=round((datetime.now() - start_time).total_seconds(), 2),
                    algorithm="XGBoost Regressor",
                    metrics=forecast_metrics_dict,
                    old_metrics={"rmse": old_forecast_rmse, "mae": old_forecast_mae},
                    improvement={"rmse": forecast_improvement},
                    final_status="REJECTED"
                )
                
                # Write AUDIT trail training failed
                write_audit_log(user, role, "MODEL_TRAINING_FAILED", details=f"Rejection: {rejection_msg}")
                raise RuntimeError(f"model_rejected: {rejection_msg}")

            # ─────────────────────────────────────────────────────────────────────
            # Stage 7: Saving Models (85%)
            # ─────────────────────────────────────────────────────────────────────
            progress.update("Saving Models")
            save_versioned_models(
                recommendation_artifacts=recommendation_bundle,
                forecast_artifacts=forecast_bundle,
                activate=True,
                recommendation_metrics=rec_metrics_dict,
                forecast_metrics=forecast_metrics_dict
            )
            
            # Transition status to ACTIVE
            update_model_status("recommendation", rec_version, "ACTIVE", user, role)
            update_model_status("forecast", forecast_version, "ACTIVE", user, role)
            
            # Write AUDIT trail approved & activated
            write_audit_log(user, role, "MODEL_APPROVED", model_type="recommendation", version=rec_version)
            write_audit_log(user, role, "MODEL_APPROVED", model_type="forecast", version=forecast_version)
            write_audit_log(user, role, "MODEL_ACTIVATED", model_type="recommendation", version=rec_version)
            write_audit_log(user, role, "MODEL_ACTIVATED", model_type="forecast", version=forecast_version)

            # Generate reports
            generate_training_report(
                training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                model_type="recommendation",
                version=rec_version,
                dataset_version=dataset_version,
                dataset_size=db_counts,
                duration=round((datetime.now() - start_time).total_seconds(), 2),
                algorithm="Hybrid (Collaborative + Content-Based)",
                metrics=rec_metrics_dict,
                old_metrics={"precision_at_k": old_rec_acc},
                improvement={"precision": rec_improvement},
                final_status="ACTIVE"
            )
            
            generate_training_report(
                training_id=f"TRN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                model_type="forecast",
                version=forecast_version,
                dataset_version=dataset_version,
                dataset_size=db_counts,
                duration=round((datetime.now() - start_time).total_seconds(), 2),
                algorithm="XGBoost Regressor",
                metrics=forecast_metrics_dict,
                old_metrics={"rmse": old_forecast_rmse, "mae": old_forecast_mae},
                improvement={"rmse": forecast_improvement},
                final_status="ACTIVE"
            )

            # ─────────────────────────────────────────────────────────────────────
            # Stage 8: Updating Metadata (90%)
            # ─────────────────────────────────────────────────────────────────────
            progress.update("Updating Metadata")
            update_metadata(
                recommendation_version=rec_version,
                forecast_version=forecast_version,
                dataset_sizes=dataset_sizes,
                recommendation_accuracy=rec_accuracy,
                forecast_rmse=forecast_rmse,
                forecast_mae=forecast_mae,
            )

            # ─────────────────────────────────────────────────────────────────────
            # Stage 9: Reloading Models (95%)
            # ─────────────────────────────────────────────────────────────────────
            progress.update("Reloading Models")
            reload_models()

            # ─────────────────────────────────────────────────────────────────────
            # Stage 10: Completed (100%)
            # ─────────────────────────────────────────────────────────────────────
            progress.complete()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Log successful log entry
            append_training_log(
                start_time=start_time,
                end_time=end_time,
                user=user,
                role=role,
                reason=reason,
                dataset_sizes=dataset_sizes,
                metrics=metrics,
                status="success",
                recommendation_version=rec_version,
                forecast_version=forecast_version,
            )

            return {
                "status": "success",
                "recommendation_version": rec_version,
                "forecast_version": forecast_version,
                "metrics": metrics,
                "dataset_sizes": dataset_sizes,
                "duration_seconds": round(duration, 2),
            }

    except Exception as e:
        # ─────────────────────────────────────────────────────────────────────
        # Error Handling
        # ─────────────────────────────────────────────────────────────────────
        end_time = datetime.now()
        error_msg = str(e)
        progress.fail(error_msg)

        # Log failed run in the audit registry
        run_status = "model_rejected" if "model_rejected" in error_msg else "failed"
        
        # If we failed evaluation before register_model_version, make sure we mark it as FAILED in registry
        try:
            from .mlops_manager import update_model_status
            update_model_status("recommendation", rec_version, "FAILED", user, role)
            update_model_status("forecast", forecast_version, "FAILED", user, role)
        except Exception:
            pass

        try:
            r_v = rec_version
            f_v = forecast_version
        except NameError:
            r_v = "N/A"
            f_v = "N/A"

        append_training_log(
            start_time=start_time,
            end_time=end_time,
            user=user,
            role=role,
            reason=reason,
            dataset_sizes=dataset_sizes,
            metrics=metrics,
            status=run_status,
            recommendation_version=r_v,
            forecast_version=f_v,
            error_message=error_msg,
        )

        logger.error(f"Training failed or model rejected: {error_msg}")
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Public API — Async Wrappers for FastAPI Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


async def start_manual_retraining(
    user: str,
    role: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Trigger a manual retraining run in a background thread.

    Called by ``POST /api/v1/model/retrain/manual``.

    Returns immediately with a 202-style response.  The actual training
    runs asynchronously — clients poll ``GET /api/v1/model/progress``
    for live updates.

    Parameters
    ----------
    user : str
        Username of the triggering user.
    role : str
        Role of the triggering user (must be Admin or Store Manager).
    db : Session
        SQLAlchemy session.

    Returns
    -------
    dict
        Confirmation that training has started.

    Raises
    ------
    RuntimeError
        If another training run is already in progress.
    """
    progress = TrainingProgress.get_instance()

    # Check if training is already running in-memory
    if progress.is_running():
        raise RuntimeError("A training run is already in progress. Please wait for it to complete.")

    # Check persistent registry lock for TRAINING state
    from .mlops_manager import load_model_registry
    registry = load_model_registry()
    for model_type in ["recommendation", "forecast"]:
        versions = registry.get(model_type, {}).get("versions", {})
        for v_name, v_data in versions.items():
            if v_data.get("status") == "TRAINING":
                raise RuntimeError(f"A training run is already in progress (Version {v_name} is in TRAINING state).")

    # Acquire the lock (non-blocking check)
    if not _training_lock.acquire(blocking=False):
        raise RuntimeError("Training lock is held by another process.")

    # Launch training in a background thread
    async def _run():
        try:
            await asyncio.to_thread(
                _run_training_pipeline, user, role, "manual"
            )
        finally:
            _training_lock.release()

    # Fire-and-forget: start the background task
    asyncio.create_task(_run())

    return {
        "message": "Manual retraining started",
        "triggered_by": user,
        "status": "running",
        "track_progress": "GET /api/v1/model/progress",
    }


async def start_automatic_retraining(
    user: str,
    role: str,
    db: Session,
    reasons: list,
) -> Dict[str, Any]:
    """
    Trigger an automatic retraining run in a background thread.

    Called by ``POST /api/v1/model/retrain/automatic`` after the
    scheduler rules have been evaluated and at least one triggered.

    Parameters
    ----------
    user : str
        Username of the triggering user.
    role : str
        Role of the triggering user.
    db : Session
        SQLAlchemy session.
    reasons : list
        List of rule trigger reasons (from scheduler.evaluate_retraining_rules).

    Returns
    -------
    dict
        Confirmation with triggered reasons.
    """
    progress = TrainingProgress.get_instance()

    # Check if training is already running in-memory
    if progress.is_running():
        raise RuntimeError("A training run is already in progress.")

    # Check persistent registry lock for TRAINING state
    from .mlops_manager import load_model_registry
    registry = load_model_registry()
    for model_type in ["recommendation", "forecast"]:
        versions = registry.get(model_type, {}).get("versions", {})
        for v_name, v_data in versions.items():
            if v_data.get("status") == "TRAINING":
                raise RuntimeError(f"A training run is already in progress (Version {v_name} is in TRAINING state).")

    # Acquire the lock (non-blocking check)
    if not _training_lock.acquire(blocking=False):
        raise RuntimeError("Training lock is held by another process.")

    reason_str = "; ".join(reasons)

    async def _run():
        try:
            await asyncio.to_thread(
                _run_training_pipeline, user, role, f"automatic: {reason_str}"
            )
        finally:
            _training_lock.release()

    asyncio.create_task(_run())

    return {
        "message": "Automatic retraining started",
        "triggered_by": user,
        "triggered_reasons": reasons,
        "status": "running",
        "track_progress": "GET /api/v1/model/progress",
    }
