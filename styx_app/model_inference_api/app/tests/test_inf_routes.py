import json
import requests

API_BASE_URL = "http://localhost:8001"


def load_test_data():
    with open("ner_test_data.json") as f:
        return json.load(f)


def test_ner_extraction():
    test_data = load_test_data()
    response = requests.post(
        f"{API_BASE_URL}/ner-inf/extract_entities",
        json={"articles": test_data["sample_articles"]},
    )
    # Get the JSON response
    data = response.json()
    print(data)

    # Assertions
    assert response.status_code == 200
    assert isinstance(data, list)
    assert isinstance(data[0]["raw_news_id"], int)
    assert len(data) == 2
    assert len(data[0]) == 5
    assert len(data[0]["body_text_mentions"]) == 6
    assert len(data[0]["salient_entities_org"]) == 0
    assert data[0]["salient_entities_set"] == ["None"]
    assert data[1]["salient_entities_set"] == ["United_States_Coast_Guard"]


def test_ner_with_invalid_data():
    response = requests.post(
        f"{API_BASE_URL}/ner-inf/extract_entities",
        json={"articles": "invalid data format"},  # intentionally incorrect format
    )
    assert (
        response.status_code == 422
    )  # Assuming 422 Unprocessable Entity for invalid data