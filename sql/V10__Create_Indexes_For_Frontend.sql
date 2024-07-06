-- V10__Create_Indexes_For_Frontend.sql

-- Drop the existing index if it exists
DROP INDEX IF EXISTS idx_gin_ner_results_entities;

-- Create the new index with jsonb_path_ops
CREATE INDEX IF NOT EXISTS idx_salient_entities_set ON ner_results USING gin (salient_entities_set jsonb_path_ops);

-- Ensure other indexes are created (if not already done in previous migrations)

-- Index on publish_date for sorting
CREATE INDEX IF NOT EXISTS idx_publish_date ON raw_news_articles(publish_date);

-- Indexes on foreign keys (use the correct column names)
CREATE INDEX IF NOT EXISTS idx_ner_results_raw_news_article_id ON ner_results(raw_news_article_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_article_id ON sentiment_results(raw_news_article_id);
CREATE INDEX IF NOT EXISTS idx_summary_results_article_id ON summary_results(raw_news_article_id);
