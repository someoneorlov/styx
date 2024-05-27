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
from styx_packages.data_connector.db_models import AWSRawNewsArticle

nltk.data.path.append("/opt/python/nltk_data")

use_file_handler = False

logger = setup_logger(__name__, use_file_handler=use_file_handler)


def get_secret(secret_name, region_name="us-east-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e

    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def preprocess_text(text):
    stemmer = PorterStemmer()
    return " ".join([stemmer.stem(word) for word in nltk.word_tokenize(text)])


def lambda_handler(event, context):
    environment = os.getenv("ENVIRONMENT")
    secret_name = f"rds-db-credentials/styx_nlp_database_{environment}"
    region_name = "us-east-1"
    secrets = get_secret(secret_name, region_name)

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
        batch_size = 3
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
        data["text"] = (
            data[["title", "text"]].agg(". ".join, axis=1).apply(preprocess_text)
        )
        output = data.drop(columns=["title"]).to_csv(index=False)

        data_size = len(output)
        logger.info(f"Size of data to upload: {data_size} bytes")

        s3 = boto3.client("s3")
        preprocessed_key = (
            f"lambda_workflow_data/{environment}/sentiment_workflow/"
            "preprocessed_data/preprocessed_data_batch.csv"
        )
        logger.info("Starting S3 upload")
        s3.put_object(Bucket="styx-nlp-artifacts", Key=preprocessed_key, Body=output)
        logger.info("Completed S3 upload")

        logger.info(
            "Successfully preprocessed and saved data to S3 "
            f"with key: {preprocessed_key}"
        )
        return {"status": "success", "s3_key": preprocessed_key}
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
