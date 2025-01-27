import asyncio
import os
from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from app.api.config.initialize import init_create_tables, configure_cors, init_dummy_data, init_superadmin
from app.api.config.exception_handler import register_exception_handler
import app.api.events
import app.api.events.event_controller
import app.api.user.user_controller
import app.api.repo.repo_controller
import app.api.org.org_controller
import app.api.registry.registry_controller
import app.api.team.team_controller
import app.api.tags.tag_controller
from app.api.config.cache import init_cache
from app.api.config.elasticsearch import try_to_init_elasticsearch

the_router = APIRouter()
the_router.include_router(app.api.user.user_controller.router)
the_router.include_router(app.api.repo.repo_controller.router)
the_router.include_router(app.api.org.org_controller.router)
the_router.include_router(app.api.team.team_controller.router)
the_router.include_router(app.api.events.event_controller.router)
the_router.include_router(app.api.tags.tag_controller.router)

internal_registry_router = APIRouter()
internal_registry_router.include_router(app.api.registry.registry_controller.router)

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
    asyncio.create_task(try_to_init_elasticsearch())
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(the_router, prefix="/api/v1")
app.include_router(internal_registry_router)

register_exception_handler(app)
configure_cors(app)