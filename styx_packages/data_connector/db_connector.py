import os
import boto3
import json
from time import sleep
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError
from botocore.exceptions import ClientError
from styx_packages.styx_logger.logging_config import setup_logger


def initialize_logger(use_file_handler=True):
    return setup_logger(__name__, use_file_handler=use_file_handler)


def get_aws_secrets(secret_name, region_name, use_file_handler=True):
    """Fetch secrets from AWS Secrets Manager."""
    logger = initialize_logger(use_file_handler)
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Unable to fetch secrets from AWS: {e}")
        raise e

    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def get_db_credentials(db_secret_name=None):
    if db_secret_name is None:  # Assuming on-premise environments
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASS")
    else:  # Assuming AWS environments
        region_name = os.getenv("REGION_NAME", "us-east-1")
        secrets = get_aws_secrets(db_secret_name, region_name, use_file_handler=True)
        db_host = secrets["host"]
        db_port = secrets["port"]
        db_name = secrets["dbname"]
        db_user = secrets["username"]
        db_pass = secrets["password"]

    return db_host, db_port, db_name, db_user, db_pass


def get_engine(
    db_secret_name=None, max_retries=5, initial_delay=5, use_file_handler=True
):
    logger = initialize_logger(use_file_handler)
    try:
        logger.info(f"Fetching database credentials for secret: {db_secret_name}")
        db_host, db_port, db_name, db_user, db_pass = get_db_credentials(db_secret_name)
        logger.info("Database credentials fetched successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch database credentials: {e}", exc_info=True)
        return None

    DATABASE_URL = (
        f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )
    logger.info(f"Database URL constructed: {DATABASE_URL}")

    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            logger.info(f"Attempting to create database engine. Attempt {retries + 1}")
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successfully established.")
            return engine
        except OperationalError as error:
            logger.error(
                f"Database connection attempt {retries + 1} failed "
                f"with error: {error}. Retrying in {delay} seconds..."
            )
            sleep(delay)
            retries += 1
            delay *= 2  # Exponential backoff

    logger.error(
        "Failed to connect to the database after exceeding maximum retry attempts."
    )
    return None


def session_factory(engine, use_file_handler=True):
    logger = initialize_logger(use_file_handler)
    if engine is not None:
        SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        logger.info("Session factory successfully created.")
        return SessionLocal
    else:
        logger.error(
            "Failed to create a session factory due to missing database engine."
        )
        return None
