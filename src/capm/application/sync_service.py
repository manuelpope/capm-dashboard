import pandas as pd
from datetime import datetime
from typing import Optional

from src.capm.config import settings
from src.capm.domain.interfaces import IMetricRepository


def needs_sync(last_calculation: Optional[object]) -> bool:
    if not last_calculation:
        return True
    last_date = last_calculation.calculated_at
    last_business_day = pd.offsets.BDay().rollback(pd.Timestamp.utcnow())
    return last_date.date() < last_business_day.date()


def get_default_tickers() -> list[str]:
    return [t.strip() for t in settings.default_tickers.split(",")]


class SyncService:
    _sync_in_progress: bool = False

    def __init__(self, repository: IMetricRepository):
        self._repository = repository

    def needs_sync(self) -> bool:
        latest = self._repository.get_latest_calculation()
        return needs_sync(latest)

    def run_sync(self, tickers: Optional[list[str]] = None) -> dict:
        if SyncService._sync_in_progress:
            return {"status": "already_running"}

        SyncService._sync_in_progress = True
        try:
            from src.capm.application.engine import FinancialEngine

            tickers = tickers or get_default_tickers()
            engine = FinancialEngine()
            metrics = engine.calculate_metrics(tickers)
            self._repository.upsert_metrics(metrics)

            return {
                "status": "ok",
                "calculated": len(metrics),
                "tickers": tickers,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            SyncService._sync_in_progress = False

    def get_sync_status(self) -> dict:
        latest = self._repository.get_latest_calculation()
        return {
            "in_progress": SyncService._sync_in_progress,
            "needs_sync": self.needs_sync(),
            "last_calculation": latest.calculated_at.isoformat() if latest else None,
        }
