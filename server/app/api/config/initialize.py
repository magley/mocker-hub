import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select
from app.api.config.database import engine, get_database
from app.api.user.user_model import User, UserRole
from app.api.user.user_dto import UserRegisterDTO
from app.api.user.user_service import UserService

def init_create_tables():
    SQLModel.metadata.create_all(engine)

def configure_cors(app: FastAPI):
    origins = [
        "http://localhost:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def init_superadmin():
    session = next(get_database())
    service = UserService(session)
    config_file = "./volume-server-cfg/superadmin_password.txt"
    
    print("Checking for superadmin...")
    existing_superadmin = session.exec(select(User).where(User.role == UserRole.superadmin)).first()

    if existing_superadmin is None:
        print("Adding superadmin...")
        password = os.getenv("SUPERADMIN_PASSWORD", "admin123")
        dto = UserRegisterDTO(email="admin@gmail.com", username="admin", password=password)
        
        with open(config_file, "w") as f:
            f.write(password)
            print(f"Written initial password to {os.path.abspath(config_file)}")
        
        service.add_superadmin(dto)

        print("Superadmin added")
    else:
        print("Superadmin already exists")
        return