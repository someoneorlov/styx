import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# Import your script's functions (assuming correct import paths)
from styx_app.ner_service.src.ner_proceed_raw import (
    fetch_unprocessed_news,
    process_news_through_ner,
    save_ner_results,
    mark_news_as_processed,
    transform_ner_results_for_saving,
)

os.environ["NER_ENV"] = "test"

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


def prepare_ner_results_for_saving(**kwargs):
    """Airflow task to transform NER results for saving."""
    ti = kwargs["ti"]
    ner_results = ti.xcom_pull(task_ids="process_news_through_ner")
    transformed_results = transform_ner_results_for_saving(ner_results)
    ti.xcom_push(key="transformed_ner_results", value=transformed_results)


def save_transformed_ner_results(**kwargs):
    """Task to save transformed NER results, pulling from XCom."""
    ti = kwargs["ti"]
    transformed_ner_results = ti.xcom_pull(
        task_ids="prepare_ner_results_for_saving", key="transformed_ner_results"
    )
    save_ner_results(transformed_ner_results)


def mark_processed_news(**kwargs):
    """Task to mark news as processed, based on IDs from saved NER results."""
    ti = kwargs["ti"]
    processed_news_ids = ti.xcom_pull(
        task_ids="save_ner_results", key="processed_news_ids"
    )
    mark_news_as_processed(processed_news_ids)


with DAG(
    "ner_workflow",
    default_args=default_args,
    schedule_interval="15 * * * *",
    catchup=False,
) as dag:

    t1 = PythonOperator(
        task_id="fetch_unprocessed_news",
        python_callable=fetch_unprocessed_news,
        op_kwargs={"batch_size": 100},
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id="process_news_through_ner",
        python_callable=process_news_through_ner,
        provide_context=True,
    )

    prepare_results = PythonOperator(
        task_id="prepare_ner_results_for_saving",
        python_callable=prepare_ner_results_for_saving,
        provide_context=True,
    )

    t3 = PythonOperator(
        task_id="save_ner_results",
        python_callable=save_transformed_ner_results,
        provide_context=True,
    )

    t4 = PythonOperator(
        task_id="mark_news_as_processed",
        python_callable=mark_processed_news,
        provide_context=True,
    )

    t1 >> t2 >> prepare_results >> t3 >> t4
