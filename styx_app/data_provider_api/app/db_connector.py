from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from time import sleep
from sqlalchemy.exc import OperationalError
from .logging_config import setup_logger


logger = setup_logger(__name__)


def get_engine(max_retries=5, initial_delay=5):
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established.")
            return engine
        except OperationalError as error:
            logger.error(f"Attempt {retries + 1} failed: {error}")
            sleep(delay)
            retries += 1
            delay *= 2  # Exponential backoff
    logger.error("Exceeded maximum number of retries to connect to the database.")
    return None


def session_factory(engine):
    if engine is not None:
        SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        return SessionLocal
    else:
        return None


# Example usage
if __name__ == "__main__":
    user = os.getenv("DB_USER", "default_user")
    password = os.getenv("DB_PASS", "default_password")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "default_db_name")

    engine = get_engine(user, password, host, port, db)
    SessionLocal = session_factory(engine)

    # Example on how to use the session
    if SessionLocal:
        db = SessionLocal()
        try:
            # Perform database operations
            result = db.execute(text("SELECT 1"))
            for row in result:
                print(row)
        finally:
            db.close()
