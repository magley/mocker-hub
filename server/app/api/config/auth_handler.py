import os
import time
from typing import Dict
import jwt
from app.api.user.user_model import User

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']

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

    return token_response(token)

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}