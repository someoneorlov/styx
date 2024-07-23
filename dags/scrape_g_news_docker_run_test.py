import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount


default_args = {
    "owner": "airflow",
    "description": "Run scraping news container",
    "depend_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

env = "test"
# Load the common .env file
load_dotenv("/opt/airflow/styx/.env")

# Load the environment-specific .env file
load_dotenv(f"/opt/airflow/styx/.env.{env}")

LOG_DIR = os.getenv("LOG_DIR")

with DAG(
    f"scrape_google_news_{env}",
    default_args=default_args,
    schedule_interval="15 * * * *",
    catchup=False,
) as dag:

    t1 = DockerOperator(
        task_id="run_scrap_container",
        image="styx_scraper_img",
        container_name=f"styx_scraper_cont_{env}",
        api_version="auto",
        auto_remove=True,
        environment={
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT_INNER"),
            "DB_NAME": os.getenv("POSTGRES_DB"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASS": os.getenv("DB_PASS"),
            "SCRAPER_URL": os.getenv("SCRAPER_URL"),
        },
        command=[
            "/bin/sh",
            "-c",
            "python /app/src/load_new_data.py ${SCRAPER_URL}",
        ],
        docker_url="unix://var/run/docker.sock",
        network_mode="styx_default",
        mount_tmp_dir=False,
        mounts=[
            Mount(
                source=LOG_DIR,
                target="/var/log",
                type="bind",
            )
        ],
    )

t1
