import os
import redis
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from styx_packages.data_connector.db_models import (
    RawNewsArticle,
    NerResults,
    SentimentResults,
    SummaryResults,
)
from styx_packages.styx_logger.logging_config import setup_logger
from ..models import (
    ArticleMainPage,
    ArticlesMPBatch,
)

logger = setup_logger(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_redis_client():
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=os.getenv("REDIS_PORT", 6379),
            password=os.getenv("REDIS_PASS", None),
            db=0,
            decode_responses=True,  # Decode responses from bytes to str
        )
        logger.info("Successfully connected to Redis.")
        return redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")


def fetch_from_cache(redis_client, cache_key):
    try:
        cached_news = redis_client.get(cache_key)
        if cached_news:
            logger.info(f"Cache hit for key {cache_key}")
            news_batch = json.loads(cached_news)
            return ArticlesMPBatch(**news_batch)
    except Exception as e:
        logger.error(f"Failed to fetch from cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch from cache")
    return None


def save_to_cache(redis_client, cache_key, news_batch):
    try:
        redis_client.setex(
            cache_key, 300, json.dumps(news_batch.dict(), default=json_serial)
        )  # Cache for 5 minutes
        logger.info(f"Cached result for key {cache_key}")
    except Exception as e:
        logger.error(f"Failed to cache result: {e}")


def get_company_name_from_redis(redis_client, company_name):
    redis_key = f"ner_mention:{company_name.lower()}"
    matched_company_name = redis_client.get(redis_key)
    if matched_company_name:
        company_name = matched_company_name
        logger.info(f"Found Redis match for {company_name} in key: {redis_key}")
    else:
        logger.info(
            f"No Redis match found for {company_name}, "
            "proceeding with original value."
        )
    return company_name


def query_news_from_db(db, company_name, page, page_size):
    query = (
        db.query(
            RawNewsArticle.title,
            RawNewsArticle.text,
            RawNewsArticle.publish_date,
            RawNewsArticle.canonical_link,
            RawNewsArticle.media_link,
            RawNewsArticle.media_title,
            NerResults.salient_entities_set,
            SentimentResults.sentiment_predict_proba,
            SummaryResults.summary_text,
        )
        .join(NerResults, isouter=False)
        .join(SentimentResults, isouter=False)
        .join(SummaryResults, isouter=False)
    )

    if company_name:
        query = query.filter(NerResults.salient_entities_set.op("@>")([company_name]))

    query = query.order_by(RawNewsArticle.publish_date.desc())

    # Implement pagination
    total_items = query.count()
    total_pages = (total_items + page_size - 1) // page_size
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    latest_news_batch = query.all()
    logger.info(f"Fetched {len(latest_news_batch)} news items from DB.")

    return latest_news_batch, total_items, total_pages


def transform_news_batch(latest_news_batch):
    front_news_items: List[ArticleMainPage] = []
    for (
        title,
        text,
        publish_date,
        canonical_link,
        media_link,
        media_title,
        salient_entities_set,
        sentiment_predict_proba,
        summary_text,
    ) in latest_news_batch:
        article_data = ArticleMainPage(
            title=title,
            text=text,
            publish_date=publish_date,
            canonical_link=canonical_link,
            media_link=media_link,
            media_title=media_title,
            salient_entities_set=(salient_entities_set if salient_entities_set else []),
            sentiment_predict_proba=sentiment_predict_proba,
            summary_text=summary_text,
        )
        front_news_items.append(article_data)
    return front_news_items


def fetch_news(
    db: Session, company_name: Optional[str] = None, page: int = 1, page_size: int = 10
) -> ArticlesMPBatch:
    redis_client = get_redis_client()

    # Handle None company_name
    cache_company_name = company_name if company_name else "all"
    cache_key = f"news:{cache_company_name}:{page}:{page_size}"

    # Check cache first
    cached_news_batch = fetch_from_cache(redis_client, cache_key)
    if cached_news_batch:
        return cached_news_batch

    try:
        if company_name:
            company_name = get_company_name_from_redis(redis_client, company_name)

        latest_news_batch, total_items, total_pages = query_news_from_db(
            db, company_name, page, page_size
        )

        front_news_items = transform_news_batch(latest_news_batch)

        news_batch = ArticlesMPBatch(
            articles=front_news_items,
            total_pages=total_pages,
            current_page=page,
            total_items=total_items,
        )

        # Cache the result with a 5-minute expiration
        save_to_cache(redis_client, cache_key, news_batch)

        return news_batch
    except SQLAlchemyError as e:
        logger.error(f"Error fetching news from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch news from DB")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
