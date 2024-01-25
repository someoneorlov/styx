DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'raw_news_articles'
    ) THEN
        CREATE TABLE raw_news_articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            publish_date TIMESTAMP WITH TIME ZONE,
            publish_date_source VARCHAR(255),
            authors TEXT[],
            canonical_link TEXT,
            feed_link TEXT,
            media_link TEXT,
            media_title TEXT,
            is_parsed BOOLEAN NOT NULL,
            exception_class TEXT,
            exception_text TEXT, 
            url_hash VARCHAR(64),
            canonical_link_hash VARCHAR(64),
            feed_link_hash VARCHAR(64),
            title_hash VARCHAR(64),
            date_created TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ALTER TABLE raw_news_articles 
        ALTER COLUMN text DROP NOT NULL,
        ALTER COLUMN publish_date DROP NOT NULL,
        ALTER COLUMN publish_date_source DROP NOT NULL,
        ALTER COLUMN authors DROP NOT NULL,
        ALTER COLUMN canonical_link DROP NOT NULL;
    END IF;
END
$$;
