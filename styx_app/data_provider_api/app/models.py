from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True


class BaseNewsItem(OurBaseModel):
    id: int
    title: str
    text: str


class NERNewsItem(BaseNewsItem):
    is_processed_ner: Optional[bool] = False


class NERNewsBatch(OurBaseModel):
    ner_news_items: List[NERNewsItem]


class Mention(OurBaseModel):
    start: int
    length: int
    mention_text: str
    linked_entity: str
    confidence_score: float
    link_probability: float
    entity_type: str


class NERInferenceResult(OurBaseModel):
    raw_news_id: int
    headline_mentions: List[Mention]
    body_text_mentions: List[Mention]
    salient_entities_org: List[Mention]
    salient_entities_set: List[str]


class NERInferenceResultBatch(OurBaseModel):
    ner_inference_results: List[NERInferenceResult]


class NewsIDs(OurBaseModel):
    news_ids: List[int]


class ArticleMainPage(OurBaseModel):
    title: str
    text: str
    publish_date: datetime
    canonical_link: str
    media_link: str
    media_title: str
    salient_entities_set: List[str]


class ArticlesMPBatch(OurBaseModel):
    articles: List[ArticleMainPage]
