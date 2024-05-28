import boto3
import json

runtime = boto3.client("runtime.sagemaker")
ENDPOINT_NAME = "sentiment-catboost-model-endpoint-15"


def call_sagemaker_endpoint(payload):
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload),
    )
    result = response["Body"].read().decode("utf-8")
    return result


# Example payload
payload = {"text": ["Example text for prediction"]}
result = call_sagemaker_endpoint(payload)
print(result)
