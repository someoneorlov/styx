import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from ..main import app
from ..models import NERNewsItem, NERNewsBatch
from sqlalchemy.exc import SQLAlchemyError
from ..dependencies import get_db_session

client = TestClient(app)


# Define a fixture for overriding the DB session
@pytest.fixture(scope="module", autouse=True)
def override_db_session():
    # Setup: Override the dependency
    app.dependency_overrides[get_db_session] = lambda: MagicMock()

    yield  # This allows the tests to run with the override in place

    # Teardown: Clear the override after the tests are done
    app.dependency_overrides.clear()


# Success Path Testing
@patch("app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_with_mock(mock_get_unprocessed_news):
    # Mock the return value of get_unprocessed_news
    mock_data = NERNewsBatch(
        ner_news_items=[NERNewsItem(id=1, title="Test News", text="Some text")]
    )

    mock_get_unprocessed_news.return_value = mock_data

    response = client.get("/ner-data/ner_unprocessed_news?batch_size=1")
    assert response.status_code == 200
    # Check that the mocked data is returned
    assert "ner_news_items" in response.json()
    assert response.json()["ner_news_items"][0]["title"] == "Test News"


# Error Handling
@patch("app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_error(mock_get_unprocessed_news):
    mock_get_unprocessed_news.side_effect = Exception("Database error")

    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Failed to fetch unprocessed news" in response.json()["detail"]


# Edge Cases
@patch("app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_edge_cases(mock_get_unprocessed_news):
    mock_get_unprocessed_news.return_value = NERNewsBatch(ner_news_items=[])
    # Test with batch size 0
    response = client.get("/ner-data/ner_unprocessed_news?batch_size=0")
    assert response.status_code == 200
    assert "ner_news_items" in response.json()

    # Test with a large batch size
    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10000")
    assert response.status_code == 200
    assert "ner_news_items" in response.json()


# No Unprocessed News Found
@patch("app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_no_content(mock_get_unprocessed_news):
    mock_get_unprocessed_news.return_value = NERNewsBatch(ner_news_items=[])

    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    assert response.status_code == 200
    assert "ner_news_items" in response.json()
    assert len(response.json()["ner_news_items"]) == 0


@patch("app.routes.ner_data_routes.mark_news_as_processed")
def test_update_processed_flag_success(mock_mark_as_processed):
    mock_mark_as_processed.return_value = True
    response = client.post("/ner-data/ner_mark_processed", json={"news_ids": [1, 2, 3]})
    assert response.status_code == 200
    assert response.json() == {"message": "News items marked as processed"}


@patch("app.routes.ner_data_routes.mark_news_as_processed")
def test_update_nonexistent_news_ids(mock_mark_as_processed):
    mock_mark_as_processed.return_value = False
    response = client.post("/ner-data/ner_mark_processed", json={"news_ids": [999]})
    print(response.content)
    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to mark news items as processed"}


@patch("app.routes.ner_data_routes.mark_news_as_processed")
def test_update_processed_flag_exception(mock_mark_as_processed):
    mock_mark_as_processed.side_effect = SQLAlchemyError("Database error")
    response = client.post("/ner-data/ner_mark_processed", json={"news_ids": [1, 2, 3]})
    assert response.status_code == 500
    assert "detail" in response.json()


@patch("app.routes.ner_data_routes.save_ner_results")
def test_save_ner_inference_results_success(mock_save_ner_results):
    mock_save_ner_results.return_value = True

    ner_results_data = {
        "ner_inference_results": [
            {
                "raw_news_id": 1,
                "headline_mentions": [],
                "body_text_mentions": [],
                "salient_entities_org": [],
                "salient_entities_set": [],
            }
        ]
    }

    response = client.post("/ner-data/ner_save_results", json=ner_results_data)
    assert response.status_code == 200
    assert response.json() == {"message": "NER results saved successfully"}


@patch("app.routes.ner_data_routes.save_ner_results")
def test_save_ner_inference_results_failure(mock_save_ner_results):
    mock_save_ner_results.return_value = False

    ner_results_data = {
        "ner_inference_results": [
            {
                "raw_news_id": 1,
                "headline_mentions": [],
                "body_text_mentions": [],
                "salient_entities_org": [],
                "salient_entities_set": [],
            }
        ]
    }
    response = client.post("/ner-data/ner_save_results", json=ner_results_data)
    print(response.content)
    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to save NER results"}
