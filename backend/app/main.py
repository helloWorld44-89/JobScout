from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Schema is managed by Alembic — run `alembic upgrade head` before starting.
    yield


app = FastAPI(title="JobScout API", lifespan=lifespan)
app.include_router(api_router)
