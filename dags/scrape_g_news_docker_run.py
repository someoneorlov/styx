import os
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


with DAG(
    "scrape_google_news_docker_run",
    default_args=default_args,
    schedule_interval="5 * * * *",
    catchup=False,
) as dag:

    t1 = DockerOperator(
        task_id="run_scrap_container",
        image="styx_scraper_img",
        container_name="styx_scraper_cont",
        api_version="auto",
        auto_remove=True,
        environment={
            "DB_HOST": "db",
            "DB_NAME": os.getenv("DB_NAME", "default_db_name_inside"),
            "DB_USER": os.getenv("DB_USER", "default_db_user_inside"),
            "DB_PASS": os.getenv("DB_PASS", "default_db_password_inside"),
            "SCRAPER_URL": os.getenv("SCRAPER_URL", "default_scraper_url_inside"),
        },
        command=[
            "/bin/sh",
            "-c",
            "python /app/src/data/load_new_data.py ${SCRAPER_URL}",
        ],
        docker_url="unix://var/run/docker.sock",
        network_mode="styx_default",
        mount_tmp_dir=False,
        mounts=[
            Mount(
                source="/home/ec2-user/projects/styx/logs",
                target="/var/log",
                type="bind",
            )
        ],
    )

    t1
