import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from docker.types import Mount


default_args = {
    "owner": "airflow",
    "description": "Use of the DockerOperator",
    "depend_on_past": False,
    "start_date": datetime(2021, 5, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def env_var():
    print("SCRAPER_URL:", os.getenv("SCRAPER_URL"))
    print("DB_NAME:", os.getenv("DB_NAME"))


with DAG(
    "docker_operator_dag",
    default_args=default_args,
    schedule_interval="5 * * * *",
    catchup=False,
) as dag:
    start_dag = DummyOperator(task_id="start_dag")

    end_dag = DummyOperator(task_id="end_dag")

    t1 = BashOperator(task_id="print_current_date", bash_command="date")

    t2 = DockerOperator(
        task_id="docker_command_sleep",
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
            "echo test_str $DB_NAME $DB_USER $DB_PASS; python /app/src/data/load_new_data.py ${SCRAPER_URL}",
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

    # t3 = DockerOperator(
    #     task_id="docker_command_hello",
    #     image="styx_scraper_img",
    #     container_name="styx_scraper_cont_2",
    #     api_version="auto",
    #     auto_remove=True,
    #     environment={
    #         "SCRAPER_URL": os.getenv("SCRAPER_URL", "default_scraper_url"),
    #     },
    #     command="python /app/src/data/load_new_data.py ${SCRAPER_URL}",
    #     docker_url="unix://var/run/docker.sock",
    #     network_mode="bridge",
    #     mount_tmp_dir=False,
    #     mounts=[
    #         Mount(
    #             source="/home/ec2-user/projects/airflow_test/logs",
    #             target="/var/log",
    #             type="bind",
    #         )
    #     ],
    # )

    t4 = BashOperator(task_id="print_hello", bash_command='echo "hello world"')

    t5 = PythonOperator(
        task_id="test_env_var",
        python_callable=env_var,
    )

    t2

    t5
    # start_dag >> t1

    # t1 >> t2 >> t4
    # t1 >> t3 >> t4

    # t4 >> end_dag
