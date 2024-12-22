from typing import Dict, List
from fastapi import Depends
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.org.org_dto import OrganizationCreateDTO
from app.api.org.org_model import Organization, OrganizationMembers
from app.api.org.org_repo import OrganizationRepo
from app.api.config.exception_handler import FieldTakenException
from app.api.config.images import generate_inline_image, save_image
 
class OrganizationService:
    def __init__(self, session: Session):
        self.session = session
        self.org_repo = OrganizationRepo(session)

    def add(self, user_id: int, dto: OrganizationCreateDTO) -> Organization:
        # Check if the name is available.

        if self.org_repo.find_by_name(dto.name) is not None:
            raise FieldTakenException("Organization name")
        
        # Save the image.

        if dto.image is None:
            dto.image = generate_inline_image(dto.name)
        image_fname = save_image(dto.image, f"org-{dto.name}")[1]

        # Create the organization.

        new_org = Organization.model_validate(dto, update={
            "owner_id": user_id,
            "image": image_fname,
        })

        org = self.org_repo.add(new_org)

        # Add user to his own organization.

        self.add_user_to_org(org.id, user_id)

        # Refresh the object from the database.
        #
        # NOTE: This is different from Spring Boot which does everything automagically.
        # We've created our `org` in the repo method:
        #    org = ...              <- `org` is in the app memory only, not in the DB.
        #    session.add(org)       <- Put `org` in the staging area.
        #    session.commit()       <- Send `org` to the database: flush + make transaction permanent
        #                               across all later sessions (1 method call = 1 session object).      
        #    session.refresh(org)   <- After commit(), `org` is detached from memory, so we re-fetch it.
        #
        # After that, we create a user-org object in the same way.
        # This means that commit() is called once again, so we lose `org` again.
        # So we have to refresh it again, here. This is bad though, because implementation details of the
        # lower layer (repository) are leaking into the current layer (service).
        #
        # ALTERNATIVES:
        #
        #       1) In database.py, when we create SessionLocal, we may pass `expire_on_commit=False`.
        #       This comes with caveats: expire on commit guarantees consistency within a session.
        #       In that case, we would have to call session.refresh(...) manually every time there
        #       may be a more complex "transaction". 
        #
        #       2) When we create an Organization, the owner of the org is added as its member inside
        #       the same transaction. This may be the way to go.
        #
        self.session.refresh(org)

        return org
    
    def add_user_to_org(self, org_id: int, user_id: int) -> OrganizationMembers:
        return self.org_repo.add_user_to_org(org_id, user_id)
    
    def find_orgs_that_user_is_member_of(self, user_id: int) -> List[Organization]:
        return self.org_repo.find_orgs_that_user_is_member_of(user_id)
    
    def find_org_names_by_ids(self, ids: List[int]) -> Dict[int, str]:
        return self.org_repo.find_orgs_by_ids(ids)
    
    def find_by_name(self, org_name: str) -> Organization:
        return self.org_repo.find_by_name(org_name)
    


def get_org_service(session: Session = Depends(get_database)) -> OrganizationService:
    return OrganizationService(session)