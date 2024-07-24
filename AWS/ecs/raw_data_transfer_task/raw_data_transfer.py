import os
import requests
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.db_connector import get_engine, session_factory
from styx_packages.data_connector.db_models import AWSRawNewsArticle
from styx_packages.data_connector.api_connector import make_request
from styx_packages.data_connector.ssh_connector import setup_ssh

logger = setup_logger(__name__)

setup_ssh()

ENVIRONMENT = os.getenv("ENVIRONMENT")
DB_SECRET_NAME = f"rds-db-credentials/styx_nlp_database_{ENVIRONMENT}"
DATA_PROVIDER_API_URL = os.getenv("DATA_PROVIDER_API_URL")


def fetch_data(batch_size: int = 100) -> list:
    try:
        logger.info(
            f"Fetching {batch_size} unprocessed news from {DATA_PROVIDER_API_URL}"
        )
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/aws-data/aws_unprocessed_news",
            method="get",
            params={"batch_size": batch_size},
        )
        response.raise_for_status()
        data = response.json().get("articles", [])
        if not data:
            logger.info("No new data fetched from data_provider_api")
        else:
            logger.info(f"Successfully fetched {len(data)} unprocessed news items.")
        return data
    except requests.ConnectionError as e:
        logger.error(f"Failed to connect to fetch raw news: {e}")
        return []
    except requests.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def mark_news_as_processed(news_ids) -> None:
    if news_ids is None or len(news_ids) == 0:
        logger.info("No news items to mark as processed.")
        return
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/aws-data/aws_mark_processed",
            method="post",
            json={"news_ids": news_ids},
        )
        response.raise_for_status()
        logger.info(f"{len(news_ids)} news items marked as processed successfully.")
    except requests.ConnectionError as e:
        logger.error(f"Failed to connect to mark news as processed: {e}")
    except requests.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def handle_rds_operations(data):
    successfully_written_ids = []
    logger.info(f"Preparing to insert {len(data)} articles into the DB...")
    try:
        engine = get_engine(
            DB_SECRET_NAME,
            use_file_handler=False,
        )
        SessionLocal = session_factory(engine)
        db = SessionLocal()

        for item in data:
            existing_article = (
                db.query(AWSRawNewsArticle)
                .filter(AWSRawNewsArticle.raw_news_article_id == item["id"])
                .first()
            )
            if existing_article:
                logger.info(f"Article with ID {item['id']} already exists.")
                continue
            new_article = AWSRawNewsArticle(
                raw_news_article_id=item["id"],
                title=item["title"],
                text=item["text"],
                publish_date=item.get("publish_date"),
                publish_date_source=item.get("publish_date_source"),
                authors=item.get("authors"),
                media_title=item.get("media_title"),
            )
            db.add(new_article)
            successfully_written_ids.append(item["id"])
        db.commit()
        logger.info(f"Successfully inserted {len(successfully_written_ids)} articles.")
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError while inserting articles: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError while inserting articles: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error occurred: {e}")
        raise
    finally:
        db.close()
    if not successfully_written_ids:
        logger.info("No articles were successfully inserted.")
    else:
        logger.info(
            f"Successfully inserted articles with IDs: {successfully_written_ids}"
        )
    return successfully_written_ids


if __name__ == "__main__":
    try:
        data = fetch_data()
        if data:
            successfully_written_ids = handle_rds_operations(data)
            if successfully_written_ids:
                mark_news_as_processed(successfully_written_ids)
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
