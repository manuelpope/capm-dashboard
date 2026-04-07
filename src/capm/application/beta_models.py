from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from arch import arch_model


@dataclass
class BetaResult:
    beta: float
    r_squared: float
    p_value: float
    std_error: float
    alpha: float


class BetaCalculator(ABC):
    name: str = "base"

    @abstractmethod
    def calculate(
        self, asset_returns: pd.Series, market_returns: pd.Series
    ) -> BetaResult:
        pass


class OLSBeta(BetaCalculator):
    name: str = "ols"

    def calculate(
        self, asset_returns: pd.Series, market_returns: pd.Series
    ) -> BetaResult:
        aligned = pd.DataFrame(
            {"asset": asset_returns, "market": market_returns}
        ).dropna()
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            aligned["market"], aligned["asset"]
        )
        return BetaResult(
            beta=round(slope, 4),
            r_squared=round(r_value**2, 4),
            p_value=round(p_value, 6),
            std_error=round(std_err, 4),
            alpha=round(intercept, 4),
        )


class GARCHBeta(BetaCalculator):
    name: str = "garch"

    def __init__(self, p: int = 1, q: int = 1):
        self.p = p
        self.q = q

    def calculate(
        self, asset_returns: pd.Series, market_returns: pd.Series
    ) -> BetaResult:
        aligned = pd.DataFrame(
            {"asset": asset_returns, "market": market_returns}
        ).dropna()
        ols_result = stats.linregress(aligned["market"], aligned["asset"])
        residuals = aligned["asset"] - (
            ols_result.slope * aligned["market"] + ols_result.intercept
        )
        market_residuals = aligned["market"] - aligned["market"].mean()

        try:
            garch = arch_model(
                market_residuals,
                vol="Garch",
                p=self.p,
                q=self.q,
                mean="Zero",
                dist="normal",
            )
            garch_fit = garch.fit(disp="off")
            conditional_vol = garch_fit.conditional_volatility
            weights = 1 / (conditional_vol**2 + 1e-6)
        except Exception:
            weights = np.ones(len(aligned))

        X = aligned["market"].values
        y = aligned["asset"].values
        Xw = X * np.sqrt(weights)
        yw = y * np.sqrt(weights)

        Xw_mean = np.mean(Xw)
        yw_mean = np.mean(yw)

        numerator = np.sum((Xw - Xw_mean) * (yw - yw_mean))
        denominator = np.sum((Xw - Xw_mean) ** 2)

        beta_garch = numerator / denominator
        alpha_garch = yw_mean - beta_garch * Xw_mean

        y_pred = beta_garch * X + alpha_garch
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - yw_mean) ** 2)
        r_squared_garch = 1 - (ss_res / ss_tot)

        n = len(X)
        std_error_garch = np.sqrt(ss_res / (n - 2)) / np.sqrt(
            np.sum((X - X.mean()) ** 2)
        )

        n_obs = len(aligned)
        dof = n_obs - 2
        t_stat = beta_garch / std_error_garch if std_error_garch != 0 else 0
        p_value_garch = 2 * (1 - stats.t.cdf(abs(t_stat), dof))

        return BetaResult(
            beta=round(beta_garch, 4),
            r_squared=round(r_squared_garch, 4),
            p_value=round(p_value_garch, 6),
            std_error=round(std_error_garch, 4),
            alpha=round(alpha_garch, 4),
        )
