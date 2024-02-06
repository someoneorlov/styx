from pydantic import BaseModel
from typing import Optional, List


class BaseNewsItem(BaseModel):
    id: int
    title: str
    text: str


class NERNewsItem(BaseNewsItem):
    is_processed_ner: Optional[bool] = False


class NERNewsBatch(BaseModel):
    ner_news_items: List[NERNewsItem]


class Mention(BaseModel):
    start: int
    length: int
    mention_text: str
    linked_entity: str
    confidence_score: float
    link_probability: float
    entity_type: str


class NERInferenceResult(BaseModel):
    raw_news_id: int
    headline_mentions: List[Mention]
    body_text_mentions: List[Mention]
    salient_entities_org: List[Mention]
    salient_entities_set: List[str]


class NERInferenceResultBatch(BaseModel):
    ner_inference_results: List[NERInferenceResult]


class NewsIDs(BaseModel):
    news_ids: List[int]
