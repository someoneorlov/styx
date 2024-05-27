import sagemaker
from sagemaker.transformer import Transformer

# Initialize the SageMaker session
sagemaker_session = sagemaker.Session()

role = "arn:aws:iam::381491949871:role/service-role/AmazonSageMaker-ExecutionRole-20240514T182453"
model_name = "sentiment-catboost-model"
model_path = "s3://styx-mlflow-artifacts/5/1ef7c69ad4ff414993e72360fd4fefb9/artifacts/styx-sentiment/catboost/model.tar.gz"
model_image = (
    "381491949871.dkr.ecr.us-east-1.amazonaws.com/sentiment-catboost-baseline:latest"
)
input_data_path = "s3://styx-nlp-artifacts/lambda_workflow_data/test/sentiment_workflow/preprocessed_data/preprocessed_data_batch.csv"
output_data_path = "s3://styx-nlp-artifacts/lambda_workflow_data/test/sentiment_workflow/preprocessed_data/"

# Create a SageMaker model
model = sagemaker.model.Model(
    model_data=model_path,
    image_uri=model_image,
    role=role,
    sagemaker_session=sagemaker_session,
)

# Deploy the model
model.deploy(initial_instance_count=1, instance_type="ml.t3.medium")

# Define the transformer
transformer = Transformer(
    model_name=model_name,
    instance_count=1,
    instance_type="ml.t3.medium",
    strategy="SingleRecord",
    assemble_with="Line",
    output_path=output_data_path,
    accept="text/csv",
    max_concurrent_transforms=4,
    max_payload=1,
    env={
        "SAGEMAKER_INFERENCE_OUTPUT": "predicted_label",
        "SAGEMAKER_INFERENCE_INPUT": "text/csv",
    },
)

# Start the transform job
transformer.transform(
    data=input_data_path,
    content_type="text/csv",
    split_type="Line",
    input_filter="$[2]",  # Adjust this based on your input data
    join_source="Input",
    output_filter="$[0,1,-1]",  # Adjust this based on your output data
)

# Wait for the transform job to complete
transformer.wait()
