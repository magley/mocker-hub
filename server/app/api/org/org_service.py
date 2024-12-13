from fastapi import Depends
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.org.org_dto import OrganizationCreateDTO
from app.api.org.org_model import Organization
from app.api.org.org_repo import OrganizationRepo
from app.api.config.exception_handler import FieldTakenException
 
class OrganizationService:
    def __init__(self, session: Session):
        self.session = session
        self.org_repo = OrganizationRepo(session)

    def add(self, user_id: int, dto: OrganizationCreateDTO) -> Organization:
        # Check if the name is available.

        if self.org_repo.find_by_name(dto.name) is not None:
            raise FieldTakenException("Organization name")
        
        # Create the organization.

        new_repo = Organization.model_validate(dto, update={
            "owner_id": user_id,
        })

        return self.org_repo.add(new_repo)


def get_org_service(session: Session = Depends(get_database)) -> OrganizationService:
    return OrganizationService(session)