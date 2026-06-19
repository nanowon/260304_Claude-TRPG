"""Open Interest analysis: OI changes, max pain, positioning."""
import numpy as np
import pandas as pd
from .data_fetcher import days_to_expiry


def compute_max_pain(chain: dict, spot: float) -> dict:
    """
    Max pain = strike where total option holder loss is maximized
    (equivalent to minimum payout by writers at expiry).
    """
    calls = chain["calls"].copy()
    puts = chain["puts"].copy()

    all_strikes = sorted(set(calls["strike"]).union(set(puts["strike"])))

    pain = []
    for S in all_strikes:
        c_pain = calls.apply(
            lambda r: r["openInterest"] * max(S - r["strike"], 0), axis=1
        ).sum()
        p_pain = puts.apply(
            lambda r: r["openInterest"] * max(r["strike"] - S, 0), axis=1
        ).sum()
        pain.append({"strike": S, "total_pain": c_pain + p_pain})

    pain_df = pd.DataFrame(pain)
    if pain_df.empty:
        return {"max_pain": spot, "distance_pct": 0.0}

    max_pain_strike = float(pain_df.loc[pain_df["total_pain"].idxmin(), "strike"])
    distance = (max_pain_strike - spot) / spot * 100
    return {
        "max_pain": max_pain_strike,
        "distance_pct": distance,
        "direction": "above" if max_pain_strike > spot else "below",
        "signal": _max_pain_signal(distance),
    }


def _max_pain_signal(dist_pct: float) -> str:
    if dist_pct < -5:
        return "강한 하방 pinning 압력"
    elif dist_pct < -2:
        return "하방 pinning 가능"
    elif dist_pct > 5:
        return "상방 pinning 압력"
    elif dist_pct > 2:
        return "상방 pinning 가능"
    else:
        return "현재가 근처 — pinning 중립"


def analyze_oi_structure(chain: dict, spot: float, expiry: str) -> dict:
    """
    Analyze OI distribution:
    - Call/Put OI ratio
    - OI concentration (ATM vs OTM)
    - Deep OTM call OI (gamma squeeze potential)
    """
    calls = chain["calls"].copy()
    puts = chain["puts"].copy()

    total_call_oi = calls["openInterest"].sum()
    total_put_oi = puts["openInterest"].sum()
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else np.nan

    # ATM band: within 5% of spot
    atm_band = spot * 0.05
    atm_calls = calls[calls["strike"].between(spot - atm_band, spot + atm_band)]["openInterest"].sum()
    atm_puts = puts[puts["strike"].between(spot - atm_band, spot + atm_band)]["openInterest"].sum()

    # Deep OTM calls: >15% above spot
    otm_call_threshold = spot * 1.15
    deep_otm_calls = calls[calls["strike"] > otm_call_threshold]["openInterest"].sum()

    # Deep OTM puts: >15% below spot
    otm_put_threshold = spot * 0.85
    deep_otm_puts = puts[puts["strike"] < otm_put_threshold]["openInterest"].sum()

    # Positioning signal
    signal, label = _oi_signal(pcr, total_call_oi, total_put_oi, deep_otm_calls, deep_otm_puts)

    return {
        "total_call_oi": int(total_call_oi),
        "total_put_oi": int(total_put_oi),
        "put_call_ratio": pcr,
        "atm_call_oi": int(atm_calls),
        "atm_put_oi": int(atm_puts),
        "deep_otm_call_oi": int(deep_otm_calls),
        "deep_otm_put_oi": int(deep_otm_puts),
        "signal": signal,
        "label": label,
    }


def _oi_signal(pcr, call_oi, put_oi, deep_otm_calls, deep_otm_puts) -> tuple:
    if pcr < 0.5 and deep_otm_calls > deep_otm_puts * 2:
        return "CROWDED_LONG", "콜 OI 과도 집중 — sell in news 위험"
    elif pcr < 0.5:
        return "CALL_DOMINANT", "콜 OI 우위 — 상방 기대감"
    elif pcr > 1.5:
        return "PUT_DOMINANT", "풋 OI 우위 — 헤지 수요 / 안도 랠리 가능"
    elif pcr > 1.0:
        return "MILD_PUT_BIAS", "약한 풋 우위 — 방어적 포지셔닝"
    else:
        return "NEUTRAL", "균형 포지셔닝"


def get_oi_summary(chains: dict, spot: float) -> dict:
    """Multi-expiry OI summary for the most relevant expirations."""
    results = {}
    for expiry, chain in chains.items():
        dte = days_to_expiry(expiry)
        if 0 < dte <= 90:
            results[expiry] = analyze_oi_structure(chain, spot, expiry)
    return results


def estimate_dealer_gamma(chain: dict, spot: float, expiry: str) -> dict:
    """
    Rough dealer gamma estimate (GEX proxy).
    Assumes dealers are short calls (hedged long) and long puts (hedged short).
    Positive GEX = market stabilizing. Negative GEX = volatile/trending.
    """
    from .bs_model import bs_delta
    from .data_fetcher import trading_days_to_expiry
    from .bs_model import RISK_FREE_RATE

    T = trading_days_to_expiry(expiry) / 252
    if T <= 0:
        return {"gex": 0, "signal": "NEUTRAL"}

    calls = chain["calls"].copy()
    puts = chain["puts"].copy()

    def gamma_approx(K, sigma, S=spot, T=T, r=RISK_FREE_RATE):
        from scipy.stats import norm
        if sigma <= 0 or T <= 0:
            return 0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    call_gex = 0
    for _, row in calls.iterrows():
        if row["impliedVolatility"] > 0.01 and row["openInterest"] > 0:
            g = gamma_approx(row["strike"], row["impliedVolatility"])
            call_gex += g * row["openInterest"] * 100 * spot

    put_gex = 0
    for _, row in puts.iterrows():
        if row["impliedVolatility"] > 0.01 and row["openInterest"] > 0:
            g = gamma_approx(row["strike"], row["impliedVolatility"])
            put_gex += g * row["openInterest"] * 100 * spot

    # Dealers: short calls (negative GEX) + long puts (positive GEX) if market is hedged
    net_gex = call_gex - put_gex
    return {
        "call_gex": call_gex,
        "put_gex": put_gex,
        "net_gex": net_gex,
        "signal": "STABILIZING" if net_gex > 0 else "TRENDING/VOLATILE",
    }
