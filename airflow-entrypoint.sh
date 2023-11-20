#!/bin/bash

# Ensure the script is running as root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Debugging as root user
python --version
which python
pip list
echo "Python path as root: $PYTHONPATH"

# Switch to airflow user for further debugging
su - airflow -c 'python --version'
su - airflow -c 'which python'
su - airflow -c 'pip list'
su - airflow -c 'echo "Python path as airflow user: $PYTHONPATH"'
su - airflow -c 'python -c "import airflow"' || echo "Airflow module not found as airflow user"


# # Create airflow user and group if they don't exist
# if ! id "airflow" &>/dev/null; then
#     groupadd -r airflow && useradd -r -g airflow airflow
# fi

# Check and create the Docker group if it doesn't exist
if [ ! -S /var/run/docker.sock ]; then
    echo 'Docker socket not found';
    exit 1;
fi
DOCKER_SOCKET_GROUP_ID=$(stat -c '%g' /var/run/docker.sock)
if ! getent group $DOCKER_SOCKET_GROUP_ID > /dev/null; then
    addgroup --gid $DOCKER_SOCKET_GROUP_ID dockersock
fi
usermod -aG dockersock airflow

# # Create and set permissions for logging directory
# mkdir -p /opt/airflow/logs
# chown -R airflow:airflow /opt/airflow/logs

# Run Airflow specific commands
if [ "$1" == "webserver" ]; then
    airflow db migrate
    # Debugging: Attempt to import Airflow
    python -c "import airflow" || { echo "Airflow module not found"; exit 1; }
    airflow users create \
        --username $AIRFLOW_USER \
        --firstname $AIRFLOW_FIRST_NAME \
        --lastname $AIRFLOW_LAST_NAME \
        --role $AIRFLOW_ROLE \
        --email $AIRFLOW_EMAIL \
        --password $AIRFLOW_PASS \
        || true
    exec airflow webserver
elif [ "$1" == "scheduler" ]; then
    airflow db migrate
    # Debugging: Attempt to import Airflow
    python -c "import airflow" || { echo "Airflow module not found"; exit 1; }
    exec airflow scheduler
else
    echo "Unknown role: $1"
    exit 1
fi