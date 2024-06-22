from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.dependencies import get_db_session
from ..models import ArticlesMPBatch
from ..services.frontend_data_services import fetch_news

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/news", response_model=ArticlesMPBatch)
@router.head("/news")
async def fetch_news_endpoint(
    db: Session = Depends(get_db_session),
    company_name: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    try:
        news_batch = fetch_news(db, company_name, page, page_size)
        logger.info(
            f"Fetched {len(news_batch.articles)} articles"
            + (f" filtered by company {company_name}" if company_name else " latest")
        )
        return news_batch
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during fetching news: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    except Exception as e:
        logger.error(f"Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")
