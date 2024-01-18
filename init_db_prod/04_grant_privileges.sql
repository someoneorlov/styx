REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM scraping_user;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM scraping_user;

-- Grant necessary permissions to scraping_user
GRANT CONNECT ON DATABASE styx_database TO scraping_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO scraping_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO scraping_user;