from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TIMESTAMP

Base = declarative_base()


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
    date_created = Column(TIMESTAMP(timezone=False), server_default="CURRENT_TIMESTAMP")
    # Add the is_processed_ner column if it's part of your application logic
    is_processed_ner = Column(Boolean, default=False)
