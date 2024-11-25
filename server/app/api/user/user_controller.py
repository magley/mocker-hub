from fastapi import APIRouter, Depends

from app.api.user.user_dto import UserDTO, UserRegisterDTO
from app.api.user.user_service import UserService, get_user_service
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserDTO, status_code=200, summary="Register a new regular user")
def register_user(dto: UserRegisterDTO, user_service: UserService = Depends(get_user_service)):
    user = user_service.add(dto)
    return user


@router.get("/test")
@cache(expire=10)
def test():
    return [
        { "id": 0, "name": "Aza" },
        { "id": 1, "name": "Bub" },
        { "id": 2, "name": "Coc" },
        { "id": 3, "name": "Did" },
    ]