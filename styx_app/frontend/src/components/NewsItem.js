import React from 'react';
import './NewsItem.css';

const NewsItem = ({ article }) => {
  return (
    <div className="news-item">
      <div className="news-content">
        <div className="news-title">
          <a href={article.canonical_link} target="_blank" rel="noopener noreferrer">
            {article.title}
          </a>
        </div>
        <div className="news-meta">
          {article.media_title} | {new Date(article.publish_date).toLocaleString('en-US', { hour12: true, month: 'long', day: 'numeric', year: 'numeric', hour: 'numeric', minute: 'numeric' })}
        </div>
        <div className="news-summary">
          {article.summary_text}
        </div>
        <div className="hashtags">
          {article.salient_entities_set.map((entity, idx) => (
            <span key={idx}>#{entity} </span>
          ))}
        </div>
      </div>
      <div className="news-sentiment">
        <img src={article.sentiment_predict_proba > 0.5 ? "/thumbs-up.png" : "/thumbs-down.png"} alt="sentiment" />
      </div>
    </div>
  );
};

export default NewsItem;
