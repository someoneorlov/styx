import React, { useState } from 'react';
import './NewsItem.css';

const NewsItem = ({ article, handleCompanyFilter }) => {
  const [showFullText, setShowFullText] = useState(false);

  const toggleFullText = () => {
    setShowFullText(!showFullText);
  };

  return (
    <div className="news-item">
      <h3><a href={article.canonical_link} target="_blank" rel="noopener noreferrer">{article.title}</a></h3>
      <p>{article.publish_date}</p>
      <p><a href={article.media_link} target="_blank" rel="noopener noreferrer">{article.media_title}</a></p>
      <div className="salient-entities">
        {article.salient_entities_set.map((entity, index) => (
          <span key={index} className="entity" onClick={() => handleCompanyFilter(entity)}>#{entity}</span>
        ))}
      </div>
      <div className="sentiment">
        {article.sentiment_predict_proba >= 0.5 ? '👍' : '👎'}
      </div>
      <p className="summary-text">
        {showFullText ? article.summary_text : `${article.summary_text.substring(0, 100)}... `}
        <span className="read-more" onClick={toggleFullText}>
          {showFullText ? 'Show less' : 'Read more'}
        </span>
      </p>
    </div>
  );
};

export default NewsItem;
