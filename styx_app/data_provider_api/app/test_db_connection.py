from sqlalchemy import text
from .db_connector import get_engine, session_factory


def test_db_connection():
    engine = get_engine()
    SessionLocal = session_factory(engine)

    # Use the session object directly from SessionLocal context manager
    with SessionLocal() as session:
        try:
            # Execute a simple SELECT 1 query correctly
            result = session.execute(text("SELECT 1"))
            for row in result:
                print(row)
            print("Database connection established successfully.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_db_connection()
