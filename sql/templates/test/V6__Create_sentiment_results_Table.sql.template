CREATE TABLE sentiment_results (
    id SERIAL PRIMARY KEY,
    raw_news_article_id INTEGER REFERENCES raw_news_articles(id),
    aws_raw_news_article_id INTEGER NOT NULL,
    sentiment_predict_proba DOUBLE PRECISION,
    date_created TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_raw_news
        FOREIGN KEY(raw_news_article_id) 
        REFERENCES raw_news_articles(id)
);