from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from styx_packages.data_connector.db_models import (
    RawNewsArticle,
    SummaryResults,
)
from styx_packages.styx_logger.logging_config import setup_logger
from ..models import (
    SummaryInferenceResultBatch,
)

logger = setup_logger(__name__)


def mark_news_as_processed(db: Session, news_ids: List[int]) -> list:
    successfully_marked_ids = []
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        for news_id in news_ids:
            existing_entry = (
                db.query(RawNewsArticle).filter(RawNewsArticle.id == news_id).first()
            )
            if existing_entry and existing_entry.is_processed_summary:
                logger.info(f"News item with ID {news_id} already marked as processed.")
                successfully_marked_ids.append(news_id)
                continue

            try:
                db.query(RawNewsArticle).filter(RawNewsArticle.id == news_id).update(
                    {RawNewsArticle.is_processed_summary: True},
                    synchronize_session="fetch",
                )
                successfully_marked_ids.append(news_id)
                logger.info(
                    f"News item with ID {news_id} marked as processed successfully."
                )
            except SQLAlchemyError as e:
                logger.error(
                    f"Failed to mark news item with ID {news_id} as processed: {e}"
                )
        # Commit once after all entries have been processed
        db.commit()
        logger.info(
            f"Successfully marked {len(successfully_marked_ids)} "
            "news items as processed."
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to mark news items as processed, rolling back: {e}")
    except Exception as e:
        db.rollback()
        logger.error(
            f"An unexpected error occurred while marking news items as processed: {e}"
        )
        raise
    return successfully_marked_ids


def save_summary_results(
    results_data: SummaryInferenceResultBatch, db: Session
) -> list:
    successfully_written_ids = []
    try:
        success_count = 0
        for result in results_data.summary_inference_results:
            # Check for existing entry
            existing_entry = (
                db.query(SummaryResults)
                .filter_by(raw_news_article_id=result.raw_news_id)
                .first()
            )
            if existing_entry:
                logger.info(
                    "Skipping duplicate summary result for ID " f"{result.raw_news_id}"
                )
                successfully_written_ids.append(result.raw_news_id)
                continue

            # Proceed with insertion if no existing entry
            new_result = SummaryResults(
                raw_news_article_id=result.raw_news_id,
                aws_raw_news_article_id=result.aws_raw_news_id,
                summary_text=result.summary_text,
            )
            db.add(new_result)
            successfully_written_ids.append(result.raw_news_id)
            success_count += 1

        # Commit once after all entries have been processed
        db.commit()
        logger.info(
            "Successfully saved/updated summary results for "
            f"{success_count} articles."
        )
    except IntegrityError as e:
        db.rollback()
        logger.info(
            "Duplicate summary result encountered during batch save, rolling back."
        )
        logger.error(f"IntegrityError occurred: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to save summary results: {e}")
        return False
    return successfully_written_ids
