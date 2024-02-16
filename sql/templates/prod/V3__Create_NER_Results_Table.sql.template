CREATE TABLE ner_results (
    id SERIAL PRIMARY KEY,
    raw_news_article_id INTEGER REFERENCES raw_news_articles(id),
    headline_mentions JSONB,
    body_text_mentions JSONB,
    salient_entities_org JSONB,
    salient_entities_set JSONB,
    date_created TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_raw_news
        FOREIGN KEY(raw_news_article_id) 
        REFERENCES raw_news_articles(id)
);
