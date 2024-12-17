import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select
from app.api.config.database import engine, get_database
from app.api.user.user_model import User, UserRole
from app.api.user.user_dto import UserRegisterDTO
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.org.org_service import OrganizationService
from app.api.repo.repo_dto import RepositoryCreateDTO
from app.api.org.org_dto import OrganizationCreateDTO

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
    

def init_dummy_data():
    print("Adding dummy data...")

    session = next(get_database())
    user_service = UserService(session)
    repo_service = RepositoryService(session)
    org_service = OrganizationService(session)

    user1 = user_service.add(UserRegisterDTO(username="user1", email="user1@test.com", password="1234"))
    user2 = user_service.add(UserRegisterDTO(username="user2", email="user2@test.com", password="1234"))
    user3 = user_service.add(UserRegisterDTO(username="user3", email="user3@test.com", password="1234"))
    user4 = user_service.add(UserRegisterDTO(username="user4", email="user4@test.com", password="1234"))
    user5 = user_service.add(UserRegisterDTO(username="user5", email="user5@test.com", password="1234"))
    user6 = user_service.add(UserRegisterDTO(username="user6", email="user6@test.com", password="1234"))

    org1 = org_service.add(user1.id, OrganizationCreateDTO(name="org1", desc="", image=None))
    org2 = org_service.add(user2.id, OrganizationCreateDTO(name="org2", desc="", image=None))
    org3 = org_service.add(user1.id, OrganizationCreateDTO(name="org3", desc="", image=None))

    org_service.add_user_to_org(org_id=org1.id, user_id=user2.id)

    repo1 = repo_service.add(user1.id, RepositoryCreateDTO(name="python", desc="Python3 docker image!", public=True, organization_id=None))
    repo2 = repo_service.add(user1.id, RepositoryCreateDTO(name="node", desc="NodeJS docker image!!!!", public=False, organization_id=None))
    repo3 = repo_service.add(user1.id, RepositoryCreateDTO(name="dsa", desc="DSA... what could it be?", public=True, organization_id=org1.id))
    repo4 = repo_service.add(user1.id, RepositoryCreateDTO(name="mio", desc="Mio's... nothing at all", public=False, organization_id=org1.id))
    repo5 = repo_service.add(user2.id, RepositoryCreateDTO(name="dsa-ui", desc="Just a temp repo....", public=True, organization_id=org1.id))
    repo6 = repo_service.add(user2.id, RepositoryCreateDTO(name="istrue", desc="istrue e repo o algo", public=True, organization_id=org2.id))
    repo7 = repo_service.add(user3.id, RepositoryCreateDTO(name="redis", desc="The best NoSQL DB!!!!", public=True, organization_id=None))
    repo8 = repo_service.add(user4.id, RepositoryCreateDTO(name="redis", desc="The worst NoSQL DB!!!", public=True, organization_id=None))

    
    print("Finished adding dummy data.")