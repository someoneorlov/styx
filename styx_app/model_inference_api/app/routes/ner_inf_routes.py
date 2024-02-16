import os
import json
import requests

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from ..services.extract_entities import extract_salient_entities
from styx_packages.styx_logger.logging_config import setup_logger


class Article(BaseModel):
    id: int
    title: str
    text: str


class ArticlesInput(BaseModel):
    articles: List[Article]


router = APIRouter()
API_URL = os.getenv("REL_API_URL", "http://rel:5555/api")
logger = setup_logger(__name__)


@router.get("/health")
async def health_check():
    try:
        # Check the REL API status
        rel_status_response = requests.get(f"{API_URL}/")
        rel_status = rel_status_response.json()

        if rel_status_response.status_code == 200 and rel_status.get("message") == "up":
            logger.info(
                "Health check successful for both Model Inference API and REL API."
            )
            return {
                "status": "ok",
                "message": "Model Inference API and REL API are up and running",
                "rel_api_status": rel_status,
            }
        else:
            logger.error("Health check failed: REL API is down.")
            raise HTTPException(status_code=500, detail="REL API is down")
    except requests.RequestException as e:
        logger.error(f"Health check failed: Failed to connect to REL API: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to REL API: {str(e)}"
        )


@router.post("/extract_entities")
async def perform_ner(input: ArticlesInput):
    try:
        results = extract_salient_entities(input.articles, API_URL)
        logger.info(f"Entity extraction successful for {len(input.articles)} articles.")
        return results
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Entity extraction failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
