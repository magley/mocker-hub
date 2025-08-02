from typing import Dict, List
from fastapi import Depends
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.org.org_dto import OrganizationCreateDTO, OrganizationDescUpdateDTO
from app.api.org.org_model import Organization, OrganizationMembers
from app.api.org.org_repo import OrganizationRepo
from app.api.config.exception_handler import AccessDeniedException, FieldTakenException, NotFoundException
from app.api.config.images import generate_inline_image, save_image
from app.api.repo.repo_model import Repository
from app.api.team.team_repo import TeamRepo
from app.api.user.user_model import User
from app.api.user.user_repo import UserRepo


class OrganizationService:
    def __init__(self, session: Session):
        self.session = session
        self.org_repo = OrganizationRepo(session)
        self.user_repo = UserRepo(session)
        self.team_repo = TeamRepo(session)

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
    
    def find_by_name(self, name: str) -> Organization:
        org = self.org_repo.find_by_name(name)
        if org is None:
            raise NotFoundException(Organization, name)
        return org
    
    def is_user_member_of_org(self, org_id: int, user_id: int) -> bool:
        return self.org_repo.user_is_in_org(user_id, org_id)

    def get_org_names_from_repos(self, repos: List[Repository]) -> Dict[int, str]:
        return self.find_org_names_by_ids([r.organization_id for r in repos if r.organization_id is not None])

    def remove_org(self, org: Organization) -> None:
        self.org_repo.remove(org)

    def update_desc_by_name(self, name: str, dto: OrganizationDescUpdateDTO, user_id: int) -> Organization:
        org = self.find_by_name(name)
        if user_id != org.owner.id:
            raise AccessDeniedException(f"User {user_id} cannot update organization description with identifier {name}")
        self.update_org_attrs(name, desc=dto.desc)
        return org

    def update_org_attrs(self, name: str, **kwargs) -> Organization:
        org = self.find_by_name(name)
        if org is None:
            raise NotFoundException(Organization, name)
        for attr, value in kwargs.items():
            org = self.org_repo.set_attribute(org, attr, value)
        return org

    def find_members_of_org(self, org_id: int, user_id: int) -> List[User]:
        if not self.org_repo.user_is_in_org(user_id, org_id):
            raise AccessDeniedException(
                f"User {user_id} cannot see members of organization {org_id}")
        return self.org_repo.find_members_of_org(org_id)

    def add_members_to_org(self, org_id: int, user_ids: list[int], owner_id: int):
        org = self.org_repo.find_by_id(org_id)
        if not org:
            raise NotFoundException(Organization, org_id)
        if org.owner_id != owner_id:
            raise AccessDeniedException(f"User {owner_id} cannot add members to organization with id {org_id}")

        new_members = []
        for uid in user_ids:
            user = self.user_repo.find_by_id(uid)
            if not user:
                continue
            if self.org_repo.user_is_in_org(uid, org_id):
                continue
            if user.role == "superadmin":
                continue
            self.org_repo.add_user_to_org(org_id, uid)
            new_members.append(user)
        return new_members

    def search_members_by_username_prefix(self, query: str, team_id_to_exclude_members: int) -> List[User]:
        team = self.team_repo.get(team_id_to_exclude_members)
        if not team:
            raise NotFoundException("Team", team_id_to_exclude_members)
        org_members = self.org_repo.search_members_by_username_prefix(query, team.organization_id)
        members_to_exclude = self.team_repo.find_members_of_team(team_id_to_exclude_members)
        filtered_users = [
            u for u in org_members
            if u.id != team.organization.owner_id and u not in members_to_exclude
        ]
        return filtered_users

    def remove_org_member(self, member_id: int, org_id: int, user_id: int):
        om = self.org_repo.find_member(org_id, member_id)
        if om is None:
            raise NotFoundException(OrganizationMembers, member_id)
        org = self.org_repo.find_by_id(org_id)
        if org.owner_id != user_id:
            raise AccessDeniedException(f"User {user_id} cannot remove member {member_id} from organization {org_id}")
        if user_id == member_id:
            raise AccessDeniedException(f"User {user_id} cannot remove himself from organization {org_id}")
        team_members = self.team_repo.find_teams_of_member(member_id)
        for tm in team_members:
            self.team_repo.delete_team_member(tm)
        self.org_repo.delete_org_member(om)


def get_org_service(session: Session = Depends(get_database)) -> OrganizationService:
    return OrganizationService(session)