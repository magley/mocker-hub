from typing import List
from fastapi import APIRouter, Depends

from app.api.config.auth import get_id_from_jwt, get_id_from_jwt_optional, pre_authorize
from app.api.user.user_dto import UserDTO
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep, JWTDepOptional
from app.api.org.org_dto import OrganizationCreateDTO, OrganizationDTO, OrganizationDTOBasic, OrganizationDescUpdateDTO, OrganizationHasMemberDTO
from app.api.org.org_service import OrganizationService, get_org_service
from app.api.access_control.access_control_service import AccessControlService

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationDTOBasic, status_code=200, summary="Create a new organization")
@pre_authorize([UserRole.user, UserRole.admin])
def create_org(jwt: JWTDep, dto: OrganizationCreateDTO, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    repo = org_service.add(user_id, dto)
    return repo

@router.get("/name/{org_name:path}", response_model=OrganizationDTOBasic, status_code=200, summary="Find organization by name")
def get_by_name(org_name: str, org_service: OrganizationService = Depends(get_org_service)):
    org = org_service.find_by_name(org_name)
    return org

@router.get("/my", response_model=List[OrganizationDTOBasic], status_code=200, summary="Find all organizations that I am a member of")
@pre_authorize([UserRole.user, UserRole.admin])
def find_my_orgs(jwt: JWTDep, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    orgs = org_service.find_orgs_that_user_is_member_of(user_id)
    return orgs

@router.get("/me/{org_id}", response_model=OrganizationHasMemberDTO, status_code=200, summary="Check if I am member of org (works for guests, too)")
def am_i_member_of_org(org_id: int, jwt: JWTDepOptional, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt_optional(jwt)
    is_member = org_service.is_user_member_of_org(org_id, user_id)
    return OrganizationHasMemberDTO(
        org_id=org_id, 
        user_id=user_id, 
        is_member=is_member
    )

@router.put("/{org_name}/desc", response_model=OrganizationDTO, status_code=200, summary="Update organization description by its name")
@pre_authorize([UserRole.user, UserRole.admin])
def update_org_desc_by_name(
    jwt: JWTDep, org_name: str, 
    dto: OrganizationDescUpdateDTO, 
    org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    org = org_service.update_desc_by_name(org_name, dto, user_id)
    return org

@router.get("/{org_id}/members", response_model=List[UserDTO], status_code=200, summary="Find all members of an organization")
@pre_authorize([UserRole.user, UserRole.admin])
def find_members_of_org(jwt: JWTDep, org_id: int, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    members = org_service.find_members_of_org(org_id, user_id)
    return members

@router.post("/{org_id}/addMember", response_model=List[UserDTO], status_code=200, summary="Add multiple users to an organization")
@pre_authorize([UserRole.user, UserRole.admin])
def add_members_to_org(jwt: JWTDep, org_id: int, user_ids: List[int], org_service: OrganizationService = Depends(get_org_service)):
    owner_id = get_id_from_jwt(jwt)
    result = org_service.add_members_to_org(org_id, user_ids, owner_id)
    return result

@router.get("/search/{query}", status_code=200, response_model=List[UserDTO], summary="Search members by username prefix")
@pre_authorize([UserRole.user, UserRole.admin])
def search_members_by_username_prefix(jwt: JWTDep, query: str, team_id_to_exclude_members: int, org_service: OrganizationService = Depends(get_org_service)):
    users = org_service.search_members_by_username_prefix(query, team_id_to_exclude_members)
    return users
