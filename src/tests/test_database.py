import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

load_dotenv()

def test_database_url_is_set():
    """Tests that the DB_CONNECTION_URL environment variable is set."""
    db_url = os.getenv("DB_CONNECTION_URL")
    assert db_url is not None, "DB_CONNECTION_URL environment variable is not set."
    print("DB_CONNECTION_URL is set.")


def test_database_connection():
    """Tests that a connection can be established to the database."""
    db_url = os.getenv("DB_CONNECTION_URL")
    if db_url is None:
        return

    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            print("Database connection successful from test.")
            assert True
    except OperationalError as e:
        print(f"Database connection failed from test: {e}")
        assert False, f"Could not connect to database: {e}" 