from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from ..logging_config import setup_logger
from ..models import NERNewsBatch, NERInferenceResultBatch, NewsIDs
from ..dependencies import get_db_session
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
        # Attempt a simple database operation to verify connectivity
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Data Provider API is up and running"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@router.get("/ner_unprocessed_news", response_model=NERNewsBatch)
async def fetch_unprocessed_news(
    db: Session = Depends(get_db_session), batch_size: int = 100
):
    try:
        unprocessed_news_batch = get_unprocessed_news(db, batch_size)
        return unprocessed_news_batch
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner_mark_processed")
async def update_processed_flag(
    news_ids: NewsIDs, db: Session = Depends(get_db_session)
):
    try:
        success = mark_news_as_processed(db, news_ids.news_ids)
        if success:
            return {"message": "News items marked as processed"}
        else:
            return JSONResponse(
                status_code=400,
                content={"detail": "Failed to mark news items as processed"},
            )
    except SQLAlchemyError as e:
        logger.error(
            f"ner_mark_processed. SQLAlchemy error: {e.__class__.__name__}: {str(e)}"
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(
            f"ner_mark_processed. Unexpected error: {e.__class__.__name__}: {str(e)}"
        )
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
            return {"message": "NER results saved successfully"}
        else:
            return JSONResponse(
                status_code=400, content={"detail": "Failed to save NER results"}
            )
    except SQLAlchemyError as e:
        logger.error(
            f"ner_mark_processed. SQLAlchemy error: {e.__class__.__name__}: {str(e)}"
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(
            f"ner_mark_processed. Unexpected error: {e.__class__.__name__}: {str(e)}"
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
