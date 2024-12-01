from sqlmodel import Session, select
from app.api.repo.repo_model import Repository
from app.api.user.user_model import User

class RepositoryRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, repo: Repository) -> Repository:
        self.session.add(repo)
        self.session.commit()
        self.session.refresh(repo)
        return repo    
    
    def find_by_id(self, id: int) -> Repository | None:
        return self.session.get(User, id)
        
    def find_by_canonical_name(self, canonical_name: str) -> Repository | None:
        return self.session.exec(select(Repository).where(Repository.canonical_name == canonical_name)).first()
    