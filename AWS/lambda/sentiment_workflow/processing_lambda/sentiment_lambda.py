import os
import json
import boto3
import nltk
import pandas as pd
from nltk.stem.porter import PorterStemmer
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.db_connector import get_engine, session_factory
from styx_packages.data_connector.db_models import (
    AWSRawNewsArticle,
    AWSSentimentResults,
)


# Access environment variables at the beginning
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "sentiment-catboost-model-endpoint")
ENVIRONMENT = os.getenv("ENVIRONMENT", "test")
DB_SECRET_NAME = f"rds-db-credentials/styx_nlp_database_{ENVIRONMENT}"

nltk.data.path.append("/opt/python/nltk_data")

use_file_handler = False
logger = setup_logger(__name__, use_file_handler=use_file_handler)
runtime = boto3.client("runtime.sagemaker")

logger.info(f"Environment: {ENVIRONMENT}")


def preprocess_text(text):
    stemmer = PorterStemmer()
    return " ".join([stemmer.stem(word) for word in nltk.word_tokenize(text)])


def fetch_raw_data(db, batch_size=100):
    try:
        raw_data = (
            db.query(
                AWSRawNewsArticle.id,
                AWSRawNewsArticle.raw_news_article_id,
                AWSRawNewsArticle.title,
                AWSRawNewsArticle.text,
            )
            .filter(AWSRawNewsArticle.is_processed_sentiment == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )

        data = pd.DataFrame(
            raw_data, columns=["id", "raw_news_article_id", "title", "text"]
        )
        if data.empty:
            logger.info("No new data to process.")
            return data

        data["text"] = (
            data[["title", "text"]].agg(". ".join, axis=1).apply(preprocess_text)
        )
        return data
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError while fetching raw data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching raw data: {e}")
        raise


def call_sagemaker_endpoint(payload):
    try:
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps(payload),
        )
        result = response["Body"].read().decode("utf-8")
        result_json = json.loads(result)  # Parse the JSON response
        return result_json["predictions"]  # Extract the predictions list
    except ClientError as e:
        logger.error(f"ClientError while calling SageMaker endpoint: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while calling SageMaker endpoint: {e}")
        raise


def save_predictions_to_db(db, data, predictions):
    successfully_written_ids = []
    try:
        for index, row in data.iterrows():
            # Check if the sentiment result already exists
            existing_result = (
                db.query(AWSSentimentResults)
                .filter(AWSSentimentResults.aws_raw_news_article_id == row["id"])
                .first()
            )
            if existing_result:
                logger.info(
                    f"Sentiment result for article ID {row['id']} already exists."
                )
                successfully_written_ids.append(row["id"])
                continue

            # Create new sentiment result entry
            result = AWSSentimentResults(
                aws_raw_news_article_id=row["id"],
                raw_news_article_id=row["raw_news_article_id"],
                sentiment_predict_proba=float(predictions[index]),
            )
            db.add(result)
            successfully_written_ids.append(row["id"])
        db.commit()
        logger.info("Successfully wrote sentiment predictions to DB.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving predictions to DB: {e}")
        raise
    return successfully_written_ids


def mark_news_as_processed(db, news_ids):
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        db.query(AWSRawNewsArticle).filter(AWSRawNewsArticle.id.in_(news_ids)).update(
            {AWSRawNewsArticle.is_processed_sentiment: True},
            synchronize_session="fetch",
        )
        db.commit()
        logger.info(f"{len(news_ids)} news items marked as processed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking news as processed: {e}")
        raise


def lambda_handler(event, context):
    engine = get_engine(
        DB_SECRET_NAME,
        use_file_handler=False,
    )
    SessionLocal = session_factory(engine)
    db = SessionLocal()

    try:
        data = fetch_raw_data(db)
        if data.empty:
            return {"status": "success", "message": "No new data"}

        payload = {"text": data["text"].tolist()}
        predictions = call_sagemaker_endpoint(payload)
        successfully_written_ids = save_predictions_to_db(db, data, predictions)
        mark_news_as_processed(db, successfully_written_ids)

        return {"status": "success", "processed_ids": successfully_written_ids}
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError while processing data: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError while processing data: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error occurred: {e}")
        raise
    finally:
        db.close()
