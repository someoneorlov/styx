# #!/bin/bash

# # Ensure the script is running as root
# if [ "$(id -u)" != "0" ]; then
#     echo "This script must be run as root" 1>&2
#     exit 1
# fi

# # Check for Docker socket
# if [ ! -S /var/run/docker.sock ]; then
#     echo 'Docker socket not found'
#     exit 1
# fi

# # Set Docker group GID to match the host's
# DOCKER_GROUP_NAME="docker"
# DOCKER_SOCKET_GROUP_ID=$(stat -c '%g' /var/run/docker.sock)

# # Check if the docker group exists, if not, create it
# if ! getent group $DOCKER_GROUP_NAME > /dev/null; then
#     groupadd -g $DOCKER_SOCKET_GROUP_ID $DOCKER_GROUP_NAME
# fi

# # Modify the Docker group GID and add the airflow user to it
# groupmod -g $DOCKER_SOCKET_GROUP_ID $DOCKER_GROUP_NAME
# usermod -aG $DOCKER_GROUP_NAME airflow

# # Call the airflow entrypoint script as 'airflow' user
# su - airflow -c "/airflow-entrypoint.sh $@"