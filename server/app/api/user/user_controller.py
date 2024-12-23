from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.user.user_dto import UserDTO, UserPasswordChangeDTO, UserRegisterDTO, UserLoginDTO, UserTokenDTO
from app.api.user.user_service import UserService, get_user_service
from app.api.user.user_model import UserRole
from fastapi_cache.decorator import cache
from app.api.config.auth import JWTBearer, JWTDep, get_id_from_jwt
from app.api.config.auth import pre_authorize

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserDTO, summary="Register a new regular user")
def register_user(dto: UserRegisterDTO, user_service: UserService = Depends(get_user_service)): 
    return user_service.add(dto)

@router.post("/login", response_model=UserTokenDTO, status_code=200, summary="Log in to your profile")
def login_user(dto: UserLoginDTO, user_service: UserService = Depends(get_user_service)):
    token = user_service.login(dto)
    return UserTokenDTO(token=token)

@router.post("/password", status_code=204, summary="Change the user's password")
@pre_authorize([UserRole.user, UserRole.admin, UserRole.superadmin], ignore_password_change_requirement=True)
def change_user_password(jwt: JWTDep, dto: UserPasswordChangeDTO, user_service: UserService = Depends(get_user_service)):
    user_id = get_id_from_jwt(jwt)
    user_service.change_password(user_id, dto)

@router.post("/register-admin", response_model=UserDTO, summary="Register a new admin")
@pre_authorize([UserRole.superadmin])
def register_admin(jwt: JWTDep, dto: UserRegisterDTO, user_service: UserService = Depends(get_user_service)):
    return user_service.add_admin(dto)

@router.get("/test")
@cache(expire=10)
@pre_authorize([UserRole.superadmin])
def test(jwt: JWTDep):
    return [
        { "id": 0, "name": "Aza" },
        { "id": 1, "name": "Bub" },
        { "id": 2, "name": "Coc" },
        { "id": 3, "name": "Did" },
    ]