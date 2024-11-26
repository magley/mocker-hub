from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import sqlalchemy.exc

class UserException(Exception):
     ...

class FieldTakenException(UserException):
    def __init__(self, field: str):
        self.message = f"{field} already taken"

    def __str__(self):
        return self.message
    
class NotFoundException(UserException):
    def __init__(self, entity_type, identifier):
          self.message = f"Could not find {entity_type} with identifier {identifier}"

    def __str__(self):
        return self.message


def register_exception_handler(app: FastAPI):
    @app.exception_handler(UserException)
    def _UserException(r: Request, e: UserException):
        raise HTTPException(400, detail={"message": str(e)}) 
    
    @app.exception_handler(RequestValidationError)
    def _ValidationError(r: Request, e: RequestValidationError):
        raise HTTPException(400, detail={"message": str(e.errors())})
    
    @app.exception_handler(sqlalchemy.exc.IntegrityError)
    def _IntegrityError(r: Request, e: sqlalchemy.exc.IntegrityError):
        raise HTTPException(400, detail={"message": e._message()}) 