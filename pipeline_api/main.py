from __future__ import annotations

import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from pipeline_api.router import router as pipeline_router


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
app.include_router(pipeline_router)
