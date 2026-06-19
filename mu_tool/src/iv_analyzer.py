"""IV analysis: ATM IV extraction, IV crush estimation, term structure."""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional
from .bs_model import implied_vol, RISK_FREE_RATE
from .data_fetcher import days_to_expiry, trading_days_to_expiry

# Re-export for convenience
RISK_FREE = RISK_FREE_RATE


def get_atm_iv(chain: dict, spot: float, expiry: str) -> dict:
    """
    Extract ATM implied volatility from calls and puts.
    Returns dict with call_iv, put_iv, avg_iv, atm_strike.
    """
    T = trading_days_to_expiry(expiry) / 252
    if T <= 0:
        return {"call_iv": np.nan, "put_iv": np.nan, "avg_iv": np.nan, "atm_strike": spot}

    calls = chain["calls"].copy()
    puts = chain["puts"].copy()

    # Find ATM strike (closest to spot)
    calls["dist"] = (calls["strike"] - spot).abs()
    puts["dist"] = (puts["strike"] - spot).abs()
    atm_strike = float(calls.loc[calls["dist"].idxmin(), "strike"])

    c_row = calls.loc[calls["strike"] == atm_strike]
    p_row = puts.loc[puts["strike"] == atm_strike]

    c_iv = float(c_row["impliedVolatility"].iloc[0]) if not c_row.empty else np.nan
    p_iv = float(p_row["impliedVolatility"].iloc[0]) if not p_row.empty else np.nan

    # If yfinance IV seems unreliable, recalculate from mid price
    if c_row.empty or np.isnan(c_iv):
        c_iv = np.nan
    if p_row.empty or np.isnan(p_iv):
        p_iv = np.nan

    avg_iv = np.nanmean([c_iv, p_iv])
    return {
        "call_iv": c_iv,
        "put_iv": p_iv,
        "avg_iv": avg_iv,
        "atm_strike": atm_strike,
        "T": T,
    }


def get_atm_straddle_iv(chain: dict, spot: float, expiry: str) -> float:
    """Derive implied vol from the ATM straddle mid price (more robust)."""
    T = trading_days_to_expiry(expiry) / 252
    if T <= 0:
        return np.nan

    calls = chain["calls"].copy()
    puts = chain["puts"].copy()
    calls["dist"] = (calls["strike"] - spot).abs()
    puts["dist"] = (puts["strike"] - spot).abs()
    atm_strike = float(calls.loc[calls["dist"].idxmin(), "strike"])

    c_row = calls.loc[calls["strike"] == atm_strike].iloc[0] if not calls.loc[calls["strike"] == atm_strike].empty else None
    p_row = puts.loc[puts["strike"] == atm_strike].iloc[0] if not puts.loc[puts["strike"] == atm_strike].empty else None

    if c_row is None or p_row is None:
        return np.nan

    c_mid = (c_row["bid"] + c_row["ask"]) / 2 if c_row["ask"] > 0 else c_row["lastPrice"]
    p_mid = (p_row["bid"] + p_row["ask"]) / 2 if p_row["ask"] > 0 else p_row["lastPrice"]
    straddle_price = c_mid + p_mid
    implied_move = straddle_price / spot

    # Convert straddle implied move to approximate ATM IV
    # For ATM straddle: price ≈ 2 * C_ATM ≈ spot * sigma * sqrt(T) * sqrt(2/pi)
    if T > 0:
        approx_sigma = implied_move / (np.sqrt(2 / np.pi) * np.sqrt(T))
    else:
        approx_sigma = np.nan

    return float(approx_sigma)


def compute_implied_move(chain: dict, spot: float, expiry: str) -> float:
    """ATM straddle price / spot → expected ±move fraction."""
    calls = chain["calls"].copy()
    puts = chain["puts"].copy()
    calls["dist"] = (calls["strike"] - spot).abs()
    puts["dist"] = (puts["strike"] - spot).abs()
    atm_c_strike = float(calls.loc[calls["dist"].idxmin(), "strike"])
    atm_p_strike = float(puts.loc[puts["dist"].idxmin(), "strike"])

    c_row = calls.loc[calls["strike"] == atm_c_strike]
    p_row = puts.loc[puts["strike"] == atm_p_strike]
    if c_row.empty or p_row.empty:
        return np.nan

    c = c_row.iloc[0]
    p = p_row.iloc[0]
    c_mid = (c["bid"] + c["ask"]) / 2 if c["ask"] > 0 else c["lastPrice"]
    p_mid = (p["bid"] + p["ask"]) / 2 if p["ask"] > 0 else p["lastPrice"]
    return (c_mid + p_mid) / spot


def compute_term_structure(chains: dict, spot: float) -> pd.DataFrame:
    """
    Compute ATM IV across expiry dates.
    Returns DataFrame sorted by expiry with IV and implied move.
    """
    rows = []
    for expiry, chain in sorted(chains.items()):
        dte = days_to_expiry(expiry)
        if dte < 1:
            continue
        atm = get_atm_iv(chain, spot, expiry)
        im = compute_implied_move(chain, spot, expiry)
        rows.append({
            "expiry": expiry,
            "dte": dte,
            "atm_iv": atm["avg_iv"],
            "call_iv": atm["call_iv"],
            "put_iv": atm["put_iv"],
            "implied_move": im,
            "atm_strike": atm["atm_strike"],
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("dte").reset_index(drop=True)
    return df


def analyze_term_structure(ts_df: pd.DataFrame) -> dict:
    """
    Classify term structure shape and derive signals.
    Uses first 3 expiry points if available.
    """
    if ts_df.empty or len(ts_df) < 2:
        return {"signal": "INSUFFICIENT_DATA", "shape": "unknown"}

    rows = ts_df.dropna(subset=["atm_iv"]).head(4)
    if len(rows) < 2:
        return {"signal": "INSUFFICIENT_DATA", "shape": "unknown"}

    ivs = rows["atm_iv"].values
    dtes = rows["dte"].values
    expiries = rows["expiry"].values.tolist()

    # Slope between consecutive expiries
    slope_12 = ivs[0] - ivs[1] if len(ivs) > 1 else 0
    slope_23 = ivs[1] - ivs[2] if len(ivs) > 2 else 0

    # Classify structure
    if slope_12 > 0.15:
        shape = "STEEP_BACKWARDATION"
        interpretation = "강한 이벤트 프리미엄 집중 — IV crush 위험 최대"
    elif slope_12 > 0.05:
        shape = "MILD_BACKWARDATION"
        interpretation = "일반적 실적 이벤트 구조 — 단기 변동성 집중"
    elif slope_12 > -0.05:
        shape = "FLAT"
        interpretation = "이벤트 이후도 불확실성 지속 — 방향성 재평가 가능"
    else:
        shape = "CONTANGO"
        interpretation = "구조적 수요/추세 이벤트 가능 — buy the news 가능"

    # Signal for earnings trade
    if shape == "STEEP_BACKWARDATION":
        signal = "SELL_VOL"
        premium_risk = "극도 위험"
    elif shape == "MILD_BACKWARDATION":
        signal = "CAUTION_LONG_VOL"
        premium_risk = "주의 필요"
    else:
        signal = "NEUTRAL_TO_LONG_VOL"
        premium_risk = "낮음"

    result = {
        "shape": shape,
        "signal": signal,
        "premium_risk": premium_risk,
        "interpretation": interpretation,
        "slope_short": slope_12,
        "slope_mid": slope_23,
        "expiries": expiries[:3],
        "ivs": ivs[:3].tolist(),
    }
    return result


def estimate_iv_crush(
    pre_earnings_iv: float,
    hist_avg_crush_pct: float = 0.38,
) -> dict:
    """
    Estimate post-announcement IV from historical crush ratio.
    Default 38% crush based on MU historical average.
    """
    estimated_post_iv = pre_earnings_iv * (1 - hist_avg_crush_pct)
    crush_abs = pre_earnings_iv - estimated_post_iv
    return {
        "pre_iv": pre_earnings_iv,
        "estimated_post_iv": estimated_post_iv,
        "crush_abs": crush_abs,
        "crush_pct": hist_avg_crush_pct * 100,
        "label": _crush_label(crush_abs),
    }


def _crush_label(crush_pct_abs: float) -> str:
    if crush_pct_abs >= 0.50:
        return "EXTREME crush — straddle 매수 매우 불리"
    elif crush_pct_abs >= 0.35:
        return "HIGH crush — 방향 맞아도 손익 불확실"
    elif crush_pct_abs >= 0.20:
        return "MODERATE crush — 보통 수준"
    else:
        return "LOW crush — long option 부담 낮음"
