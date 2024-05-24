from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.dependencies import get_db_session
from ..models import NERNewsBatch, NERInferenceResultBatch, NewsIDs
from ..services.ner_data_services import (
    get_unprocessed_news,
    mark_news_as_processed,
    save_ner_results,
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


@router.get("/ner_unprocessed_news", response_model=NERNewsBatch)
async def fetch_unprocessed_news(
    db: Session = Depends(get_db_session), batch_size: int = 100
):
    try:
        unprocessed_news_batch = get_unprocessed_news(db, batch_size)
        logger.info(
            f"Fetched {len(unprocessed_news_batch.ner_news_items)} "
            "unprocessed news items"
        )
        return unprocessed_news_batch
    except Exception as e:
        logger.error(f"Failed to fetch unprocessed news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch unprocessed news")


@router.post("/ner_mark_processed")
async def update_processed_flag(
    news_ids: NewsIDs, db: Session = Depends(get_db_session)
):
    try:
        success = mark_news_as_processed(db, news_ids.news_ids)
        if success:
            logger.info(f"News items {news_ids.news_ids} marked as processed")
            return {"message": "News items marked as processed"}
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


@router.post("/ner_save_results")
async def save_ner_inference_results(
    ner_results: NERInferenceResultBatch, db: Session = Depends(get_db_session)
):
    try:
        success = save_ner_results(ner_results, db)
        if success:
            logger.info("NER results saved successfully")
            return {"message": "NER results saved successfully"}
        else:
            logger.warning("Failed to save NER results")
            return JSONResponse(
                status_code=400, content={"detail": "Failed to save NER results"}
            )
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during saving NER results: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during saving NER results: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
