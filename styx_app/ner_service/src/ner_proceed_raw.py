import os
import requests
import backoff
from typing import List

DATA_PROVIDER_API_URL = os.getenv("DATA_PROVIDER_API_URL", "http://localhost/ner-data")
MODEL_INFERENCE_API_URL = os.getenv(
    "MODEL_INFERENCE_API_URL", "http://localhost/ner-inf"
)


def transform_ner_results_for_saving(ner_results):
    """Transform NER results to match the expected format for saving."""
    transformed_results = [
        {
            "model_config": {"from_attributes": True},
            "raw_news_id": result["raw_news_id"],
            "headline_mentions": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention["start"],
                    "length": mention["length"],
                    "mention_text": mention["mention_text"],
                    "linked_entity": mention["linked_entity"],
                    "confidence_score": mention["confidence_score"],
                    "link_probability": mention["link_probability"],
                    "entity_type": mention["entity_type"],
                }
                for mention in result["headline_mentions"]
            ],
            "body_text_mentions": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention["start"],
                    "length": mention["length"],
                    "mention_text": mention["mention_text"],
                    "linked_entity": mention["linked_entity"],
                    "confidence_score": mention["confidence_score"],
                    "link_probability": mention["link_probability"],
                    "entity_type": mention["entity_type"],
                }
                for mention in result["body_text_mentions"]
            ],
            "salient_entities_org": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention["start"],
                    "length": mention["length"],
                    "mention_text": mention["mention_text"],
                    "linked_entity": mention["linked_entity"],
                    "confidence_score": mention["confidence_score"],
                    "link_probability": mention["link_probability"],
                    "entity_type": mention["entity_type"],
                }
                for mention in result["salient_entities_org"]
            ],
            "salient_entities_set": result["salient_entities_set"],
        }
        for result in ner_results
    ]
    return {"ner_inference_results": transformed_results}


# Define a backoff on HTTP error status codes 500-599
@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=8,
    giveup=lambda e: e.response is not None and e.response.status_code < 500,
)
def make_request(url, method="get", **kwargs):
    """
    A generic request function that includes retry logic.
    """
    with requests.Session() as session:
        if method.lower() == "get":
            response = session.get(url, **kwargs)
        elif method.lower() == "post":
            response = session.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response


def fetch_unprocessed_news(batch_size: int = 100) -> List[dict]:
    """Fetch a batch of unprocessed news articles."""
    response = make_request(
        f"{DATA_PROVIDER_API_URL}/ner_unprocessed_news",
        method="get",
        params={"batch_size": batch_size},
    )
    response.raise_for_status()  # This will raise an exception for HTTP error responses
    return response.json()["ner_news_items"]


def process_news_through_ner(**kwargs):
    """Send news items to the NER model for entity recognition."""
    ti = kwargs["ti"]
    news_items = ti.xcom_pull(task_ids="fetch_unprocessed_news")  # Pull data from XCom
    if not news_items:
        return []  # Early exit if no news items are fetched

    articles_input = {"articles": news_items}
    response = make_request(
        f"{MODEL_INFERENCE_API_URL}/extract_entities",
        method="post",
        json=articles_input,
    )
    response.raise_for_status()
    return response.json()


def save_ner_results(ner_results: List[dict], **context):
    """Save NER results to the database and return processed news IDs."""
    processed_ids = [result["raw_news_id"] for result in ner_results]
    response = make_request(
        f"{DATA_PROVIDER_API_URL}/ner_save_results",
        method="post",
        json={"ner_inference_results": ner_results},
    )
    response.raise_for_status()
    # Push the processed_ids to XCom
    context["ti"].xcom_push(key="processed_news_ids", value=processed_ids)
    return processed_ids


def mark_news_as_processed(**context):
    """Mark news items as processed in the database."""
    news_ids = context["ti"].xcom_pull(
        task_ids="save_ner_results", key="processed_news_ids"
    )
    response = make_request(
        f"{DATA_PROVIDER_API_URL}/ner_mark_processed",
        method="post",
        json={"news_ids": news_ids},
    )
    response.raise_for_status()
    return response.json()


# def main():
#     try:
#         # Step 1: Fetch Unprocessed News
#         unprocessed_news = fetch_unprocessed_news()
#         if not unprocessed_news:
#             print("No unprocessed news found.")
#             return

#         # Step 2: Process News Through NER
#         ner_results = process_news_through_ner(unprocessed_news)

#         # Step 3: Save NER Results
#         save_results_response = save_ner_results(ner_results)
#         print(save_results_response)

#         # Step 4: Mark News as Processed
#         news_ids = [item["id"] for item in unprocessed_news]
#         mark_processed_response = mark_news_as_processed(news_ids)
#         print(mark_processed_response)

#     except requests.exceptions.HTTPError as e:
#         print(f"HTTPError occurred: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")


# if __name__ == "__main__":
#     main()
