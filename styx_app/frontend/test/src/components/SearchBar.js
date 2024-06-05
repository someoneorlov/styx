import React from 'react';
import './SearchBar.css';

const SearchBar = ({ companyName, setCompanyName, handleSubmit }) => {
  return (
    <div className="search-bar">
      <h2>Which company are you interested in?</h2>
      <p>We know everything.</p>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="Type company name, e.g. Tesla"
        />
        <button type="submit">Search</button>
      </form>
    </div>
  );
};

export default SearchBar;
