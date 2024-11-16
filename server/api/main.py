from fastapi import APIRouter, FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from server.api.config.initialize import init_create_tables, configure_cors
from server.api.config.exception_handler import register_exception_handler
import server.api.user.user_controller


the_router = APIRouter()
the_router.include_router(server.api.user.user_controller.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_create_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(the_router, prefix="/api/v1")

register_exception_handler(app)
configure_cors(app)