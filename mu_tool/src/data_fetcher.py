"""Market data fetching via yfinance."""
import warnings
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional

warnings.filterwarnings("ignore")

RISK_FREE_RATE = 0.053  # approximate 3-month T-bill


def get_stock_info(ticker: str) -> dict:
    """Fetch current price and basic info."""
    t = yf.Ticker(ticker)
    hist = t.history(period="5d")
    if hist.empty:
        return {}
    price = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
    return {
        "ticker": ticker,
        "price": price,
        "prev_close": prev,
        "change_pct": (price - prev) / prev * 100,
    }


def get_options_chain(ticker: str, target_expiries: list[str]) -> dict:
    """
    Fetch options chain for specific expiry dates.
    Returns dict keyed by expiry date string.
    """
    t = yf.Ticker(ticker)
    available = t.options  # tuple of expiry strings (YYYY-MM-DD)
    result = {}
    for exp in target_expiries:
        if exp in available:
            chain = t.option_chain(exp)
            result[exp] = {
                "calls": chain.calls.copy(),
                "puts": chain.puts.copy(),
            }
    return result


def get_all_options(ticker: str) -> dict:
    """Fetch all available options chains."""
    t = yf.Ticker(ticker)
    result = {}
    for exp in t.options:
        try:
            chain = t.option_chain(exp)
            result[exp] = {
                "calls": chain.calls.copy(),
                "puts": chain.puts.copy(),
            }
        except Exception:
            continue
    return result


def get_historical_prices(
    ticker: str, period: str = "2y", interval: str = "1d"
) -> pd.DataFrame:
    """Fetch historical OHLCV data."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def get_historical_hv(ticker: str, window: int = 30, period: str = "2y") -> pd.Series:
    """Calculate rolling historical volatility (annualized)."""
    df = get_historical_prices(ticker, period=period)
    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    hv = log_returns.rolling(window).std() * np.sqrt(252)
    return hv.dropna()


def get_beta(ticker: str, benchmark: str = "SOXX", period: str = "1y") -> float:
    """Calculate beta of ticker vs benchmark."""
    t_data = get_historical_prices(ticker, period=period)
    b_data = get_historical_prices(benchmark, period=period)
    t_ret = np.log(t_data["Close"] / t_data["Close"].shift(1)).dropna()
    b_ret = np.log(b_data["Close"] / b_data["Close"].shift(1)).dropna()
    common = t_ret.index.intersection(b_ret.index)
    if len(common) < 20:
        return 1.5
    cov = np.cov(t_ret.loc[common], b_ret.loc[common])
    return float(cov[0, 1] / cov[1, 1])


def get_nearest_expiry(ticker: str, target_date: str) -> Optional[str]:
    """Find nearest available expiry to target date."""
    t = yf.Ticker(ticker)
    available = list(t.options)
    if not available:
        return None
    target = datetime.strptime(target_date, "%Y-%m-%d")
    diffs = {exp: abs((datetime.strptime(exp, "%Y-%m-%d") - target).days) for exp in available}
    return min(diffs, key=diffs.get)


def get_all_expiries(ticker: str) -> list[str]:
    """Get list of all available expiry dates."""
    return list(yf.Ticker(ticker).options)


def days_to_expiry(expiry: str) -> float:
    """Calendar days from today to expiry."""
    exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
    return max((exp_dt - datetime.today()).days, 0)


def trading_days_to_expiry(expiry: str) -> float:
    """Approximate trading days to expiry."""
    cal_days = days_to_expiry(expiry)
    return cal_days * 252 / 365
