from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import sqlalchemy.exc

def register_exception_handler(app: FastAPI):
    @app.exception_handler(ValidationError)
    def _ValidationError(r: Request, e: ValidationError):
        raise HTTPException(400, detail={"message": e.errors()}) 
    
    @app.exception_handler(sqlalchemy.exc.IntegrityError)
    def _IntegrityError(r: Request, e: sqlalchemy.exc.IntegrityError):
        raise HTTPException(400, detail={"message": e._message()}) 