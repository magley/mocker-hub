from fastapi import APIRouter, FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.api.config.initialize import init_create_tables, configure_cors, init_superadmin
from app.api.config.exception_handler import register_exception_handler
import app.api.user.user_controller
from app.api.config.cache import init_cache

the_router = APIRouter()
the_router.include_router(app.api.user.user_controller.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_create_tables()
    init_cache()
    init_superadmin()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(the_router, prefix="/api/v1")

register_exception_handler(app)
configure_cors(app)