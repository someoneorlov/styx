import os
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from ..models.extract_entities import extract_salient_entities


class Article(BaseModel):
    id: int
    title: str
    text: str


class ArticlesInput(BaseModel):
    articles: List[Article]


router = APIRouter()
API_URL = os.getenv("REL_API_URL", "http://rel:5555/api")


@router.post("/extract_entities")
async def perform_ner(input: ArticlesInput):
    try:
        results = extract_salient_entities(input.articles, API_URL)
        return results
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
