from .db_connector import get_engine, session_factory
from .services.ner_data_services import mark_news_as_processed, get_unprocessed_news
from .db_models import RawNewsArticle


def test_mark_news_as_processed():
    engine = get_engine()
    SessionLocal = session_factory(engine)

    with SessionLocal() as session:
        unprocessed_news_batch = get_unprocessed_news(session, batch_size=5)
        news_ids = [news_item.id for news_item in unprocessed_news_batch]

        # news_ids = [1, 2, 3]  # Example IDs

        result = mark_news_as_processed(session, news_ids)

        if result:
            print(f"Successfully marked news items as processed: {news_ids}")
        else:
            print("Failed to mark news items as processed")

        for news_id in news_ids:
            is_processed = (
                session.query(RawNewsArticle)
                .filter_by(id=news_id)
                .first()
                .is_processed_ner
            )
            assert (
                is_processed == True
            ), f"News item with ID {news_id} was not marked as processed."


if __name__ == "__main__":
    test_mark_news_as_processed()
