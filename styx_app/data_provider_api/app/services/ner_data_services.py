from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..db_models import (
    RawNewsArticle,
    NerResults,
)
from styx_packages.styx_logger.logging_config import setup_logger
from typing import List
from ..models import (
    NERInferenceResultBatch,
    NERNewsBatch,
    NERNewsItem,
)

logger = setup_logger(__name__)


def get_unprocessed_news(db: Session, batch_size=100) -> NERNewsBatch:
    try:
        unprocessed_news_batch = (
            db.query(RawNewsArticle)
            .filter(
                RawNewsArticle.is_parsed == True,  # noqa: E712
                RawNewsArticle.is_processed_ner == False,  # noqa: E712
            )
            .limit(batch_size)
            .all()
        )
        # Convert ORM objects to Pydantic models
        ner_news_items: List[NERNewsItem] = [
            NERNewsItem.from_orm(item) for item in unprocessed_news_batch
        ]
        logger.info(
            f"Successfully fetched {len(unprocessed_news_batch)} "
            f"unprocessed news articles."
        )
        return NERNewsBatch(ner_news_items=ner_news_items)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching unprocessed news from DB: {e}", exc_info=True)
        raise


def mark_news_as_processed(db: Session, news_ids: List[int]):
    try:
        # Retrieve and lock the rows to be updated to prevent race conditions
        articles_to_update = (
            db.query(RawNewsArticle)
            .filter(
                RawNewsArticle.id.in_(news_ids),
                RawNewsArticle.is_processed_ner == False,  # noqa: E712
            )
            .with_for_update()
            .all()
        )  # Lock these rows
        if not articles_to_update:
            logger.info(f"No news items found to mark as processed for IDs: {news_ids}")
            return False
        # Mark them as processed
        for article in articles_to_update:
            article.is_processed_ner = True
        db.commit()
        logger.info(f"Marked news items as processed: {news_ids}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Failed to mark news items as processed {news_ids}: {e}", exc_info=True
        )
        return False


def save_ner_results(ner_results_data: NERInferenceResultBatch, db: Session):
    try:
        success_count = 0
        for ner_result in ner_results_data.ner_inference_results:
            # Check for existing entry
            existing_entry = (
                db.query(NerResults)
                .filter_by(raw_news_article_id=ner_result.raw_news_id)
                .first()
            )
            if existing_entry:
                logger.info(
                    f"Skipping duplicate NER result for ID {ner_result.raw_news_id}"
                )
                continue
            try:
                # Proceed with insertion if no existing entry
                new_ner_result = NerResults(
                    raw_news_article_id=ner_result.raw_news_id,
                    headline_mentions=[
                        mention.dict() for mention in ner_result.headline_mentions
                    ],
                    body_text_mentions=[
                        mention.dict() for mention in ner_result.body_text_mentions
                    ],
                    salient_entities_org=[
                        mention.dict() for mention in ner_result.salient_entities_org
                    ],
                    salient_entities_set=ner_result.salient_entities_set,
                )
                db.add(new_ner_result)
                db.commit()
                success_count += 1
            except IntegrityError:
                db.rollback()  # Rollback in case of a unique constraint violation
                logger.info(
                    f"Duplicate NER result skipped for ID {ner_result.raw_news_id}"
                )
        logger.info(
            f"Successfully saved/updated NER results for {success_count} articles."
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to save NER results: {e}")
        return False
    return True