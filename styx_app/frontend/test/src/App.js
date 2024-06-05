import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Header from './components/Header';
import SearchBar from './components/SearchBar';
import NewsList from './components/NewsList';
import Pagination from './components/Pagination';
import Footer from './components/Footer';
import './App.css';

const App = () => {
  const [news, setNews] = useState([]);
  const [companyName, setCompanyName] = useState('');
  const [batchSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchNews = useCallback(async (page = 1, company = '') => {
    try {
      console.log(`Fetching news for page ${page} and company ${company}`);
      const response = await axios.get(`/api/front-data/news`, {
        params: { company_name: company, batch_size: batchSize, page }
      });
      console.log('API Response:', response.data); // Log the API response
      setNews(response.data.articles);
      setTotalPages(Math.ceil(response.data.total / batchSize)); // Assuming response includes total articles count
    } catch (error) {
      console.error('Error fetching news:', error);
    }
  }, [batchSize]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const handleSubmit = (event) => {
    event.preventDefault();
    fetchNews(1, companyName);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    fetchNews(page, companyName);
  };

  const handleCompanyFilter = (company) => {
    setCompanyName(company);
    fetchNews(1, company);
  };

  return (
    <div className="app">
      <Header />
      <SearchBar
        companyName={companyName}
        setCompanyName={setCompanyName}
        handleSubmit={handleSubmit}
      />
      <NewsList articles={news} handleCompanyFilter={handleCompanyFilter} />
      <Pagination
        totalPages={totalPages}
        currentPage={currentPage}
        handlePageChange={handlePageChange}
      />
      <Footer />
    </div>
  );
};

export default App;
