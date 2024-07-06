import redis
from typing import List
from airflow.models import TaskInstance
from styx_packages.styx_logger.logging_config import setup_logger
from styx_packages.data_connector.api_connector import make_request


def get_task_logger(task_name, log_dir):
    logger_name = f"{__name__}.{task_name}"
    return setup_logger(logger_name, log_dir)


def fetch_unprocessed_news(
    batch_size: int = 5, log_dir: str = None, api_url=None, **kwargs
) -> None:
    """Fetch a batch of unprocessed news articles and push to XCom."""
    logger = get_task_logger("fetch_unprocessed_news", log_dir)
    logger.info(f"Attempting to fetch {batch_size} unprocessed news items...")
    logger.info(f"DATA_PROVIDER_API_URL: {api_url} | log_dir: {log_dir}")
    try:
        response = make_request(
            f"{api_url}/ner-data/ner_unprocessed_news",
            method="get",
            logger=logger,
            params={"batch_size": batch_size},
        )
        response.raise_for_status()
        news_items = response.json()["ner_news_items"]
        logger.info(f"Successfully fetched {len(news_items)} unprocessed news items.")
        # Explicitly push news items to XCom
        ti: TaskInstance = kwargs["ti"]  # TaskInstance is passed via kwargs in Airflow
        ti.xcom_push(key="news_items", value=news_items)
    except Exception as e:
        logger.error(f"Error fetching unprocessed news: {e}")
        raise


def process_news_through_ner(log_dir: str = None, api_url=None, **kwargs) -> List[dict]:
    """Send news items to the NER model for entity recognition."""
    logger = get_task_logger("process_news_through_ner", log_dir)
    ti = kwargs["ti"]
    news_items = ti.xcom_pull(task_ids="fetch_unprocessed_news", key="news_items")
    logger.info(f"MODEL_INFERENCE_API_URL: {api_url} | log_dir: {log_dir}")
    logger.info(f"Processing {len(news_items)} news items through NER...")

    if not news_items:
        logger.info("No news items to process.")
        return []
    try:
        articles_input = {"articles": news_items}
        response = make_request(
            f"{api_url}/ner-inf/extract_entities",
            method="post",
            logger=logger,
            json=articles_input,
        )
        response.raise_for_status()
        ner_results = response.json()["annotated_articles"]
        processed_ids = response.json()["processed_ids"]
        logger.info(f"Successfully processed {len(ner_results)} items through NER.")
        ti.xcom_push(key="ner_results", value=ner_results)
        ti.xcom_push(key="processed_news_ids", value=processed_ids)
        return ner_results
    except Exception as e:
        logger.error(f"Error processing news through NER: {e}")
        raise


def transform_ner_results_for_saving(ner_results, log_dir: str = None):
    """Transform NER results to match the expected format for saving."""
    logger = get_task_logger("transform_ner_results_for_saving", log_dir)
    logger.info("Transforming NER results for saving...")
    transformed_results = [
        {
            "model_config": {"from_attributes": True},
            "raw_news_id": result["raw_news_id"],
            "headline_mentions": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention[0],
                    "length": mention[1],
                    "mention_text": mention[2],
                    "linked_entity": mention[3],
                    "confidence_score": mention[4],
                    "link_probability": mention[5],
                    "entity_type": mention[6],
                }
                for mention in result["headline_mentions"]
            ],
            "body_text_mentions": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention[0],
                    "length": mention[1],
                    "mention_text": mention[2],
                    "linked_entity": mention[3],
                    "confidence_score": mention[4],
                    "link_probability": mention[5],
                    "entity_type": mention[6],
                }
                for mention in result["body_text_mentions"]
            ],
            "salient_entities_org": [
                {
                    "model_config": {"from_attributes": True},
                    "start": mention[0],
                    "length": mention[1],
                    "mention_text": mention[2],
                    "linked_entity": mention[3],
                    "confidence_score": mention[4],
                    "link_probability": mention[5],
                    "entity_type": mention[6],
                }
                for mention in result["salient_entities_org"]
            ],
            "salient_entities_set": result["salient_entities_set"],
        }
        for result in ner_results
    ]
    logger.info("Transformed NER results for saving successfully.")
    return transformed_results


def init_redis_client(
    redis_host: str = None, redis_port: int = None, redis_pass: str = None
):
    """
    Initialize a Redis client and test the connection.
    """
    try:
        # Initialize Redis client
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_pass,
            db=0,
            decode_responses=True,  # Automatically decode responses to Python strings
        )
        redis_client.ping()  # Test the connection
        return redis_client
    except Exception as e:
        logger = get_task_logger("save_ner_results_to_redis", None)
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def save_ner_results_to_redis(
    ner_results,
    log_dir: str = None,
    redis_host: str = None,
    redis_port: int = None,
    redis_pass: str = None,
    **kwargs,
):
    logger = get_task_logger("save_ner_results_to_redis", log_dir)
    logger.info("Saving NER results to Redis...")

    redis_client = init_redis_client(
        redis_host=redis_host, redis_port=redis_port, redis_pass=redis_pass
    )
    if redis_client is None:
        logger.error("Redis client initialization failed, aborting save operation.")
        return

    # Iterate over each result
    for result in ner_results:
        # Process each mention in headline_mentions and body_text_mentions
        for mention_list in [result["headline_mentions"], result["body_text_mentions"]]:
            for mention in mention_list:
                # Extracting mention and linked entity
                mention_text = mention[2]
                linked_entity = mention[3]

                # Prepare keys in original, lowercase, and uppercase
                keys = [mention_text, mention_text.lower(), mention_text.upper()]

                # Attempt to save each key with the linked entity value to Redis
                try:
                    for key in keys:
                        redis_key = f"ner_mention:{key}"
                        redis_client.set(redis_key, linked_entity)
                        logger.info(f"Saved {redis_key} to Redis")
                except Exception as e:
                    logger.error(f"Failed to save {redis_key} to Redis: {e}")


def save_ner_results(
    ner_results: List[dict], log_dir: str = None, api_url=None, **context
) -> List[str]:
    """Save NER results to the database and return processed news IDs."""
    logger = get_task_logger("save_ner_results", log_dir)
    processed_ids = [result["raw_news_id"] for result in ner_results]
    context["ti"].xcom_push(key="processed_news_ids", value=processed_ids)

    if len(processed_ids) == 0:
        logger.info("No NER results to save.")
        return processed_ids

    try:
        logger.info(f"Saving {len(processed_ids)} NER results...")
        response = make_request(
            f"{api_url}/ner-data/ner_save_results",
            method="post",
            logger=logger,
            json={"ner_inference_results": ner_results},
        )
        response.raise_for_status()
        logger.info(f"NER results saved successfully for IDs: {processed_ids}")
        return processed_ids
    except Exception as e:
        logger.error(f"Failed to save NER results: {e}")
        raise


def mark_news_as_processed(log_dir: str = None, api_url=None, **context):
    """Mark news items as processed in the database."""
    logger = get_task_logger("mark_news_as_processed", log_dir)
    news_ids = context["ti"].xcom_pull(
        task_ids="process_news_through_ner", key="processed_news_ids"
    )
    if news_ids is None or len(news_ids) == 0:
        logger.info("No news items to mark as processed.")
        return

    try:
        logger.info(f"Marking {len(news_ids)} news items as processed...")
        response = make_request(
            f"{api_url}/ner-data/ner_mark_processed",
            method="post",
            logger=logger,
            json={"news_ids": news_ids},
        )
        response.raise_for_status()
        logger.info(f"{len(news_ids)} news items marked as processed successfully.")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to mark news items as processed: {e}")
        raise
