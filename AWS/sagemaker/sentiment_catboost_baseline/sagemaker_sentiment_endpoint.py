from sagemaker.model import Model
from sagemaker.session import Session
from sagemaker.serverless import ServerlessInferenceConfig
from sagemaker.predictor import Predictor

sagemaker_session = Session()

role = (
    "arn:aws:iam::381491949871:role/service-role/"
    "AmazonSageMaker-ExecutionRole-20240514T182453"
)
model_name = "sentiment-catboost-model"
model_path = (
    "s3://styx-mlflow-artifacts"
    "/5/1ef7c69ad4ff414993e72360fd4fefb9/artifacts/styx-sentiment/catboost/model.tar.gz"
)
model_image = (
    "381491949871.dkr.ecr.us-east-1.amazonaws.com/sentiment-catboost-baseline:latest"
)

# Create a SageMaker model
model = Model(
    model_data=model_path,
    image_uri=model_image,
    role=role,
    name=model_name,
    sagemaker_session=sagemaker_session,
    predictor_cls=Predictor,  # Specify the custom predictor class
)

# Deploy the model
predictor = model.deploy(
    serverless_inference_config=ServerlessInferenceConfig(
        memory_size_in_mb=2048,
        max_concurrency=10,
    ),
    endpoint_name="sentiment-catboost-model-endpoint-15",
)

# Save the endpoint name for use in your Lambda function
endpoint_name = predictor.endpoint_name
print(f"Model deployed at endpoint: {endpoint_name}")
