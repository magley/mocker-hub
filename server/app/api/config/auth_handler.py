import os
import time
from typing import Dict, List
import jwt
from fastapi import HTTPException
from app.api.user.user_model import User, UserRole
from pydantic import BaseModel

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']

class TokenDTO(BaseModel):
    access_token: str

def token_response(token: str):
    return {
        "access_token": token
    }

def sign_jwt(user: User) -> Dict[str, str]:
    payload = {
        "id": user.id,
        "role": user.role, 
        "must_change_password": user.must_change_password,
        "expires": time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return TokenDTO(access_token=token)

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
    
def pre_authorize(token: str, roles:  List[UserRole], is_change_password = False) -> dict:
    decoded_token = decode_jwt(token)
    if decoded_token['must_change_password'] and is_change_password == False:
        raise HTTPException(403, "Password change is required before proceeding")    
    elif decoded_token['role'] not in [role.value for role in roles]:
        raise HTTPException(401, "User does not have permission to access this page")
    return decoded_token