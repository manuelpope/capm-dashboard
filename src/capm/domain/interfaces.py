from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol


class MetricData(Protocol):
    id: int
    ticker: str
    market_ticker: str
    current_price: float | None
    volume: int | None
    beta: float
    alpha: float
    capm: float
    sharpe: float
    r_squared: float
    p_value: float
    std_error: float
    risk_free_rate: float
    risk_free_source: str | None
    market_return: float
    calculated_at: datetime
    active: bool


class IMetricRepository(ABC):
    @abstractmethod
    def upsert_metrics(self, metrics: list[dict]) -> None: ...

    @abstractmethod
    def get_all_metrics(self, active_only: bool = True) -> list[MetricData]: ...

    @abstractmethod
    def get_metric_by_ticker(self, ticker: str) -> MetricData | None: ...

    @abstractmethod
    def get_latest_calculation(self) -> MetricData | None: ...

    @abstractmethod
    def get_active_tickers(self) -> list[str]: ...

    @abstractmethod
    def toggle_active(self, ticker: str, active: bool) -> bool: ...

    @abstractmethod
    def delete_metric(self, ticker: str) -> bool: ...
