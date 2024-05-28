from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from styx_packages.data_connector.db_models import (
    RawNewsArticle,
    SentimentResults,
)
from styx_packages.styx_logger.logging_config import setup_logger
from ..models import (
    SentimentInferenceResultBatch,
)

logger = setup_logger(__name__)


def mark_news_as_processed(db, news_ids):
    successfully_marked_ids = []
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        for news_id in news_ids:
            try:
                db.query(RawNewsArticle).filter(RawNewsArticle.id == news_id).update(
                    {RawNewsArticle.is_processed_sentiment: True},
                    synchronize_session="fetch",
                )
                db.commit()
                successfully_marked_ids.append(news_id)
                logger.info(
                    f"News item with ID {news_id} marked as processed successfully."
                )
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    f"Failed to mark news item with ID {news_id} as processed: {e}"
                )
        logger.info(
            f"Successfully marked {len(successfully_marked_ids)} "
            "news items as processed."
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"An unexpected error occurred while marking news items as processed: {e}"
        )
        raise
    return successfully_marked_ids


def save_sentiment_results(
    sentiment_results_data: SentimentInferenceResultBatch, db: Session
) -> list:
    successfully_written_ids = []
    try:
        success_count = 0
        for sentiment_result in sentiment_results_data.sentiment_inference_results:
            # Check for existing entry
            existing_entry = (
                db.query(SentimentResults)
                .filter_by(raw_news_article_id=sentiment_result.raw_news_id)
                .first()
            )
            if existing_entry:
                logger.info(
                    "Skipping duplicate sentiment result for ID "
                    f"{sentiment_result.raw_news_id}"
                )
                successfully_written_ids.append(sentiment_result.raw_news_id)
                continue

            # Proceed with insertion if no existing entry
            new_sentiment_result = SentimentResults(
                raw_news_article_id=sentiment_result.raw_news_id,
                aws_raw_news_article_id=sentiment_result.aws_raw_news_id,
                sentiment_predict_proba=sentiment_result.sentiment_predict_proba,
            )
            db.add(new_sentiment_result)
            successfully_written_ids.append(sentiment_result.raw_news_id)
            success_count += 1

        # Commit once after all entries have been processed
        db.commit()
        logger.info(
            "Successfully saved/updated sentiment results for "
            f"{success_count} articles."
        )
    except IntegrityError as e:
        db.rollback()
        logger.info(
            "Duplicate sentiment result encountered during batch save, rolling back."
        )
        logger.error(f"IntegrityError occurred: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to save sentiment results: {e}")
        return False
    return successfully_written_ids
