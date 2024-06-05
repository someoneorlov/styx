import React from 'react';
import NewsItem from './NewsItem';
import './NewsList.css';

const NewsList = ({ articles, handleCompanyFilter }) => {
  console.log('Articles:', articles); // Log the articles prop
  return (
    <div className="news-list">
      {articles.map((article, index) => (
        <NewsItem key={index} article={article} handleCompanyFilter={handleCompanyFilter} />
      ))}
    </div>
  );
};

export default NewsList;
