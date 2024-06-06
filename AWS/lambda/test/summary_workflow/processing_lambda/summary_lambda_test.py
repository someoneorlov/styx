import os
import json
import boto3
import time
import pandas as pd
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.db_connector import get_engine, session_factory
from styx_packages.data_connector.db_models import (
    AWSRawNewsArticle,
    AWSSummaryResults,
)

ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "flan-t5-small-finetuned-6144-5")
ENVIRONMENT = os.getenv("ENVIRONMENT")
REGION_NAME = os.getenv("REGION_NAME", "us-east-1")
SECRET_NAME = f"rds-db-credentials/styx_nlp_database_{ENVIRONMENT}"
prefix = os.getenv("MODEL_PREFIX", "summarize: ")
batch_size = int(os.getenv("FETCH_RAW_BATCH_SIZE", 10))
model_batch_size = int(os.getenv("MODEL_BATCH_SIZE", 5))
input_length = int(os.getenv("INP_TOKEN_LENGTH", 256))

use_file_handler = False
logger = setup_logger(__name__, use_file_handler=use_file_handler)
runtime = boto3.client("runtime.sagemaker")


def get_secret(secret_name, region_name=REGION_NAME):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e

    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def fetch_raw_data(db, batch_size=batch_size):
    try:
        raw_data = (
            db.query(
                AWSRawNewsArticle.id,
                AWSRawNewsArticle.raw_news_article_id,
                AWSRawNewsArticle.text,
            )
            .filter(AWSRawNewsArticle.is_processed_summary == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )

        data = pd.DataFrame(raw_data, columns=["id", "raw_news_article_id", "text"])
        if data.empty:
            logger.info("No new data to process.")
            return data

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
        return result_json
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
            # Check if the summary result already exists
            existing_result = (
                db.query(AWSSummaryResults)
                .filter(AWSSummaryResults.aws_raw_news_article_id == row["id"])
                .first()
            )
            if existing_result:
                logger.info(
                    f"Summary result for article ID {row['id']} already exists."
                )
                successfully_written_ids.append(row["id"])
                continue

            # Create new summary result entry
            result = AWSSummaryResults(
                aws_raw_news_article_id=row["id"],
                raw_news_article_id=row["raw_news_article_id"],
                summary_text=predictions[index]["generated_text"],
            )
            db.add(result)
            successfully_written_ids.append(row["id"])
        db.commit()
        logger.info("Successfully wrote summary predictions to DB.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving predictions to DB: {e}")
        raise
    return successfully_written_ids


def mark_news_as_processed(db, news_ids):
    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        db.query(AWSRawNewsArticle).filter(AWSRawNewsArticle.id.in_(news_ids)).update(
            {AWSRawNewsArticle.is_processed_summary: True},
            synchronize_session="fetch",
        )
        db.commit()
        logger.info(f"{len(news_ids)} news items marked as processed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking news as processed: {e}")
        raise


def preprocess_input(text: str, input_length: int, prefix: str) -> str:
    tokens = text.split()
    if len(tokens) > input_length - 1:
        return (
            prefix
            + " ".join(tokens[: (input_length - 1) // 2])
            + " "
            + " ".join(tokens[-(input_length - 1) // 2 :])
        )
    else:
        return prefix + text


def lambda_handler(event, context):
    secrets = get_secret(SECRET_NAME, REGION_NAME)

    AWS_DB_HOST = secrets["host"]
    AWS_DB_PORT = secrets["port"]
    AWS_DB_NAME = secrets["dbname"]
    AWS_DB_USER = secrets["username"]
    AWS_DB_PASS = secrets["password"]

    engine = get_engine(
        AWS_DB_HOST,
        AWS_DB_PORT,
        AWS_DB_NAME,
        AWS_DB_USER,
        AWS_DB_PASS,
        use_file_handler=use_file_handler,
    )
    SessionLocal = session_factory(engine, use_file_handler=use_file_handler)
    db = SessionLocal()

    try:
        data = fetch_raw_data(db)
        if data.empty:
            return {"status": "success", "message": "No new data"}

        predictions = []
        start_time = time.time()
        for i in range(0, len(data), model_batch_size):
            iteration_start_time = time.time()
            batch_data = data.iloc[i : i + model_batch_size]
            batch_text = (
                batch_data["text"]
                .apply(lambda x: preprocess_input(x, input_length, prefix))
                .tolist()
            )
            payload = {
                "inputs": batch_text,
                "parameters": {
                    "do_sample": True,
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "top_k": 50,
                    "max_length": 512,
                    "repetition_penalty": 1.03,
                },
            }
            batch_predictions = call_sagemaker_endpoint(payload)
            predictions.extend(batch_predictions)
            current_time = time.time()
            logger.info(
                f"Time from beginning: {current_time-start_time:.2f}s, "
                f"iteration time: {current_time-iteration_start_time:.2f}s"
            )
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
