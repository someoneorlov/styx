# Use the Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements and the script into the container at /app
COPY requirements.txt /app/requirements/
COPY src/load_new_data.py /app/src/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements/requirements.txt

RUN apt-get update -y \
    && apt-get install -y python3-dev python3-pip build-essential \
    && apt-get install gcc -y \
    && apt-get install sudo -y \ 
    && apt-get clean

RUN adduser --disabled-password --gecos '' airflow

USER airflow