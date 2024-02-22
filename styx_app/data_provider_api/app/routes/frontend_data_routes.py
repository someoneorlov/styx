from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from styx_packages.styx_logger.logging_config import setup_logger
from ..models import ArticlesMPBatch
from ..dependencies import get_db_session
from ..services.frontend_data_services import get_latest_news

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/news/latest", response_model=ArticlesMPBatch)
async def fetch_lates_news(db: Session = Depends(get_db_session), batch_size: int = 10):
    try:
        latest_news_batch = get_latest_news(db, batch_size)
        logger.info(f"Fetched {len(latest_news_batch.front_news_items)} latest news")
        return latest_news_batch
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during fetching latest news: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch latest news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest news")
