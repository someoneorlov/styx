from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db_models import (
    RawNewsArticle,
)
from styx_packages.styx_logger.logging_config import setup_logger
from typing import List
from ..models import (
    ArticleRawAWSBatch,
    ArticleRawAWS,
)

logger = setup_logger(__name__)


def fetch_unprocessed_news(db: Session, batch_size=100) -> ArticleRawAWSBatch:
    try:
        unprocessed_news_batch = (
            db.query(
                RawNewsArticle.id,
                RawNewsArticle.title,
                RawNewsArticle.text,
                RawNewsArticle.publish_date,
                RawNewsArticle.publish_date_source,
                RawNewsArticle.authors,
                RawNewsArticle.media_title,
            )
            .filter(
                RawNewsArticle.is_parsed == True,  # noqa: E712
                RawNewsArticle.is_processed_ner == False,  # noqa: E712
            )
            .limit(batch_size)
            .all()
        )
        # Convert ORM objects to Pydantic models
        aws_news_items: List[ArticleRawAWS] = [
            ArticleRawAWS.from_orm(item) for item in unprocessed_news_batch
        ]
        logger.info(
            f"Successfully fetched {len(unprocessed_news_batch)} "
            f"unprocessed news articles."
        )
        return ArticleRawAWSBatch(articles=aws_news_items)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching unprocessed news from DB: {e}", exc_info=True)
        raise
