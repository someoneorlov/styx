from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db_models import (
    RawNewsArticle,
    NerResults,
)  # Ensure these are defined in your SQLAlchemy models
from ....logging_config import setup_logger  # Adjust the import path as needed
from typing import List
from ..models import NERInferenceResultBatch  # Adjust import path as needed

logger = setup_logger(__name__)


def get_unprocessed_news(db: Session, batch_size=100):
    try:
        unprocessed_news_batch = (
            db.query(RawNewsArticle)
            .filter(RawNewsArticle.is_processed_ner == False)
            .limit(batch_size)
            .all()
        )
        logger.info(
            f"Successfully fetched {len(unprocessed_news_batch)} unprocessed news articles."
        )
        return unprocessed_news_batch  # Ensure you return a structure that matches NERNewsBatch
    except SQLAlchemyError as e:
        logger.error(f"Failed to fetch unprocessed news: {e}")
        raise


def mark_news_as_processed(db: Session, news_ids: List[int]):
    try:
        result = (
            db.query(RawNewsArticle)
            .filter(RawNewsArticle.id.in_(news_ids))
            .update({RawNewsArticle.is_processed_ner: True})
        )
        db.commit()
        logger.info(f"Marked news items as processed: {news_ids}")
        return True if result else False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to mark news items as processed {news_ids}: {e}")
        return False


def save_ner_results(db: Session, ner_results_data: NERInferenceResultBatch):
    try:
        for ner_result in ner_results_data.ner_inference_results:
            entities = {
                "headline_mentions": [
                    mention.dict() for mention in ner_result.headline_mentions
                ],
                "body_text_mentions": [
                    mention.dict() for mention in ner_result.body_text_mentions
                ],
                "salient_entities_org": [
                    mention.dict() for mention in ner_result.salient_entities_org
                ],
                "salient_entities_set": ner_result.salient_entities_set,
            }
            new_ner_result = NerResults(
                raw_news_article_id=ner_result.raw_news_id, entities=entities
            )
            db.add(new_ner_result)
        db.commit()
        logger.info(
            f"Successfully saved NER results for {len(ner_results_data.ner_inference_results)} articles."
        )
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to save NER results: {e}")
        return False