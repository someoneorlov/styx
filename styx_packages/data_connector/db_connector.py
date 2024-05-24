import os
from time import sleep
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError
from styx_packages.styx_logger.logging_config import setup_logger

logger = None


def initialize_logger(use_file_handler=True):
    global logger
    if logger is None:
        logger = setup_logger(__name__, use_file_handler=use_file_handler)


def get_engine(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    db=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    max_retries=5,
    initial_delay=5,
    use_file_handler=True,
):
    initialize_logger(use_file_handler)

    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
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
    initialize_logger(use_file_handler)

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
