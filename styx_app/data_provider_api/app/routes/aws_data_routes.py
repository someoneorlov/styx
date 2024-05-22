from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from styx_packages.styx_logger.logging_config import setup_logger
from ..models import ArticleRawAWSBatch, NewsIDs
from ..dependencies import get_db_session
from ..services.aws_data_services import fetch_unprocessed_news, mark_news_as_processed

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/aws_unprocessed_news", response_model=ArticleRawAWSBatch)
async def fetch_news_endpoint(
    db: Session = Depends(get_db_session),
    batch_size: int = 10,
):
    try:
        news_batch = fetch_unprocessed_news(db, batch_size)
        logger.info(f"Fetched {len(news_batch.articles)} unprocessed news items")
        return news_batch
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during fetching news: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch unprocessed news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch unprocessed news")


@router.post("/aws_mark_processed")
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
