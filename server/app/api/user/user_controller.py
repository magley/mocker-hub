from fastapi import APIRouter, Depends

from app.api.user.user_dto import UserDTO
from app.api.user.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserDTO, status_code=200, summary="Register a new regular user")
def user_register(dto: UserDTO, user_service: UserService = Depends(get_user_service)):
    user = user_service.add(dto)
    return user

@router.get("/test")
def test():
    return [
        { "id": 0, "name": "Aza" },
        { "id": 1, "name": "Bub" },
        { "id": 2, "name": "Coc" },
        { "id": 3, "name": "Did" },
    ]