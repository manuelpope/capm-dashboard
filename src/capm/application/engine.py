import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

from src.capm.config import settings
from src.capm.application.beta_models import OLSBeta, GARCHBeta, BetaResult
from src.capm.application.adapters import YahooDataAdapter


def get_beta_calculator():
    method = settings.beta_method.lower()
    if method == "garch":
        return GARCHBeta()
    return OLSBeta()


class FinancialEngine:
    def __init__(self):
        self.beta_calculator = get_beta_calculator()
        self.market_ticker = settings.market_ticker
        self.data_period = settings.data_period
        self.risk_free_rate = self._fetch_risk_free_rate()
        self.risk_free_source = "^TNX (US Treasury 10Y)"

    def _fetch_risk_free_rate(self) -> float:
        try:
            treasury = yf.Ticker("^TNX")
            hist = treasury.history(period="5d")
            if not hist.empty:
                rate = hist["Close"].iloc[-1] / 100
                return float(rate)
        except Exception as e:
            print(f"Could not fetch Treasury rate: {e}")
        return 0.0

    def download_data(
        self, tickers: list[str], period: str = "2y"
    ) -> dict[str, pd.DataFrame]:
        data = {}
        all_tickers = list(set(tickers + [self.market_ticker]))
        for ticker in all_tickers:
            ticker_data = yf.Ticker(ticker)
            hist = ticker_data.history(period=period)
            if hist.empty:
                raise ValueError(f"No data for ticker {ticker}")
            data[ticker] = hist
        return data

    @staticmethod
    def log_returns(prices: pd.Series) -> pd.Series:
        return np.log(prices / prices.shift(1)).dropna()

    def calculate_metrics(self, tickers: list[str], period: str = "2y") -> list[dict]:
        data = self.download_data(tickers, period)
        market_prices = data[self.market_ticker]["Close"]
        market_returns = self.log_returns(market_prices)

        results = []
        valid_tickers = [t for t in tickers if t != self.market_ticker and t in data]

        for ticker in valid_tickers:
            asset_prices = data[ticker]["Close"]
            asset_returns = self.log_returns(asset_prices)

            if not YahooDataAdapter.validate_price_data(asset_prices):
                print(f"Skipping {ticker}: insufficient price data")
                continue

            beta_result = self.beta_calculator.calculate(asset_returns, market_returns)

            market_mean_return = market_returns.mean() * 252
            capm = self.risk_free_rate + beta_result.beta * (
                market_mean_return - self.risk_free_rate
            )

            asset_std_daily = asset_returns.std()
            asset_std_annualized = asset_std_daily * np.sqrt(252)
            sharpe = (
                (capm - self.risk_free_rate) / asset_std_annualized
                if asset_std_annualized > 0
                else 0
            )

            current_price = YahooDataAdapter.get_latest_price(asset_prices)
            volume = YahooDataAdapter.get_latest_volume(data[ticker]["Volume"])

            if current_price is None or volume is None:
                print(f"Skipping {ticker}: could not fetch price or volume")
                continue

            results.append(
                {
                    "ticker": ticker,
                    "market_ticker": self.market_ticker,
                    "current_price": current_price,
                    "volume": volume,
                    "beta": float(beta_result.beta),
                    "alpha": float(beta_result.alpha),
                    "capm": float(round(capm, 4)),
                    "sharpe": float(round(sharpe, 4)),
                    "r_squared": float(beta_result.r_squared),
                    "p_value": float(beta_result.p_value),
                    "std_error": float(beta_result.std_error),
                    "risk_free_rate": float(self.risk_free_rate),
                    "risk_free_source": self.risk_free_source,
                    "market_return": float(round(market_mean_return, 4)),
                    "calculated_at": datetime.utcnow(),
                }
            )

        return results
