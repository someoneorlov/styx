CREATE TABLE aws_sentiment_results (
    id SERIAL PRIMARY KEY,
    aws_raw_news_article_id INTEGER REFERENCES aws_raw_news_articles(id),
    raw_news_article_id INTEGER NOT NULL,
    sentiment_predict_proba DOUBLE PRECISION,
    is_processed_remote BOOLEAN DEFAULT FALSE,
    date_created TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_raw_news
        FOREIGN KEY(aws_raw_news_article_id) 
        REFERENCES aws_raw_news_articles(id)
);
