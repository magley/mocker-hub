from typing import List
from sqlmodel import Session, or_, select
from app.api.repo.repo_model import Repository, RepositoryStar
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
    
    def set_desc(self, repo: Repository, desc: str) -> Repository:
        repo.sqlmodel_update({"desc": desc})
        self.session.add(repo)
        self.session.commit()
        self.session.refresh(repo)
        return repo
    
    def set_visibility(self, repo: Repository, public: bool) -> Repository:
        repo.sqlmodel_update({"public": public})
        self.session.add(repo)
        self.session.commit()
        self.session.refresh(repo)
        return repo
    
    def set_stars(self, repo: Repository, stars: int) -> Repository:
        repo.sqlmodel_update({"stars": stars})
        self.session.add(repo)
        self.session.commit()
        self.session.refresh(repo)
        return repo

    def unstar_repo(self, repo: Repository, user: User) -> Repository | None:
        repo_star = self.session.exec(
            select(RepositoryStar)
            .where(RepositoryStar.repository_id == repo.id)
            .where(RepositoryStar.starrer_id == user.id)
        ).first()
        
        if repo_star is None:
            return None
        
        self.session.delete(repo_star)
        self.session.commit()
        return self.set_stars(repo, repo.stars - 1)
    
    def star_repo(self, star: RepositoryStar, repo: Repository) -> Repository:
        self.session.add(star)
        self.session.commit()
        self.session.refresh(star)
        return self.set_stars(repo, repo.stars + 1)    
    
    def find_user_starred_repos(self, user_id: int) -> List[Repository] | None:
        query = (
            select(Repository)
            .join(RepositoryStar, Repository.id == RepositoryStar.repository_id, isouter=False)
            .where(RepositoryStar.starrer_id == user_id)
        )

        return self.session.exec(query).all()