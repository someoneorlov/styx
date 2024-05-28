import boto3
import json

# SageMaker runtime client
runtime = boto3.client("runtime.sagemaker")

# Define the endpoint name
endpoint_name = "sentiment-catboost-model-endpoint-14"

# Example input data
input_data = {"text": ["Example text for predict"]}

# Invoke the endpoint
response = runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    ContentType="application/json",
    Body=json.dumps(input_data),
)

# Read and decode the response
result = json.loads(response["Body"].read().decode())
print(result)
