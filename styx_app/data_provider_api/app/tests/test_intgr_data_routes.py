import pytest
from fastapi.testclient import TestClient
from ..main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


def test_fetch_unprocessed_news(client):
    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    data = response.json()
    print(data)
    assert response.status_code == 200

    # Assert the response structure matches NERNewsBatch
    assert "ner_news_items" in data
    ner_news_items = data["ner_news_items"]

    # Assert the response is not empty and has the expected length
    assert len(ner_news_items) > 0
    assert len(ner_news_items) <= 10  # Assuming batch_size=10

    # Assert the structure of each item in the response
    for item in ner_news_items:
        assert "id" in item
        assert "title" in item
        assert "text" in item
        assert "is_processed_ner" in item
        assert isinstance(item["id"], int)
        assert isinstance(item["title"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["is_processed_ner"], bool)


def test_update_processed_flag(client):
    news_ids = {"news_ids": [1, 2, 3]}
    response = client.post("/ner-data/ner_mark_processed", json=news_ids)
    assert response.status_code == 200


def test_save_ner_inference_results(client):
    mention = {
        "start": 10,
        "length": 7,
        "mention_text": "Example",
        "linked_entity": "http://example.org/entity",
        "confidence_score": 0.95,
        "link_probability": 0.8,
        "entity_type": "ORG",
    }
    ner_results = {
        "ner_inference_results": [
            {
                "raw_news_id": 1,
                "headline_mentions": [mention],
                "body_text_mentions": [mention, mention],
                "salient_entities_org": [mention],
                "salient_entities_set": ["ExampleEntity1", "ExampleEntity2"],
            }
        ]
    }
    response = client.post("/ner-data/ner_save_results", json=ner_results)
    assert response.status_code == 200
