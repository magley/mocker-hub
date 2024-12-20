from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from app.api.config.initialize import init_create_tables, configure_cors, init_dummy_data, init_superadmin
from app.api.config.exception_handler import register_exception_handler
import app.api.user.user_controller
import app.api.repo.repo_controller
import app.api.org.org_controller
from app.api.config.cache import init_cache

the_router = APIRouter()
the_router.include_router(app.api.user.user_controller.router)
the_router.include_router(app.api.repo.repo_controller.router)
the_router.include_router(app.api.org.org_controller.router)

# TODO: Remove in production, this is for development purposes only.
# This is slightly easier to deal with than environment variables.
@the_router.get("/dummy")
def add_dummy_data():
    init_dummy_data()

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