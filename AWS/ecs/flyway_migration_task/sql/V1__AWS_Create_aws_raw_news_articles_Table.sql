DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'aws_raw_news_articles'
    ) THEN
        CREATE TABLE aws_raw_news_articles (
            id SERIAL PRIMARY KEY,
            raw_news_article_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            publish_date TIMESTAMP WITH TIME ZONE,
            publish_date_source VARCHAR(255),
            authors TEXT[],
            media_title TEXT,
            is_processed_ner BOOLEAN DEFAULT FALSE,
            is_processed_sentiment BOOLEAN DEFAULT FALSE,
            is_processed_summary BOOLEAN DEFAULT FALSE,
            date_created TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    END IF;
END
$$;
