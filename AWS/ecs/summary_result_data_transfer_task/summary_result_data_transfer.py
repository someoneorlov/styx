import os
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.db_connector import get_engine, session_factory
from styx_packages.data_connector.db_models import (
    AWSSummaryResults,
)
from styx_packages.data_connector.api_connector import make_request
from styx_packages.data_connector.ssh_connector import setup_ssh

logger = setup_logger(__name__)

setup_ssh()

ENVIRONMENT = os.getenv("ENVIRONMENT")
DB_SECRET_NAME = f"rds-db-credentials/styx_nlp_database_{ENVIRONMENT}"
DATA_PROVIDER_API_URL = os.getenv("DATA_PROVIDER_API_URL")

logger.info(f"Environment: {ENVIRONMENT}")


def fetch_summary_result_data(db, batch_size=30):
    try:
        result_data = (
            db.query(
                AWSSummaryResults.id,
                AWSSummaryResults.aws_raw_news_article_id,
                AWSSummaryResults.raw_news_article_id,
                AWSSummaryResults.summary_text,
            )
            .filter(AWSSummaryResults.is_processed_remote == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )
        # Convert result_data to a format suitable for the remote API
        formatted_data = []
        for row in result_data:
            formatted_data.append(
                {
                    "raw_news_id": row.raw_news_article_id,
                    "aws_raw_news_id": row.aws_raw_news_article_id,
                    "summary_text": row.summary_text,
                }
            )
        return formatted_data
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError while fetching raw data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching raw data: {e}")
        raise


def write_summary_remote(summary_results: List[dict]) -> List[int]:
    ids = [result["raw_news_id"] for result in summary_results]
    try:
        logger.info(f"Saving {len(ids)} Summary results...")
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/summary-data/summary_save_results",
            method="post",
            json={"summary_inference_results": summary_results},
        )
        response.raise_for_status()
        saved_ids = response.json()["saved_ids"]
        logger.info(f"Summary results saved successfully for IDs: {saved_ids}")
        return saved_ids
    except Exception as e:
        logger.error(f"Failed to save summary results: {e}")
        raise


def mark_summary_remote(ids: List[int]) -> List[int]:
    try:
        logger.info(f"Marking {len(ids)} Summary results...")
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/summary-data/summary_mark_processed",
            method="post",
            json={"news_ids": ids},
        )
        response.raise_for_status()
        marked_ids = response.json()["processed_ids"]
        logger.info(f"Summary results marked successfully for IDs: {marked_ids}")
        return marked_ids
    except Exception as e:
        logger.error(f"Failed to mark summary results: {e}")
        raise


def mark_summary_aws(db: Session, news_ids: List[int]) -> None:
    successfully_marked_ids = []
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        for news_id in news_ids:
            # Check if already marked
            existing_entry = (
                db.query(AWSSummaryResults)
                .filter(
                    AWSSummaryResults.raw_news_article_id == news_id,
                    AWSSummaryResults.is_processed_remote == True,  # noqa: E712
                )
                .first()
            )
            if existing_entry:
                logger.info(f"News item with ID {news_id} already marked as processed.")
                successfully_marked_ids.append(news_id)
                continue

            try:
                # Mark as processed
                db.query(AWSSummaryResults).filter(
                    AWSSummaryResults.raw_news_article_id == news_id
                ).update(
                    {AWSSummaryResults.is_processed_remote: True},
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
    return


if __name__ == "__main__":
    try:
        engine = get_engine(
            DB_SECRET_NAME,
            use_file_handler=False,
        )
        SessionLocal = session_factory(engine)
        db = SessionLocal()

        summary_result_data = fetch_summary_result_data(db)
        if summary_result_data:
            summary_written_ids = write_summary_remote(summary_result_data)
            if summary_written_ids:
                summary_marked_ids = mark_summary_remote(summary_written_ids)
                if summary_marked_ids:
                    mark_summary_aws(db, summary_marked_ids)

    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
