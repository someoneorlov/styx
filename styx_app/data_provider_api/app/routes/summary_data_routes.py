from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.dependencies import get_db_session
from ..models import SummaryInferenceResultBatch, NewsIDs
from ..services.summary_data_services import (
    mark_news_as_processed,
    save_summary_results,
)

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db_session)):
    try:
        db.execute(text("SELECT 1"))
        logger.info("Health check successful")
        return {"status": "ok", "message": "Data Provider API is up and running"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@router.post("/summary_mark_processed")
async def update_processed_flag(
    news_ids: NewsIDs, db: Session = Depends(get_db_session)
):
    try:
        successfully_marked_ids = mark_news_as_processed(db, news_ids.news_ids)
        if successfully_marked_ids:
            logger.info(f"News items {successfully_marked_ids} marked as processed")
            return {
                "message": "News items marked as processed",
                "processed_ids": successfully_marked_ids,
            }
        else:
            logger.warning(
                f"Failed to mark news items {news_ids.news_ids} as processed"
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Failed to mark news items as processed"},
            )
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during marking as processed: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during marking as processed: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


@router.post("/summary_save_results")
async def save_summary_inference_results(
    results: SummaryInferenceResultBatch,
    db: Session = Depends(get_db_session),
):
    try:
        successfully_saved_ids = save_summary_results(results, db)
        if successfully_saved_ids:
            logger.info("Summary results saved successfully")
            return {
                "message": "Summary results saved successfully",
                "saved_ids": successfully_saved_ids,
            }
        else:
            logger.warning("Failed to save Summary results")
            return JSONResponse(
                status_code=400, content={"detail": "Failed to save Summary results"}
            )
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during saving Summary results: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during saving Summary results: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
