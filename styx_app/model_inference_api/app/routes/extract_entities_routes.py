import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Json
from typing import List, Dict

from ..models.extract_entities import extract_salient_entities


class ArticleInput(BaseModel):
    articles: Json


router = APIRouter()
API_URL = "http://rel:5555/api"


@router.post("/extract_entities")
async def perform_ner(input: ArticleInput):
    try:
        articles = json.loads(input.articles)
        # Validate that articles is a list of dicts
        if not isinstance(articles, List) or not all(
            isinstance(article, Dict) for article in articles
        ):
            raise ValueError("Invalid input format")

        results = extract_salient_entities(articles, API_URL)
        return results
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
