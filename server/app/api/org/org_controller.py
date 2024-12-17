from typing import List
from fastapi import APIRouter, Depends

from app.api.config.auth import get_id_from_jwt, pre_authorize
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep
from app.api.org.org_dto import OrganizationCreateDTO, OrganizationDTOBasic
from app.api.org.org_service import OrganizationService, get_org_service

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationDTOBasic, status_code=200, summary="Create a new organization")
@pre_authorize([UserRole.user, UserRole.admin])
def create_org(jwt: JWTDep, dto: OrganizationCreateDTO, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    repo = org_service.add(user_id, dto)
    return repo


@router.get("/my", response_model=List[OrganizationDTOBasic], status_code=200, summary="Find all organizations that I am a member of")
@pre_authorize([UserRole.user, UserRole.admin])
def find_my_orgs(jwt: JWTDep, org_service: OrganizationService = Depends(get_org_service)):
    user_id = get_id_from_jwt(jwt)
    orgs = org_service.find_orgs_that_user_is_member_of(user_id)
    return orgs