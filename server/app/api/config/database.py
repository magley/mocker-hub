import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session


# database_url = "sqlite:///database.db"

postgre_hostname = "db"
postgre_db = os.environ['POSTGRES_DATABASE']
postgre_user = os.environ['POSTGRES_USER']
postgre_password = os.environ['POSTGRES_PASSWORD']
database_url = f"postgresql://{postgre_user}:{postgre_password}@{postgre_hostname}/{postgre_db}"

engine = create_engine(
    database_url,
#    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
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