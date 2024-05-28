# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the inference code and model
COPY inference.py /app/inference.py
# COPY model.cbm /opt/ml/model/model.cbm

# Define environment variables
ENV MODEL_DIR=/opt/ml/model

# Expose the port the application runs on
EXPOSE 8080

# Use exec form of ENTRYPOINT
ENTRYPOINT ["python", "/app/inference.py"]
