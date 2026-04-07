from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from src.capm.domain.interfaces import IMetricRepository
from src.capm.domain.repositories import SQLiteMetricRepository
from src.capm.api.deps import get_db, verify_api_key
from src.capm.infrastructure.templates import generate_dashboard
from src.capm.config import settings
from src.capm.application.sync_service import SyncService, get_default_tickers


limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def get_sync_service(repo: IMetricRepository = Depends(get_db)) -> SyncService:
    return SyncService(repo)


@router.get("/", response_class=HTMLResponse)
async def dashboard(sync_service: SyncService = Depends(get_sync_service)):
    if sync_service.needs_sync():
        import asyncio

        tickers = get_default_tickers()
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, sync_service.run_sync, tickers)

    db = sync_service._repository
    return generate_dashboard(db)


@router.post("/sync")
@limiter.limit("10/minute")
async def sync_metrics(
    request: Request,
    sync_service: SyncService = Depends(get_sync_service),
    db: IMetricRepository = Depends(get_db),
):
    verify_api_key(request)
    body = await request.json()
    tickers = body.get("tickers", get_default_tickers())

    result = sync_service.run_sync(tickers)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


@router.get("/api/metrics")
async def api_metrics(
    active_only: bool = True, db: IMetricRepository = Depends(get_db)
):
    metrics = db.get_all_metrics(active_only=active_only)
    return [
        {
            "ticker": m.ticker,
            "current_price": m.current_price,
            "volume": m.volume,
            "beta": m.beta,
            "alpha": m.alpha,
            "sharpe": m.sharpe,
            "capm": m.capm,
            "r_squared": m.r_squared,
            "p_value": m.p_value,
            "risk_free_rate": m.risk_free_rate,
            "risk_free_source": m.risk_free_source,
            "market_return": m.market_return,
            "active": m.active,
            "calculated_at": m.calculated_at.isoformat(),
        }
        for m in metrics
    ]


@router.get("/api/metrics/{ticker}")
async def get_metric(ticker: str, db: IMetricRepository = Depends(get_db)):
    metric = db.get_metric_by_ticker(ticker)
    if not metric:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    return {
        "ticker": metric.ticker,
        "current_price": metric.current_price,
        "volume": metric.volume,
        "beta": metric.beta,
        "alpha": metric.alpha,
        "sharpe": metric.sharpe,
        "capm": metric.capm,
        "r_squared": metric.r_squared,
        "p_value": metric.p_value,
        "risk_free_rate": metric.risk_free_rate,
        "risk_free_source": metric.risk_free_source,
        "market_return": metric.market_return,
        "active": metric.active,
        "calculated_at": metric.calculated_at.isoformat(),
    }


@router.delete("/api/metrics/{ticker}")
@limiter.limit("5/minute")
async def delete_metric(
    ticker: str, request: Request, db: IMetricRepository = Depends(get_db)
):
    verify_api_key(request)
    success = db.delete_metric(ticker)
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    return {"status": "deleted", "ticker": ticker.upper()}


@router.patch("/api/metrics/{ticker}/active")
@limiter.limit("10/minute")
async def toggle_ticker_active(
    ticker: str, request: Request, db: IMetricRepository = Depends(get_db)
):
    verify_api_key(request)
    body = await request.json()
    active = body.get("active", True)

    success = db.toggle_active(ticker.upper(), active)
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    return {"ticker": ticker.upper(), "active": active, "status": "updated"}


@router.get("/api/tickers")
async def list_tickers(
    active_only: bool = True, db: IMetricRepository = Depends(get_db)
):
    metrics = db.get_all_metrics(active_only=active_only)
    return [
        {
            "ticker": m.ticker,
            "active": m.active,
            "current_price": m.current_price,
            "beta": m.beta,
            "sharpe": m.sharpe,
        }
        for m in metrics
    ]


@router.get("/api/sync/status")
async def sync_status(sync_service: SyncService = Depends(get_sync_service)):
    return sync_service.get_sync_status()


@router.get("/api/config")
async def get_config():
    return {
        "market_ticker": settings.market_ticker,
        "data_period": settings.data_period,
        "beta_method": settings.beta_method,
        "beta_buy_threshold": settings.beta_buy_threshold,
        "beta_sell_threshold": settings.beta_sell_threshold,
        "alpha_buy_threshold": settings.alpha_buy_threshold,
        "sharpe_buy_threshold": settings.sharpe_buy_threshold,
    }
