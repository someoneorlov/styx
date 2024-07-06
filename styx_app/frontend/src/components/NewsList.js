import React from 'react';
import NewsItem from './NewsItem';
import './NewsList.css';

const NewsList = ({ articles, handleCompanyFilter }) => {
  console.log('Articles:', articles); // Log the articles prop
  return (
    <div className="news-list">
      <h2 className="latest-news">Latest News</h2>
      {articles.map((article, index) => (
        <NewsItem key={index} article={article} handleCompanyFilter={handleCompanyFilter} />
      ))}
    </div>
  );
};

export default NewsList;
