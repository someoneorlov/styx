from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db_models import (
    RawNewsArticle,
    NerResults,
)
from styx_packages.styx_logger.logging_config import setup_logger
from typing import List
from ..models import (
    ArticleMainPage,
    ArticlesMPBatch,
)

logger = setup_logger(__name__)


def fetch_news(
    db: Session, company_name: str = None, batch_size: int = 10
) -> ArticlesMPBatch:
    try:
        query = db.query(
            RawNewsArticle.title,
            RawNewsArticle.text,
            RawNewsArticle.publish_date,
            RawNewsArticle.canonical_link,
            RawNewsArticle.media_link,
            RawNewsArticle.media_title,
            NerResults.salient_entities_set,
        ).join(NerResults, isouter=False)

        # Conditional filtering based on company_name
        if company_name:
            # Assuming company_name is already in the matched format
            query = query.filter(
                NerResults.salient_entities_set.op("@>")([company_name])
            )

        query = query.order_by(RawNewsArticle.publish_date.desc()).limit(batch_size)

        latest_news_batch = query.all()

        front_news_items: List[ArticleMainPage] = []
        for (
            title,
            text,
            publish_date,
            canonical_link,
            media_link,
            media_title,
            salient_entities_set,
        ) in latest_news_batch:
            article_data = ArticleMainPage(
                title=title,
                text=text,
                publish_date=publish_date,
                canonical_link=canonical_link,
                media_link=media_link,
                media_title=media_title,
                salient_entities_set=(
                    salient_entities_set if salient_entities_set else []
                ),
            )
            front_news_items.append(article_data)

        return ArticlesMPBatch(articles=front_news_items)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching news from DB: {e}", exc_info=True)
        raise
