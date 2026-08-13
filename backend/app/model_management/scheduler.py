"""
Automatic Retraining Scheduler
================================
Defines configurable rules that determine WHEN automatic retraining
should be triggered. Periodically sweeps the database and runs the retraining pipeline.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from sqlalchemy.orm import Session

from app import models
from .metadata_manager import load_metadata
from .settings_manager import load_settings

logger = logging.getLogger("model_management.scheduler")

# Global reference to background task
_scheduler_task: Optional[asyncio.Task] = None
_scheduler_running: bool = False


def evaluate_retraining_rules(db: Session) -> Tuple[bool, List[str]]:
    """
    Evaluate if retraining is required based on dynamic threshold settings.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy database session for counting table rows.

    Returns
    -------
    Tuple[bool, List[str]]
        - bool: True if at least one rule recommends retraining.
        - List[str]: Human-readable reasons for each triggered rule.
    """
    metadata = load_metadata()
    settings = load_settings()

    if not settings.get("enabled", True):
        logger.info("Automatic retraining is currently disabled in settings.")
        return False, ["Automatic retraining is disabled"]

    # 1. Fetch current database record counts
    current_sales = db.query(models.Sale).count()
    current_customers = db.query(models.Customer).count()
    current_products = db.query(models.Product).count()

    # 2. Get dataset sizes from last training run
    last_sales = metadata.get("sales", 0)
    last_customers = metadata.get("customers", 0)
    last_products = metadata.get("products", 0)

    # 3. Calculate additions (ensure non-negative)
    new_sales = max(0, current_sales - last_sales)
    new_customers = max(0, current_customers - last_customers)
    new_products = max(0, current_products - last_products)

    triggered_reasons = []

    # Get settings thresholds
    sales_thresh = settings.get("sales_threshold", 1000)
    cust_thresh = settings.get("customer_threshold", 500)
    prod_thresh = settings.get("product_threshold", 50)
    interval_months = settings.get("training_interval_months", 1)

    logger.info(
        f"Scheduler evaluating rules: New Sales={new_sales}/{sales_thresh}, "
        f"New Customers={new_customers}/{cust_thresh}, "
        f"New Products={new_products}/{prod_thresh}"
    )

    if new_sales >= sales_thresh:
        triggered_reasons.append(f"new_sales_threshold: {new_sales} >= {sales_thresh}")
    if new_customers >= cust_thresh:
        triggered_reasons.append(f"new_customers_threshold: {new_customers} >= {cust_thresh}")
    if new_products >= prod_thresh:
        triggered_reasons.append(f"new_products_threshold: {new_products} >= {prod_thresh}")

    # 4. Check monthly/time-based interval
    trained_on = metadata.get("trained_on", "N/A")
    if trained_on and trained_on != "N/A":
        try:
            last_trained = datetime.strptime(trained_on, "%Y-%m-%d")
            # Calculate months difference (each month is approx 30.4375 days)
            days_elapsed = (datetime.now() - last_trained).days
            months_elapsed = days_elapsed / 30.4375
            if months_elapsed >= interval_months:
                triggered_reasons.append(f"time_interval: {months_elapsed:.2f} months elapsed >= {interval_months}")
        except Exception as e:
            logger.warning(f"Failed to parse last trained date: {e}. Recommending initial training.")
            triggered_reasons.append("initial_training: invalid trained_on date")
    else:
        triggered_reasons.append("initial_training: no trained_on record")

    should_retrain = len(triggered_reasons) > 0
    return should_retrain, triggered_reasons


async def _scheduler_loop():
    """Background loop that executes periodic retraining checks."""
    global _scheduler_running
    logger.info("Automatic retraining scheduler loop started.")
    
    # Run check immediately on start, then every check_interval_hours
    last_check_time = None
    
    while _scheduler_running:
        try:
            settings = load_settings()
            enabled = settings.get("enabled", True)
            check_interval_hours = settings.get("check_interval_hours", 24)
            
            now = datetime.now()
            should_run_check = False
            if last_check_time is None:
                should_run_check = True
            else:
                elapsed_hours = (now - last_check_time).total_seconds() / 3600.0
                if elapsed_hours >= check_interval_hours:
                    should_run_check = True
                    
            if enabled and should_run_check:
                logger.info("Scheduler checking automatic retraining rules...")
                last_check_time = now
                
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    should_retrain, reasons = evaluate_retraining_rules(db)
                    if should_retrain:
                        logger.info(f"Scheduler rules triggered: {reasons}. Starting automatic retraining.")
                        from .training_service import start_automatic_retraining
                        await start_automatic_retraining(
                            user="system",
                            role="System",
                            db=db,
                            reasons=reasons
                        )
                    else:
                        logger.info("Scheduler rules checked: All within thresholds. Retraining skipped.")
                except Exception as e:
                    logger.error(f"Scheduler run evaluation failed: {e}", exc_info=True)
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            
        # Sleep in small ticks to remain highly responsive to shutdowns
        for _ in range(5):
            if not _scheduler_running:
                break
            await asyncio.sleep(1)

    logger.info("Automatic retraining scheduler loop stopped.")


async def start_scheduler():
    """Start the background scheduler task."""
    global _scheduler_task, _scheduler_running
    if _scheduler_task is not None:
        logger.warning("Scheduler task is already running. Skipping startup.")
        return
        
    _scheduler_running = True
    _scheduler_task = asyncio.create_task(_scheduler_loop())
    logger.info("Automatic retraining scheduler initialized successfully.")


async def stop_scheduler():
    """Stop the background scheduler task cleanly."""
    global _scheduler_task, _scheduler_running
    if _scheduler_task is None:
        return
        
    logger.info("Stopping automatic retraining scheduler...")
    _scheduler_running = False
    
    # Cancel task
    _scheduler_task.cancel()
    try:
        await _scheduler_task
    except asyncio.CancelledError:
        pass
    _scheduler_task = None
    logger.info("Scheduler stopped cleanly.")


def get_scheduler_config() -> Dict[str, Any]:
    """
    Return the current scheduler configuration for display in the API.
    """
    settings = load_settings()
    return {
        "enabled": settings.get("enabled", True),
        "sales_threshold": settings.get("sales_threshold", 1000),
        "customer_threshold": settings.get("customer_threshold", 500),
        "product_threshold": settings.get("product_threshold", 50),
        "training_interval_months": settings.get("training_interval_months", 1),
        "check_interval_hours": settings.get("check_interval_hours", 24),
    }
