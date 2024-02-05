from typing import List
from fastapi import APIRouter, HTTPException
from ..models import NERNewsBatch, NERInferenceResultBatch
from ..services.ner_data_services.py import (
    get_unprocessed_news,
    mark_news_as_processed,
    save_ner_results,
)

router = APIRouter()


@router.get("/ner_unprocessed_news", response_model=NERNewsBatch)
async def fetch_unprocessed_news():
    try:
        unprocessed_news = get_unprocessed_news()
        return unprocessed_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner_mark_processed")
async def update_processed_flag(news_ids: List[int]):
    try:
        mark_news_as_processed(news_ids)
        return {"message": "News items marked as processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner_save_results")
async def save_ner_inference_results(ner_results: NERInferenceResultBatch):
    try:
        save_ner_results(ner_results)
        return {"message": "NER results saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
