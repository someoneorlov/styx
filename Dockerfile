# Use the Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements and the script into the container at /app
COPY requirements/req_load_new_data.txt /app/requirements/
COPY src/data/load_new_data.py /app/src/data/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements/req_load_new_data.txt

# (Optional) Run the script when the container launches
CMD ["python", "/app/src/data/load_new_data.py"]