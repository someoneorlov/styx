ALTER TABLE raw_news_articles
ADD COLUMN is_processed_ner BOOLEAN DEFAULT FALSE;
