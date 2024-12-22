from sqlmodel import Session, select
from app.api.team.team_model import Team, TeamMember, TeamPermission
from typing import List, Optional

class TeamRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, team: Team) -> Team:
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)
        return team

    def get(self, team_id: int) -> Team | None:
        return self.session.get(Team, team_id)

    def get_all(self) -> List[Team]:
        statement = select(Team)
        return self.session.exec(statement).all()

    def add_member(self, team_id: int, user_id: int) -> TeamMember:
        team_member = TeamMember(team_id=team_id, user_id=user_id)
        self.session.add(team_member)
        self.session.commit()
        self.session.refresh(team_member)
        return team_member

    def add_permission(self, team_id: int, repo_id: int, kind: str) -> TeamPermission:
        permission = TeamPermission(team_id=team_id, repo_id=repo_id, kind=kind)
        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission

    def find_all_by_organization(self, organization_id: int) -> List[Team]:
        statement = select(Team).filter(Team.organization_id == organization_id)
        return self.session.exec(statement).all()
    
    def find_member(self, team_id: int, user_id: int) -> Optional[TeamMember]:
        statement = select(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
        return self.session.exec(statement).first()

    def find_permission(self, team_id: int, repo_id: int) -> Optional[TeamPermission]:
        statement = select(TeamPermission).filter(
            TeamPermission.team_id == team_id,
            TeamPermission.repo_id == repo_id
        )
        return self.session.exec(statement).first()