from typing import List
from sqlmodel import Session, select
from app.api.org.org_model import Organization, OrganizationMembers
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
    
    def add_user_to_org(self, org_id: int, user_id: int) -> OrganizationMembers:
        orgmember = OrganizationMembers(user_id=user_id, organization_id=org_id)

        self.session.add(orgmember)
        self.session.commit()
        self.session.refresh(orgmember)
        return orgmember