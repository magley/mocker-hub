from typing import List
from fastapi import APIRouter, Depends

from app.api.config.auth import get_id_from_jwt, pre_authorize
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep
from app.api.team.team_dto import TeamAddMemberDTO, TeamCreateDTO, TeamDTOBasic
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
    return teams