from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    secret_trigger_key: str = Field(..., min_length=8)
    market_ticker: str = "^GSPC"
    risk_free_rate: float = 0.0
    db_path: str = "capm.db"
    env_mode: str = "development"
    default_tickers: str = "AAPL,MSFT,AMZN,GOOGL,META,NVDA,JPM,JNJ,WMT,XOM"
    beta_method: str = "ols"
    data_period: str = "2y"
    beta_buy_threshold: float = 0.7
    beta_sell_threshold: float = 1.3
    alpha_buy_threshold: float = 0.0
    sharpe_buy_threshold: float = 1.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
