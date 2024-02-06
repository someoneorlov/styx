from .db_connector import session_factory, get_engine


def get_db_session():
    SessionLocal = session_factory(get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
