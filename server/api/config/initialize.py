from sqlmodel import SQLModel
from server.api.config.database import engine

def init_create_tables():
    SQLModel.metadata.create_all(engine)