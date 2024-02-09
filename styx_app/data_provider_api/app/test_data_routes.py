from unittest.mock import patch
from fastapi.testclient import TestClient
from styx_app.data_provider_api.app.main import app
from .models import NERNewsItem, NERNewsBatch
from sqlalchemy.exc import SQLAlchemyError
from .dependencies import get_db_session
from .models import NewsIDs

client = TestClient(app)


# Success Path Testing
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.get_unprocessed_news")
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
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_error(mock_get_unprocessed_news):
    mock_get_unprocessed_news.side_effect = Exception("Database error")

    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Database error" in response.json()["detail"]


# Edge Cases
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.get_unprocessed_news")
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
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.get_unprocessed_news")
def test_fetch_unprocessed_news_no_content(mock_get_unprocessed_news):
    mock_get_unprocessed_news.return_value = NERNewsBatch(ner_news_items=[])

    response = client.get("/ner-data/ner_unprocessed_news?batch_size=10")
    assert response.status_code == 200
    assert "ner_news_items" in response.json()
    assert len(response.json()["ner_news_items"]) == 0


@patch("styx_app.data_provider_api.app.dependencies.get_db_session")
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.mark_news_as_processed")
def test_update_processed_flag_success(mock_mark_as_processed, get_db_sessio):
    mock_mark_as_processed.return_value = True
    response = client.post("/ner-data/ner_mark_processed", json={"news_ids": [1, 2, 3]})
    assert response.status_code == 200
    assert response.json() == {"message": "News items marked as processed"}


@patch("styx_app.data_provider_api.app.dependencies.get_db_session")
@patch("styx_app.data_provider_api.app.routes.ner_data_routes.mark_news_as_processed")
def test_update_nonexistent_news_ids(mock_mark_as_processed, get_db_sessio):
    mock_mark_as_processed.return_value = False
    response = client.post("/ner-data/ner_mark_processed", json={"news_ids": [999]})
    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to mark news items as processed"}


# @patch("path.to.get_db_session")
# @patch("styx_app.data_provider_api.app.routes.ner_data_routes.mark_news_as_processed")
# def test_update_processed_flag_exception(mock_mark_as_processed, mock_db_session):
#     mock_mark_as_processed.side_effect = SQLAlchemyError("Database error")
#     response = client.post("/ner_mark_processed", json={"news_ids": [1, 2, 3]})
#     assert response.status_code == 500
#     assert "detail" in response.json()
