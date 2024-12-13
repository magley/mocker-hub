from sqlmodel import Session, select
from app.api.org.org_model import Organization
from app.api.repo.repo_model import Repository
from app.api.user.user_model import User

class OrganizationRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, org: Organization) -> Organization:
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        return org    
    
    def find_by_id(self, id: int) -> Organization | None:
        return self.session.get(Organization, id)
    
    def find_by_name(self, name: str) -> Organization | None:
        return self.session.exec(select(Organization).where(Organization.name == name)).first()