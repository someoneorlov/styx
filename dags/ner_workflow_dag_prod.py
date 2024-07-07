import os
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

from styx_app.ner_service.src.ner_proceed_raw import (
    fetch_unprocessed_news,
    process_news_through_ner,
    save_ner_results,
    mark_news_as_processed,
    transform_ner_results_for_saving,
    save_ner_results_to_redis,
)

env = "prod"
# Load the common .env file
load_dotenv("/opt/airflow/styx/.env")

# Load the environment-specific .env file
load_dotenv(f"/opt/airflow/styx/.env.{env}")

DATA_PROVIDER_API_URL = os.getenv("DATA_PROVIDER_API_URL")
MODEL_INFERENCE_API_URL = os.getenv("MODEL_INFERENCE_API_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT_INNER"))
REDIS_PASS = os.getenv("REDIS_PASS")

log_dir = f"/opt/airflow/styx/logs_{env}"

default_args = {
    "owner": "airflow",
    "description": "Run NER news processing",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def prepare_ner_results_for_saving(log_dir: str = None, **kwargs):
    """Airflow task to transform NER results for saving."""
    ti = kwargs["ti"]
    ner_results = ti.xcom_pull(task_ids="process_news_through_ner")
    transformed_results = transform_ner_results_for_saving(ner_results, log_dir)
    ti.xcom_push(key="transformed_ner_results", value=transformed_results)


def save_to_redis_callable(
    log_dir: str = None,
    redis_host: str = None,
    redis_port: int = None,
    redis_pass: str = None,
    **kwargs,
):
    """Wrapper callable for the Airflow task to save NER results to Redis."""
    ti = kwargs["ti"]
    # Pull NER results directly from `process_news_through_ner` task
    ner_results = ti.xcom_pull(task_ids="process_news_through_ner")
    # Call the function to save results to Redis
    save_ner_results_to_redis(
        ner_results, log_dir, redis_host, redis_port, redis_pass, **kwargs
    )


def save_transformed_ner_results(log_dir: str = None, api_url=None, **kwargs):
    """Task to save transformed NER results, pulling from XCom."""
    ti = kwargs["ti"]
    transformed_ner_results = ti.xcom_pull(
        task_ids="prepare_ner_results_for_saving", key="transformed_ner_results"
    )
    save_ner_results(
        ner_results=transformed_ner_results, log_dir=log_dir, api_url=api_url, **kwargs
    )


def mark_processed_news(log_dir: str = None, api_url=None, **kwargs):
    """Task to mark news as processed, based on IDs from saved NER results."""
    ti = kwargs["ti"]
    processed_news_ids = ti.xcom_pull(
        task_ids="save_ner_results", key="processed_news_ids"
    )
    context = kwargs  # Copy existing context
    context["news_ids"] = processed_news_ids  # Add 'news_ids' to context

    # Now pass the entire context as keyword arguments
    mark_news_as_processed(log_dir=log_dir, api_url=api_url, **context)


with DAG(
    f"ner_workflow_{env}",
    default_args=default_args,
    schedule_interval="45 * * * *",
    catchup=False,
) as dag:

    t1 = PythonOperator(
        task_id="fetch_unprocessed_news",
        python_callable=fetch_unprocessed_news,
        op_kwargs={
            "batch_size": 5,
            "log_dir": log_dir,
            "api_url": DATA_PROVIDER_API_URL,
        },
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id="process_news_through_ner",
        python_callable=process_news_through_ner,
        op_kwargs={"log_dir": log_dir, "api_url": MODEL_INFERENCE_API_URL},
        provide_context=True,
    )

    prepare_results = PythonOperator(
        task_id="prepare_ner_results_for_saving",
        python_callable=prepare_ner_results_for_saving,
        op_kwargs={"log_dir": log_dir},
        provide_context=True,
    )

    save_to_redis = PythonOperator(
        task_id="save_ner_results_to_redis",
        python_callable=save_to_redis_callable,
        op_kwargs={
            "log_dir": log_dir,
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
            "redis_pass": REDIS_PASS,
        },
        provide_context=True,
    )

    t3 = PythonOperator(
        task_id="save_ner_results",
        python_callable=save_transformed_ner_results,
        op_kwargs={"log_dir": log_dir, "api_url": DATA_PROVIDER_API_URL},
        provide_context=True,
    )

    t4 = PythonOperator(
        task_id="mark_news_as_processed",
        python_callable=mark_processed_news,
        op_kwargs={"log_dir": log_dir, "api_url": DATA_PROVIDER_API_URL},
        provide_context=True,
    )

    t1 >> t2 >> [prepare_results, save_to_redis]
    prepare_results >> t3 >> t4
