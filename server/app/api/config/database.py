import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SQLModelSession
from sqlalchemy.pool import StaticPool

if os.getenv('mocker_hub_TEST_ENV') is not None:
    print("[!] Detected environment variable mocker_hub_TEST_ENV -> using SQLite")

    # To make the database truly in-memory, you need to specify a static 
    # pool which uses only one connection, shared between all requests.
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
else:
    postgre_hostname = "db"
    postgre_db = os.environ.get('POSTGRES_DATABASE', None)
    postgre_user = os.environ.get('POSTGRES_USER', None)
    postgre_password = os.environ.get('POSTGRES_PASSWORD', None)
    database_url = f"postgresql://{postgre_user}:{postgre_password}@{postgre_hostname}/{postgre_db}"

    engine = create_engine(database_url)

SessionLocal = sessionmaker(
    # https://github.com/fastapi/sqlmodel/issues/75#issuecomment-2109911909
    class_ = SQLModelSession,
    
    autocommit=False,
    autoflush=False,

    # expire_on_commit = False,
    bind=engine
)

def get_database():
    db = SessionLocal()
    try:
        yield db
    except:
        db.rollback()
        raise
    finally:
        db.close()