import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SQLModelSession

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