import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'scrape_google_news_docker_run',
    default_args=default_args,
    schedule_interval=timedelta(hours=1),  # Adjust the interval as needed
) as dag:

    run_container = DockerOperator(
        task_id='scrape_google_news',
        image='styx_scraper:latest',  # Replace with your actual image name
        api_version='auto',
        auto_remove=True,
        network_mode='bridge',  # or your custom network if defined
        docker_url='unix://var/run/docker.sock',  # Docker daemon socket
        mount_tmp_dir=False,
        # environment={
        #     'DB_HOST': 'db',
        #     'DB_NAME': os.environ.get('DB_NAME', 'default_db_name'),
        #     'DB_USER': os.environ.get('DB_USER', 'default_db_user'),
        #     'DB_PASS': os.environ.get('DB_PASS', 'default_db_password'),
        #     'SCRAPER_URL': os.environ.get('SCRAPER_URL', 'default_scraper_url')
        # },
        # mounts=[
        #     Mount(
        #         source='/home/ec2-user/projects/styx/logs',
        #         target='/var/log',
        #         type='bind'
        #     )
        # ],
        command='echo "this is a test message shown from within the container"',
        # command="python /app/src/data/load_new_data.py '${SCRAPER_URL}'"
    )

#    'DB_HOST': os.environ.get('DB_HOST', 'default_db_host'),