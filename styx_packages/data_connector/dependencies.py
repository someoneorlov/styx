from .db_connector import session_factory, get_engine


def get_db_session(db_secret_name=None):
    engine = get_engine(db_secret_name=db_secret_name)
    SessionLocal = session_factory(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
