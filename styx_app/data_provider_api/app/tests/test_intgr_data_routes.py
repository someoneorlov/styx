import pytest
import json
from fastapi.testclient import TestClient
from ..dependencies import get_db_session
from ..db_models import RawNewsArticle, NerResults
from ..models import Mention, NERInferenceResult, NERInferenceResultBatch
from ..main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session():
    session_generator = get_db_session()
    session = next(session_generator)
    try:
        yield session
    finally:
        session.close()


def test_fetch_unprocessed_news(client):
    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    assert response.status_code == 200
    data = response.json()
    # Assert the response structure matches NERNewsBatch
    assert "ner_news_items" in data
    ner_news_items = data["ner_news_items"]

    # Assert the response is not empty and has the expected length
    # assert len(ner_news_items) > 0
    assert len(ner_news_items) <= 10  # Assuming batch_size=10

    # Assert the structure of each item in the response
    for item in ner_news_items:
        assert "id" in item
        assert "title" in item
        assert "text" in item
        assert "is_processed_ner" in item
        assert not item["is_processed_ner"]  # Verify items are unprocessed
        assert isinstance(item["id"], int)
        assert isinstance(item["title"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["is_processed_ner"], bool)


def test_update_processed_flag(client, db_session):
    # Precondition: Set specific news items to unprocessed
    news_ids_to_test = [1, 2, 3]
    for news_id in news_ids_to_test:
        db_session.query(RawNewsArticle).filter_by(id=news_id).update(
            {"is_processed_ner": False}
        )
    db_session.commit()

    # Execute the operation to mark news as processed
    response = client.post(
        "/ner-data/ner_mark_processed", json={"news_ids": news_ids_to_test}
    )
    assert response.status_code == 200

    # Postcondition: Verify that the news items are now marked as processed
    # Refresh the session state to ensure updated data is fetched
    db_session.expire_all()
    for news_id in news_ids_to_test:
        article = db_session.query(RawNewsArticle).filter_by(id=news_id).one()
        assert (
            article.is_processed_ner
        ), f"News ID {news_id} was not marked as processed."


def load_test_data():
    with open("ner_test_intgr.json") as f:
        return json.load(f)


def test_save_ner_inference_results(client, db_session):
    # Sample data directly from your ner_inference_api
    test_data = load_test_data()["ner_results"]

    # Transform sample data into Pydantic models
    ner_inference_results = [
        NERInferenceResult(
            raw_news_id=item["raw_news_id"],
            headline_mentions=[
                Mention(
                    start=hm[0],
                    length=hm[1],
                    mention_text=hm[2],
                    linked_entity=hm[3],
                    confidence_score=hm[4],
                    link_probability=hm[5],
                    entity_type=hm[6],
                )
                for hm in item["headline_mentions"]
            ],
            body_text_mentions=[
                Mention(
                    start=bm[0],
                    length=bm[1],
                    mention_text=bm[2],
                    linked_entity=bm[3],
                    confidence_score=bm[4],
                    link_probability=bm[5],
                    entity_type=bm[6],
                )
                for bm in item["body_text_mentions"]
            ],
            salient_entities_org=[
                Mention(
                    start=so[0],
                    length=so[1],
                    mention_text=so[2],
                    linked_entity=so[3],
                    confidence_score=so[4],
                    link_probability=so[5],
                    entity_type=so[6],
                )
                for so in item.get("salient_entities_org", [])
            ],
            salient_entities_set=item["salient_entities_set"],
        )
        for item in test_data
    ]

    ner_results_batch = NERInferenceResultBatch(
        ner_inference_results=ner_inference_results
    )

    # Post the serialized Pydantic model to the endpoint
    response = client.post("/ner-data/ner_save_results", json=ner_results_batch.dict())
    assert response.status_code == 200, response.text

    for news_id in [7343, 7350]:
        ner_result = (
            db_session.query(NerResults)
            .filter(NerResults.raw_news_article_id == news_id)
            .first()
        )
        assert (
            ner_result is not None
        ), f"NER results for news ID {news_id} were not found in the database."


# def test_save_ner_inference_results(client):
#     # Define a template function that returns a serialized mention dictionary
#     def mention_template(id):
#         mention = Mention(
#             start=10 + id,
#             length=7,
#             mention_text=f"Example text {id}",
#             linked_entity=f"http://example.org/entity{id}",
#             confidence_score=0.95,
#             link_probability=0.8,
#             entity_type="ORG",
#         )
#         return mention.dict()  # Convert Pydantic model to dict for serialization

#     news_ids = [1, 2, 3]

#     # Constructing NERInferenceResultBatch with serialized mentions
#     ner_inference_results = [
#         NERInferenceResult(
#             raw_news_id=news_id,
#             headline_mentions=[mention_template(news_id)],
#             body_text_mentions=[mention_template(news_id), mention_template(news_id)],
#             salient_entities_org=[mention_template(news_id)],
#             salient_entities_set=[
#                 f"ExampleEntity{news_id}1",
#                 f"ExampleEntity{news_id}2",
#             ],
#         ).dict()
#         for news_id in news_ids
#     ]

#     ner_results_batch = NERInferenceResultBatch(
#         ner_inference_results=ner_inference_results
#     )

#     # Serialize the entire payload since it contains lists of dictionaries
#     response = client.post("/ner-data/ner_save_results", json=ner_results_batch.dict())
#     assert response.status_code == 200

#     for news_id in news_ids:
#         ner_result = (
#             db_session.query(NerResults)
#             .filter(NerResults.raw_news_article_id == news_id)
#             .first()
#         )
#         assert (
#             ner_result is not None
#         ), f"NER results for news ID {news_id} were not found in the database."
