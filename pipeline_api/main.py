from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pipeline_api.router import router as pipeline_router
from pipeline_api.dashboard_router import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    dsn = os.getenv(
        "SSOT_DATABASE_DSN",
        "postgresql://ssot:ssot@127.0.0.1:5433/ssot",
    )
    app.state.pg_pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)
    try:
        yield
    finally:
        await app.state.pg_pool.close()


app = FastAPI(title="SSOT Pipeline API", version="1.0.0", lifespan=lifespan)

# Mount static files and include dashboard router
BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

app.include_router(dashboard_router)
app.include_router(pipeline_router)
