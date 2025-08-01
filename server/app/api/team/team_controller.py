from typing import List
from fastapi import APIRouter, Depends

from app.api.config.auth import get_id_from_jwt, pre_authorize
from app.api.user.user_dto import UserDTO
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep
from app.api.team.team_dto import TeamAddMemberDTO, TeamCreateDTO, TeamDTOBasic, TeamPermissionsDTO, \
    TeamAddPermissionDTO
from app.api.team.team_service import TeamService, get_team_service

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamDTOBasic, status_code=200, summary="Create a new team")
@pre_authorize([UserRole.user, UserRole.admin])
def create_team(jwt: JWTDep, dto: TeamCreateDTO, team_service: TeamService = Depends(get_team_service)):
    user_id = get_id_from_jwt(jwt)
    team = team_service.create_team(dto, user_id)
    return team

@router.get("/o/{org_id}", response_model=List[TeamDTOBasic], status_code=200, summary="Find all teams by organization")
@pre_authorize([UserRole.user, UserRole.admin])
def find_by_org_id(jwt: JWTDep, org_id: int, team_service: TeamService = Depends(get_team_service)):
    user_id = get_id_from_jwt(jwt)
    teams = team_service.find_by_org(org_id, user_id)
    return [TeamDTOBasic(
            id=team.id,
            name=team.name,
            desc=team.desc,
            organization_id=team.organization_id,
            members_count=len(team.members))
        for team in teams]


@router.get("/{team_id}/members", response_model=List[UserDTO], status_code=200, summary="Find all members of a team")
@pre_authorize([UserRole.user, UserRole.admin])
def find_members_of_team(jwt: JWTDep, team_id: int, team_service: TeamService = Depends(get_team_service)):
    user_id = get_id_from_jwt(jwt)
    members = team_service.find_members_of_team(team_id, user_id)
    return members

@router.post("/{team_id}/addMember", response_model=List[TeamAddMemberDTO], status_code=200, summary="Add multiple users to the team")
@pre_authorize([UserRole.user, UserRole.admin])
def add_members_to_team(jwt: JWTDep, team_id: int, user_ids: List[int], team_service: TeamService = Depends(get_team_service)):
    owner_id = get_id_from_jwt(jwt)
    results = []
    for uid in user_ids:
        dto = TeamAddMemberDTO(team_id=team_id, user_id=uid)
        result = team_service.add_member(dto, owner_id)
        results.append(result)
    return results

@router.post("/permission", response_model=TeamPermissionsDTO, status_code=200, summary="Add team permission")
@pre_authorize([UserRole.user, UserRole.admin])
def add_permission(jwt: JWTDep, dto: TeamPermissionsDTO, team_service: TeamService = Depends(get_team_service)):
    owner_id = get_id_from_jwt(jwt)
    print(dto)
    add_dto = TeamAddPermissionDTO(team_id=dto.team_id, repo_id=dto.repo_id, kind=dto.kind)
    result = team_service.add_permission(add_dto, owner_id)
    return result

@router.get("/{team_id}/permissions", response_model=List[TeamPermissionsDTO], status_code=200, summary="Find all permissions of a team")
@pre_authorize([UserRole.user, UserRole.admin])
def get_permissions_by_team(jwt: JWTDep, team_id: int, team_service: TeamService = Depends(get_team_service)):
    user_id = get_id_from_jwt(jwt)
    members = team_service.get_permissions_by_team(team_id, user_id)
    return members
