import os
import sys
import pandas as pd
from catboost import CatBoostClassifier
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Define request and response models
class TextRequest(BaseModel):
    text: List[str]


class PredictionResponse(BaseModel):
    predictions: List[float]


# Initialize the FastAPI application
app = FastAPI()

# Load the model
model_path = os.path.join(os.getenv("MODEL_DIR", "/opt/ml/model"), "model.cbm")
model = CatBoostClassifier()
try:
    model.load_model(model_path)
    logger.info(f"Model loaded successfully from {model_path}")
except Exception as e:
    logger.error(f"Failed to load model from {model_path}: {str(e)}")


@app.get("/ping")
def ping():
    # Check if the model is loaded correctly
    health = model is not None
    status = 200 if health else 404
    logger.info(f"Health check status: {status}")
    return JSONResponse(
        content={"status": "Healthy" if health else "Unhealthy"}, status_code=status
    )


@app.post("/invocations", response_model=PredictionResponse)
def invoke(request: TextRequest):
    try:
        # Extract the feature column from the input
        input_data = pd.DataFrame(request.text, columns=["text"])
        predictions = model.predict_proba(input_data)[
            :, 1
        ]  # Assuming binary classification
        logger.info(f"Predictions: {predictions.tolist()}")
        return PredictionResponse(predictions=predictions.tolist())
    except Exception as e:
        logger.error(f"Failed to make predictions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to make predictions")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        logger.error("Unknown argument provided")
