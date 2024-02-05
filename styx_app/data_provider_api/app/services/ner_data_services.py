from sqlalchemy.orm import Session
from ..db_models import RawNewsArticle  # Import the appropriate model
from ..db_connector import SessionLocal


def get_unprocessed_news():
    with SessionLocal() as db:
        unprocessed_news = (
            db.query(RawNewsArticle)
            .filter(RawNewsArticle.is_processed_ner is False)
            .all()
        )
        return unprocessed_news
