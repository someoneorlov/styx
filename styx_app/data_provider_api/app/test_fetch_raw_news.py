# test_fetch_raw_news.py
from .db_connector import get_engine, session_factory
from .services.ner_data_services import get_unprocessed_news


def test_fetch_unprocessed_news():
    engine = get_engine()
    SessionLocal = session_factory(engine)
    with SessionLocal() as session:
        unprocessed_news_batch = get_unprocessed_news(session, batch_size=10)
        for news_item in unprocessed_news_batch:
            print(news_item.title)


if __name__ == "__main__":
    test_fetch_unprocessed_news()
