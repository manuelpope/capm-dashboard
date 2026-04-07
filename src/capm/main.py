import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.capm.api.routes import router as api_router
from src.capm.config import settings

limiter = Limiter(key_func=get_remote_address)


def need_sync_check():
    from src.capm.domain.repositories import SQLiteMetricRepository
    from src.capm.application.sync_service import needs_sync

    db = SQLiteMetricRepository()
    last_calc = db.get_latest_calculation()
    return needs_sync(last_calc)


def get_sync_status():
    try:
        return {"status": "ok" if not need_sync_check() else "needs_sync"}
    except Exception:
        return {"status": "error"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.capm.domain.repositories import SQLiteMetricRepository
    from src.capm.application.sync_service import SyncService, get_default_tickers

    db = SQLiteMetricRepository()
    sync_service = SyncService(db)

    if sync_service.needs_sync():
        tickers = get_default_tickers()
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, sync_service.run_sync, tickers)

    yield


app = FastAPI(
    title="CAPM Terminal",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


@app.get("/health")
async def health():
    return get_sync_status()


app.include_router(api_router)
