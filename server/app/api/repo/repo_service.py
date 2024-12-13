from fastapi import Depends
from app.api.config.exception_handler import FieldTakenException, NotFoundException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_model import Repository
from app.api.repo.repo_dto import RepositoryCreateDTO
from app.api.org.org_repo import OrganizationRepo
 
class RepositoryService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)

    def add(self, user_id: int, dto: RepositoryCreateDTO) -> Repository:
        # Find the User who's creating the repository.

        owner = self.user_repo.find_by_id(user_id)
        if owner is None:
            raise NotFoundException(User, user_id)
        repo_is_official = owner.role == UserRole.admin 

        # Find the organization this repository is created for (if any).

        org_name = None
        if dto.organization_id is not None:
            organization = self.org_repo.find_by_id(dto.organization_id)
            if organization is not None:
                org_name = organization.name
        
        # Compute the canonical name of the repository.

        canonical_name = Repository.compute_canonical_name(dto.name, owner.username, repo_is_official, org_name)
        if self.repo_repo.find_by_canonical_name(canonical_name):
            raise FieldTakenException("Repository name")

        # Create the new repository.

        new_repo = Repository.model_validate(dto, update={
            "canonical_name": canonical_name,
            "official": repo_is_official,
            "owner_id": owner.id,
        })

        return self.repo_repo.add(new_repo)


def get_repo_service(session: Session = Depends(get_database)) -> RepositoryService:
    return RepositoryService(session)