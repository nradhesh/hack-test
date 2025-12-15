"""
Celery Worker for Background Debt Calculations.

This worker runs scheduled tasks to:
- Calculate daily debt for all assets
- Update debt snapshots
- Aggregate ward and city scores
"""

from celery import Celery
from celery.schedules import crontab
from datetime import date
import logging

from app.core.config import get_settings
from app.core.database import get_db_context

settings = get_settings()
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "mdi_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "calculate-daily-debts": {
        "task": "app.workers.celery_worker.calculate_all_debts",
        "schedule": crontab(hour=0, minute=30),  # Run at 00:30 daily
    },
    "calculate-daily-scores": {
        "task": "app.workers.celery_worker.calculate_all_scores",
        "schedule": crontab(hour=1, minute=0),  # Run at 01:00 daily
    },
}


@celery_app.task(bind=True, name="app.workers.celery_worker.calculate_all_debts")
def calculate_all_debts(self):
    """Calculate and update debt for all assets."""
    logger.info("Starting daily debt calculation...")
    
    try:
        with get_db_context() as db:
            from app.services.debt_service import DebtService
            debt_service = DebtService(db)
            debt_service.calculate_all_asset_debts()
        
        logger.info("Daily debt calculation completed successfully")
        return {"status": "success", "date": str(date.today())}
    
    except Exception as e:
        logger.error(f"Error in daily debt calculation: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="app.workers.celery_worker.calculate_all_scores")
def calculate_all_scores(self):
    """Calculate and update MDI scores for all wards and city."""
    logger.info("Starting daily score calculation...")
    
    try:
        with get_db_context() as db:
            from app.services.aggregation_service import AggregationService
            agg_service = AggregationService(db)
            agg_service.calculate_all_scores()
        
        logger.info("Daily score calculation completed successfully")
        return {"status": "success", "date": str(date.today())}
    
    except Exception as e:
        logger.error(f"Error in daily score calculation: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(name="app.workers.celery_worker.calculate_asset_debt")
def calculate_asset_debt(asset_id: int):
    """Calculate debt for a single asset."""
    try:
        with get_db_context() as db:
            from app.services.debt_service import DebtService
            debt_service = DebtService(db)
            snapshot = debt_service.create_debt_snapshot(asset_id)
            return {
                "asset_id": asset_id,
                "debt": snapshot.total_debt if snapshot else 0,
                "mdi_score": snapshot.mdi_score if snapshot else 100,
            }
    except Exception as e:
        logger.error(f"Error calculating debt for asset {asset_id}: {e}")
        raise
