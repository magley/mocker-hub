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
          self.entity_type = entity_type
          self.identifier = identifier
          self.message = f"Could not find {entity_type} with identifier {identifier}"

    def __str__(self):
        return self.message
    
class AccessDeniedException(UserException):
    def __init__(self, msg: str):
        self.message = f"{msg}"

    def __str__(self):
        return self.message

class NotInRelationshipException(UserException):
    """
    Exceptions of the type: `[e1] is not in [e2]`.
    """
    def __init__(self, e1_type, e1_id, e2_type, e2_id):
          self.message = f"{e1_type} with identifier {e1_id} does not have a {e2_type} with identifier {e2_id}"

    def __str__(self):
        return self.message

def register_exception_handler(app: FastAPI):
    @app.exception_handler(NotFoundException)
    def _NotFoundException(r: Request, e: NotFoundException):
        raise HTTPException(404, detail={"message": str(e)}) 
    
    @app.exception_handler(UserException)
    def _UserException(r: Request, e: UserException):
        raise HTTPException(400, detail={"message": str(e)}) 
    
    @app.exception_handler(RequestValidationError)
    def _ValidationError(r: Request, e: RequestValidationError):
        raise HTTPException(400, detail={"message": str(e.errors())})
    
    @app.exception_handler(sqlalchemy.exc.IntegrityError)
    def _IntegrityError(r: Request, e: sqlalchemy.exc.IntegrityError):
        raise HTTPException(400, detail={"message": e._message()}) 