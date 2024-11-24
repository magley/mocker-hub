import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SQLModelSession

postgre_hostname = "db"
postgre_db = os.environ['POSTGRES_DATABASE']
postgre_user = os.environ['POSTGRES_USER']
postgre_password = os.environ['POSTGRES_PASSWORD']
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