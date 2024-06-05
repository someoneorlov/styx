import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">Logo</div>
        <nav>
          <ul>
            <li><a href="#">About Us</a></li> {/* Update this with a valid URL or use a button */}
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
