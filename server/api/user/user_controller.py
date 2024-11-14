from fastapi import APIRouter, Depends

from server.api.user.user_dto import UserDTO
from server.api.user.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserDTO, status_code=200, summary="Register a new regular user")
def user_register(dto: UserDTO, user_service: UserService = Depends(get_user_service)):
    user = user_service.add(dto)
    return user