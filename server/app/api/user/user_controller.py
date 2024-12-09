from fastapi import APIRouter, Depends

from app.api.user.user_dto import UserDTO, UserPasswordChangeDTO, UserRegisterDTO, UserLoginDTO
from app.api.user.user_service import UserService, get_user_service
from app.api.user.user_model import UserRole
from fastapi_cache.decorator import cache
from typing import Dict, Annotated
from app.api.config.auth_bearer import JWTBearer
from app.api.config.auth_handler import TokenDTO, pre_authorize

router = APIRouter(prefix="/users", tags=["users"])
JWTDep = Annotated[dict, Depends(JWTBearer())]

@router.post("/", status_code=201, summary="Register a new regular user")
def register_user(dto: UserRegisterDTO, user_service: UserService = Depends(get_user_service)): 
    user_service.add(dto)

@router.post("/login", response_model=TokenDTO, status_code=200, summary="Log in to your profile")
def login_user(dto: UserLoginDTO, user_service: UserService = Depends(get_user_service)):
    token = user_service.login(dto)
    return token

@router.post("/password", response_model=TokenDTO, status_code=200, summary="Change the user's password")
def change_user_password(token: JWTDep, dto: UserPasswordChangeDTO, user_service: UserService = Depends(get_user_service)):
    decoded_token = pre_authorize(token, [UserRole.user, UserRole.admin, UserRole.superadmin], True)
    token = user_service.change_password(decoded_token["id"], dto)
    return token

@router.get("/test")
@cache(expire=10)
def test(token: JWTDep):
    pre_authorize(token, [UserRole.user, UserRole.admin])
    return [
        { "id": 0, "name": "Aza" },
        { "id": 1, "name": "Bub" },
        { "id": 2, "name": "Coc" },
        { "id": 3, "name": "Did" },
    ]