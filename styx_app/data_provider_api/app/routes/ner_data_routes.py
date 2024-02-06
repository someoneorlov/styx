from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models import NERNewsBatch, NERInferenceResultBatch, NewsIDs
from ..dependencies import get_db_session
from ..services.ner_data_services import (
    get_unprocessed_news,
    mark_news_as_processed,
    save_ner_results,
)

router = APIRouter()


@router.get("/ner_unprocessed_news", response_model=NERNewsBatch)
async def fetch_unprocessed_news(db: Session = Depends(get_db_session), batch_size: int = 100):
    try:
        unprocessed_news = get_unprocessed_news(db, batch_size)
        if unprocessed_news:
            return {"ner_news_items": unprocessed_news}
        else:
            return {"message": "No unprocessed news found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/ner_mark_processed")
async def update_processed_flag(
    news_ids: NewsIDs, db: Session = Depends(get_db_session)
):
    try:
        success = mark_news_as_processed(db, news_ids.news_ids)
        if success:
            return {"message": "News items marked as processed"}
        else:
            raise HTTPException(
                status_code=400, detail="Failed to mark news items as processed"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner_save_results")
async def save_ner_inference_results(
    db: Session = Depends(get_db_session), ner_results: NERInferenceResultBatch
):
    try:
        success = save_ner_results(db, ner_results)
        if success:
            return {"message": "NER results saved successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to save NER results")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
