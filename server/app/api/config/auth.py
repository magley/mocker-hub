# ----------------------------------------------
# Authentification utility classes and functions
# ----------------------------------------------
# 
# There are two important definitions in this module:
#
# JWTDep - Used as a dependency for FastAPI routes expecting a JWT.
# pre_authorize - Decorator function similar to Spring Boot.
#
#

from functools import wraps
import inspect
from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Callable, List, get_type_hints
import jwt
from fastapi import HTTPException
from app.api.user.user_model import User, UserRole
from typing import Annotated
from functools import wraps
from typing import List, Callable


JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        
    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            decode_jwt(jwtoken)
        except Exception:
            return False
        return True
 

JWTDep = Annotated[str, Depends(JWTBearer())]


def sign_jwt(user: User) -> str:
    payload = {
        "id": user.id,
        "role": user.role.value,
        "must_change_password": user.must_change_password,
    }
    print(payload)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_role_from_jwt(jwt: JWTDep):
    return decode_jwt(jwt)["role"]


def get_id_from_jwt(jwt: JWTDep):
    return decode_jwt(jwt)["id"]

def validate_jwt_or_raise_exceptions(jwt: JWTDep, expected_roles: List[str] | List[UserRole] | None, ignore_password_change_requirement: bool):
    token = decode_jwt(jwt)

    password_needs_change = token["must_change_password"]
    role_from_jwt = token["role"]
    
    # If password needs change, pre_authorize must fail.
    # Unless ignore_password_change_requirement is True.
    # Which should only be the case when you're changing
    # your password.
    if password_needs_change and not ignore_password_change_requirement:
        raise HTTPException(403, f"Password change required")
        
    # Expected roles not specified => any role is fine.
    if expected_roles is None:
        return
    
    # If the roles were provided as UserRole, convert them to string first.
    expected_roles_str = []
    for role in expected_roles:
        if isinstance(role, UserRole):
            expected_roles_str.append(role.value)
        else:
            expected_roles_str.append(role)
    
    # Check if one of the specified roles matches the one inside the JWT.
    
    if role_from_jwt not in expected_roles_str:
        raise HTTPException(403, f"Access denied for role {role_from_jwt}")


def pre_authorize(roles: List[str] | List[UserRole] | None, ignore_password_change_requirement = False):
    """
    ## Usage

    - `@pre_authorize` must go after `@router.foo`.
    - The endpoint function you're wrapping must have a parameter `jwt: JWTDep`. It must be called `jwt`.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_dep = kwargs.get('jwt')
            if not jwt_dep:
                # TODO: Change error message in production.
                raise Exception("Cannot perform authorization without a JWT. Your router endpoint function MUST have a parameter named `jwt: JWTDep`")
            validate_jwt_or_raise_exceptions(jwt_dep, roles, ignore_password_change_requirement)
            return func(*args, **kwargs)
        return wrapper
    return decorator
