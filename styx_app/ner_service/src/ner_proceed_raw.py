import os
import requests
import backoff
from typing import List
from ...logging_config import setup_logger

# Determine the environment and set log directory accordingly
env = os.getenv("NER_ENV", "test")  # Default to 'prod' if not set
log_dir = "/opt/airflow/styx/logs_test" if env == "test" else "/opt/airflow/styx/logs"

# Now use this `log_dir` when setting up your logger
logger = setup_logger(__name__, log_dir)

DATA_PROVIDER_API_URL = os.getenv("DATA_PROVIDER_API_URL_TEST")
MODEL_INFERENCE_API_URL = os.getenv("MODEL_INFERENCE_API_URL_PROD")


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
    logger.info(f"Attempting to fetch {batch_size} unprocessed news items...")
    try:
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/ner-data/ner_unprocessed_news",
            method="get",
            params={"batch_size": batch_size},
        )
        response.raise_for_status()
        news_items = response.json()["ner_news_items"]
        logger.info(f"Successfully fetched {len(news_items)} unprocessed news items.")
        return news_items
    except Exception as e:
        logger.error(f"Error fetching unprocessed news: {e}")
        raise


def process_news_through_ner(**kwargs):
    """Send news items to the NER model for entity recognition."""
    ti = kwargs["ti"]
    news_items = ti.xcom_pull(task_ids="fetch_unprocessed_news")
    logger.info(f"Processing {len(news_items)} news items through NER...")
    if not news_items:
        logger.info("No news items to process.")
        return []
    try:
        articles_input = {"articles": news_items}
        response = make_request(
            f"{MODEL_INFERENCE_API_URL}/ner-inf/extract_entities",
            method="post",
            json=articles_input,
        )
        response.raise_for_status()
        ner_results = response.json()
        logger.info(f"Successfully processed {len(ner_results)} items through NER.")
        return ner_results
    except Exception as e:
        logger.error(f"Error processing news through NER: {e}")
        raise


def save_ner_results(ner_results: List[dict], **context):
    """Save NER results to the database and return processed news IDs."""
    logger = setup_logger("save_ner_results")
    try:
        logger.info("Saving NER results...")
        processed_ids = [result["raw_news_id"] for result in ner_results]
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/ner-data/ner_save_results",
            method="post",
            json={"ner_inference_results": ner_results},
        )
        response.raise_for_status()
        context["ti"].xcom_push(key="processed_news_ids", value=processed_ids)
        logger.info(f"NER results saved successfully for IDs: {processed_ids}")
        return processed_ids
    except Exception as e:
        logger.error(f"Failed to save NER results: {e}")
        raise


def mark_news_as_processed(**context):
    """Mark news items as processed in the database."""
    logger = setup_logger("mark_news_as_processed")
    news_ids = context["ti"].xcom_pull(
        task_ids="save_ner_results", key="processed_news_ids"
    )
    logger.info(f"Marking {len(news_ids)} news items as processed...")
    try:
        response = make_request(
            f"{DATA_PROVIDER_API_URL}/ner-data/ner_mark_processed",
            method="post",
            json={"news_ids": news_ids},
        )
        response.raise_for_status()
        logger.info("News items marked as processed successfully.")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to mark news items as processed: {e}")
        raise
