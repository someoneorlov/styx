import os
import base64
import subprocess
import time
import requests

from styx_packages.db_connector.db_connector import get_engine, session_factory
from styx_packages.db_connector.db_models import AWSRawNewsArticle


# Decode SSH keys and config from environment variables
ssh_private_key = base64.b64decode(os.environ["SSH_PRIVATE_KEY"]).decode("utf-8")
ssh_public_key = base64.b64decode(os.environ["SSH_PUBLIC_KEY"]).decode("utf-8")
ssh_config = base64.b64decode(os.environ["SSH_CONFIG"]).decode("utf-8")

# AWS RDS connection parameters
AWS_DB_HOST = os.getenv("AWS_DB_HOST")
AWS_DB_PORT = os.getenv("AWS_DB_PORT")
AWS_DB_NAME = os.getenv("AWS_DB_NAME")
AWS_DB_USER = os.getenv("AWS_DB_USER")
AWS_DB_PASS = os.getenv("AWS_DB_PASS")

# Write the SSH private key
with open("/root/.ssh/id_aws_ecs_task", "w") as f:
    f.write(ssh_private_key)
    os.chmod("/root/.ssh/id_aws_ecs_task", 0o600)

# Write the SSH public key
with open("/root/.ssh/id_aws_ecs_task.pub", "w") as f:
    f.write(ssh_public_key)
    os.chmod("/root/.ssh/id_aws_ecs_task.pub", 0o600)

# Write the SSH config
with open("/root/.ssh/config", "w") as f:
    f.write(ssh_config)
    os.chmod("/root/.ssh/config", 0o600)

# Create SSH tunnel using autossh
autossh_command = [
    "autossh",
    "-M",
    "0",
    "-f",
    "-N",
    "-L",
    "8004:127.0.0.1:8004",
    "ec2-user@194.242.122.57",
]
subprocess.Popen(autossh_command)
time.sleep(3)


# Function to fetch data from data_provider_api
def fetch_data():
    try:
        response = requests.get(
            "http://localhost:8004/aws-data/aws_unprocessed_news?batch_size=2"
        )
        if response.status_code == 200:
            return response.json()["articles"]
        else:
            print(f"Requests failed with status code: {response.status_code}")
            return None
    except requests.ConnectionError as e:
        print(f"Requests failed to connect: {e}")
        return None


# Function to connect to AWS RDS and perform read/write operations
def test_rds_operations(data):
    try:
        # Get the database engine and session factory
        engine = get_engine(
            host=AWS_DB_HOST,
            port=AWS_DB_PORT,
            db=AWS_DB_NAME,
            user=AWS_DB_USER,
            password=AWS_DB_PASS,
        )
        SessionLocal = session_factory(engine)

        # Create the session
        db = SessionLocal()

        # Insert data into aws_raw_news_articles table
        successfully_written_ids = []
        for item in data:
            raw_news_article = AWSRawNewsArticle(
                raw_news_article_id=item["id"],
                title=item["title"],
                text=item["text"],
                publish_date=item.get("publish_date"),
                publish_date_source=item.get("publish_date_source"),
                authors=item.get("authors"),
                media_title=item.get("media_title"),
            )
            db.add(raw_news_article)
            successfully_written_ids.append(item["id"])
        db.commit()

        # Close the session
        db.close()

        return successfully_written_ids
    except Exception as e:
        print(f"Error: {e}")
        return []


# Function to mark news as processed
def mark_news_as_processed(news_ids):
    try:
        response = requests.post(
            "http://localhost:8004/aws-data/aws_mark_processed",
            json={"news_ids": news_ids},
        )
        if response.status_code == 200:
            print("Successfully marked news as processed.")
        else:
            print(
                f"Failed to mark news as processed with status code: {response.status_code}"
            )
    except requests.ConnectionError as e:
        print(f"Failed to connect to mark news as processed: {e}")


# Main function
if __name__ == "__main__":
    data = fetch_data()
    if data:
        successfully_written_ids = test_rds_operations(data)
        if successfully_written_ids:
            mark_news_as_processed(successfully_written_ids)
