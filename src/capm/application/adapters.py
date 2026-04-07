import yfinance as yf
import pandas as pd
import numpy as np
from typing import Any


class YahooDataAdapter:
    @staticmethod
    def clean_price(value: Any) -> float | None:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def clean_volume(value: Any) -> int | None:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def clean_series(series: pd.Series) -> pd.Series:
        return series.dropna()

    @staticmethod
    def validate_price_data(prices: pd.Series, min_periods: int = 30) -> bool:
        cleaned = YahooDataAdapter.clean_series(prices)
        return len(cleaned) >= min_periods and cleaned.last_valid_index() is not None

    @staticmethod
    def get_latest_price(prices: pd.Series) -> float | None:
        cleaned = YahooDataAdapter.clean_series(prices)
        if cleaned.empty:
            return None
        return YahooDataAdapter.clean_price(cleaned.iloc[-1])

    @staticmethod
    def get_latest_volume(volume: pd.Series) -> int | None:
        cleaned = YahooDataAdapter.clean_series(volume)
        if cleaned.empty:
            return None
        return YahooDataAdapter.clean_volume(cleaned.iloc[-1])
