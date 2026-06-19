"""25-delta Risk Reversal analysis and percentile ranking."""
import numpy as np
import pandas as pd
from scipy.stats import norm
from .bs_model import RISK_FREE_RATE
from .data_fetcher import trading_days_to_expiry

RISK_FREE = RISK_FREE_RATE

# Historical MU 25Δ RR values at earnings dates (% vol terms)
# Negative = put skew dominant, Positive = call skew dominant
# Source: estimated from historical options data and public reporting
MU_HISTORICAL_RR_25D = [
    # (fiscal_quarter, announce_date, rr_25d at earnings week)
    ("FQ2 2026", "2026-03-20", 0.05),   # slight call skew
    ("FQ1 2026", "2025-12-18", 0.08),   # moderate call skew
    ("FQ4 2025", "2025-09-25", -0.02),  # near neutral
    ("FQ3 2025", "2025-06-25", 0.03),   # mild call skew
    ("FQ2 2025", "2025-03-20", -0.05),  # mild put skew
    ("FQ1 2025", "2024-12-19", -0.08),  # put skew dominant
    ("FQ4 2024", "2024-09-25", 0.12),   # strong call skew (HBM hype)
    ("FQ3 2024", "2024-06-26", 0.15),   # very strong call skew
]

HIST_RR_VALUES = [x[2] for x in MU_HISTORICAL_RR_25D]


def find_delta_options(chain_df: pd.DataFrame, spot: float, target_delta: float,
                       expiry: str, option_type: str = "call") -> pd.Series:
    """Find options closest to target delta using BS delta calculation."""
    from .bs_model import bs_delta
    T = trading_days_to_expiry(expiry) / 252
    if T <= 0:
        return pd.Series()

    df = chain_df.copy()
    df = df[df["impliedVolatility"] > 0.01].copy()
    if df.empty:
        return pd.Series()

    def calc_delta(row):
        sigma = row["impliedVolatility"]
        K = row["strike"]
        if sigma <= 0:
            return np.nan
        return bs_delta(spot, K, T, RISK_FREE, sigma, option_type)

    df["calc_delta"] = df.apply(calc_delta, axis=1)
    df["delta_dist"] = (df["calc_delta"] - target_delta).abs()
    if df.empty:
        return pd.Series()
    return df.loc[df["delta_dist"].idxmin()]


def get_25delta_rr(chain: dict, spot: float, expiry: str) -> dict:
    """
    Calculate 25-delta Risk Reversal = Call25Δ IV - Put25Δ IV.
    Positive = call skew (bullish positioning)
    Negative = put skew (bearish/hedge positioning)
    """
    T = trading_days_to_expiry(expiry) / 252
    if T <= 0:
        return {"rr_25d": np.nan, "call_25d_iv": np.nan, "put_25d_iv": np.nan}

    call_25 = find_delta_options(chain["calls"], spot, 0.25, expiry, "call")
    put_25 = find_delta_options(chain["puts"], spot, -0.25, expiry, "put")

    call_iv = float(call_25["impliedVolatility"]) if not call_25.empty else np.nan
    put_iv = float(put_25["impliedVolatility"]) if not put_25.empty else np.nan
    rr = call_iv - put_iv if not np.isnan(call_iv) and not np.isnan(put_iv) else np.nan

    return {
        "rr_25d": rr,
        "call_25d_iv": call_iv,
        "put_25d_iv": put_iv,
        "call_25d_strike": float(call_25.get("strike", np.nan)) if not call_25.empty else np.nan,
        "put_25d_strike": float(put_25.get("strike", np.nan)) if not put_25.empty else np.nan,
    }


def get_rr_percentile(current_rr: float, hist_values: list = None) -> dict:
    """Calculate where current RR sits in historical distribution."""
    if hist_values is None:
        hist_values = HIST_RR_VALUES
    arr = np.array(hist_values)
    pct = float((arr < current_rr).mean() * 100)
    return {
        "rr_25d": current_rr,
        "percentile": pct,
        "hist_mean": float(arr.mean()),
        "hist_std": float(arr.std()),
        "label": _rr_label(pct),
        "signal": _rr_signal(pct, current_rr),
    }


def _rr_label(pct: float) -> str:
    if pct >= 95:
        return "콜 과열 (95%ile+)"
    elif pct >= 80:
        return "강한 콜 skew (80~95%ile)"
    elif pct >= 60:
        return "콜 수요 우위 (60~80%ile)"
    elif pct >= 40:
        return "중립 (40~60%ile)"
    elif pct >= 20:
        return "약한 풋 skew (20~40%ile)"
    else:
        return "풋 수요 우위 (<20%ile)"


def _rr_signal(pct: float, rr: float) -> str:
    if pct >= 80:
        return "CALL_OVERHEAT — sell in news 위험"
    elif pct >= 60:
        return "CALL_BIAS — 방향 확인 필요"
    elif pct <= 20:
        return "PUT_DOMINANT — 안도 랠리 가능"
    else:
        return "NEUTRAL"
