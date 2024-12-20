from typing import List
from sqlmodel import Session, or_, select
from app.api.repo.repo_model import Repository
from app.api.user.user_model import User
from app.api.org.org_model import Organization, OrganizationMembers

class RepositoryRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, repo: Repository) -> Repository:
        self.session.add(repo)
        self.session.commit()
        self.session.refresh(repo)
        return repo    
    
    def find_by_id(self, id: int) -> Repository | None:
        return self.session.get(Repository, id)
        
    def find_by_canonical_name(self, canonical_name: str) -> Repository | None:
        return self.session.exec(select(Repository).where(Repository.canonical_name == canonical_name)).first()

    def get_repositories_for_user(self, user_id: int):
        query = (
            select(Repository)
            .join(Organization, Organization.id == Repository.organization_id, isouter=True)
            .join(OrganizationMembers, OrganizationMembers.organization_id == Organization.id, isouter=True)
            .where(
                (OrganizationMembers.user_id == user_id) 
                | (Repository.organization_id.is_(None) & (Repository.owner_id == user_id))  
            )
        )

        return self.session.exec(query).all()