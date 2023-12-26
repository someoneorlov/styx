import os
import argparse
import feedparser
import logging
import time
import requests
import psycopg2
import hashlib

from logging.handlers import RotatingFileHandler
from requests.exceptions import HTTPError
from newspaper import Article
from datetime import datetime
from psycopg2.extras import execute_batch
from psycopg2 import OperationalError


# Set up the logger
log_file_path = "./update_data.log"

# Set up a rotating log handler (5 MB per file, keep 3 backup)
handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def connect_to_db(
        db_name=None, db_user=None, db_pass=None, db_host=None, db_port="5432",
        max_retries=5, initial_delay=5):
    """Connect to the PostgreSQL database server with exponential backoff retries."""
    # Use environment variables as defaults
    db_name = db_name or os.getenv("DB_NAME", "default_db_name")
    db_user = db_user or os.getenv("DB_USER", "default_user")
    db_pass = db_pass or os.getenv("DB_PASS", "default_password")
    db_host = db_host or os.getenv("DB_HOST", "localhost")
    db_port = db_port or os.getenv("DB_PORT", "5432")

    retries = 0
    delay = initial_delay
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                dbname=db_name, user=db_user, password=db_pass,
                host=db_host, port=db_port
            )
            logger.info("Database connection established.")
            return conn
        except OperationalError as error:
            logger.error(f"Attempt {retries + 1} failed: {error}")
            time.sleep(delay)
            retries += 1
            delay *= 2  # Exponential backoff

    logger.error("Exceeded maximum number of retries to connect to database.")
    return None


def calculate_hash(field):
    """Calculate and return the SHA-256 hash of the given URL."""
    return hashlib.sha256(field.encode()).hexdigest()


def update_hashes_in_database(conn):
    try:
        select_cursor = conn.cursor()
        update_cursor = conn.cursor()

        # Count rows that need hash updates
        select_cursor.execute("SELECT COUNT(*) FROM raw_news_articles WHERE feed_link_hash IS NULL OR title_hash IS NULL OR canonical_link_hash IS NULL")
        count = select_cursor.fetchone()[0]
        logger.info(f"Num rows {count}")

        # Select rows that need hash updates
        select_cursor.execute("SELECT id, feed_link, title, canonical_link FROM raw_news_articles WHERE feed_link_hash IS NULL OR title_hash IS NULL OR canonical_link_hash IS NULL")
        rows_to_update = select_cursor.fetchall()

        for row in rows_to_update:
            id, feed_link, title, canonical_link = row
            feed_link_hash = calculate_hash(feed_link) if feed_link else None
            title_hash = calculate_hash(title) if title else None
            canonical_link_hash = calculate_hash(canonical_link) if canonical_link else None

            # Update the row with new hash values
            update_cursor.execute("""
                UPDATE raw_news_articles
                SET feed_link_hash = %s, title_hash = %s, canonical_link_hash = %s
                WHERE id = %s
            """, (feed_link_hash, title_hash, canonical_link_hash, id))

        conn.commit()
        select_cursor.close()
        update_cursor.close()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        conn.rollback()


def main():
    logger.info(f"{'=' * 30} Start of the log section {'=' * 30}")
    conn = connect_to_db()
    if conn is not None:
        logger.info("Connected to the database successfully")
        try:
            update_hashes_in_database(conn)
            logger.info(
                f"Successfully updated articles into the database"
            )
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error while inserting into PostgreSQL: {error}")
        finally:
            conn.close()
            logger.info("Database connection closed")
    else:
        logger.error("Failed to establish database connection")
    logger.info(f"{'^' * 30} End of the log section {'^' * 30}\n")


if __name__ == "__main__":
    main()
