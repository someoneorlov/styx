DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'styx_database'
    ) THEN
        CREATE DATABASE styx_database;
    END IF;
END
$$;