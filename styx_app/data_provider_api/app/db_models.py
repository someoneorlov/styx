from sqlalchemy import Column, Integer, String, Boolean, ARRAY, Text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class RawNewsArticle(Base):
    __tablename__ = "raw_news_articles"
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    text = Column(Text)
    publish_date = Column(TIMESTAMP(timezone=True))
    publish_date_source = Column(String(255))
    authors = Column(ARRAY(Text))
    canonical_link = Column(Text)
    feed_link = Column(Text)
    media_link = Column(Text)
    media_title = Column(Text)
    is_parsed = Column(Boolean, nullable=False, default=False)
    exception_class = Column(Text)
    exception_text = Column(Text)
    url_hash = Column(String(64))
    canonical_link_hash = Column(String(64))
    feed_link_hash = Column(String(64))
    title_hash = Column(String(64))
    date_created = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_processed_ner = Column(Boolean, default=False)
    is_processed_aws = Column(Boolean, default=False)
    ner_results = relationship(
        "NerResults", back_populates="raw_news_article"
    )  # Relationship to NerResults


class NerResults(Base):
    __tablename__ = "ner_results"
    id = Column(Integer, primary_key=True)
    raw_news_article_id = Column(
        Integer, ForeignKey("raw_news_articles.id"), nullable=False
    )
    headline_mentions = Column(JSON)
    body_text_mentions = Column(JSON)
    salient_entities_org = Column(JSON)
    salient_entities_set = Column(JSON)
    date_created = Column(TIMESTAMP(timezone=True), server_default=func.now())
    raw_news_article = relationship("RawNewsArticle", back_populates="ner_results")
