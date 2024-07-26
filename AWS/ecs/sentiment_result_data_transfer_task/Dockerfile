FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y sshpass openssh-client autossh

COPY AWS/ecs/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./styx_packages /app/styx_packages
RUN pip install ./styx_packages

COPY AWS/ecs/sentiment_result_data_transfer_task/sentiment_result_data_transfer.py /app/sentiment_result_data_transfer.py

RUN mkdir /root/.ssh/

ENTRYPOINT ["python", "/app/sentiment_result_data_transfer.py"]