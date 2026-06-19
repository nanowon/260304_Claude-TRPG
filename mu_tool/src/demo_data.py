"""
Demo/offline mode: realistic MU data for FQ3 2026 earnings (2026-06-24).
Based on user-provided context:
- MU price: ~$143 (estimated 2026 range)
- Expected move: ~18-20% (Options AI: 17.9%, other sources: ~20%)
- SOXX: ~$265
- ATM IV for 7-DTE weekly (~163%) to produce 18% straddle move

Straddle approximation: IM ≈ S * IV_ATM * sqrt(2T/π)
For T=7/365, IM=18%: IV_ATM ≈ 18% / (143 * sqrt(2*7/365/π)) * 143 ≈ 163%
"""
import numpy as np
import pandas as pd

MU_DEMO = {
    "ticker": "MU",
    "price": 143.0,
    "prev_close": 140.5,
    "change_pct": 1.78,
}

SOXX_DEMO = {
    "ticker": "SOXX",
    "price": 265.0,
    "prev_close": 263.0,
    "change_pct": 0.76,
}

MU_BETA_DEMO = 1.52


def _call(strike, iv, bid, ask, oi):
    return {"strike": float(strike), "impliedVolatility": float(iv),
            "bid": float(bid), "ask": float(ask),
            "lastPrice": float((bid + ask) / 2),
            "openInterest": int(oi), "volume": int(oi // 3)}


def _put(strike, iv, bid, ask, oi):
    return {"strike": float(strike), "impliedVolatility": float(iv),
            "bid": float(bid), "ask": float(ask),
            "lastPrice": float((bid + ask) / 2),
            "openInterest": int(oi), "volume": int(oi // 3)}


def build_demo_chains():
    """
    Build realistic demo options chain for MU.

    Weekly 2026-06-27 (7 DTE):
      ATM IV ~163% → straddle ~$25.7 → IM ≈ 18% of $143
      Steep backwardation vs monthly.
      Slight call skew: RR ≈ +11% (calls > puts at 25Δ)

    Monthly 2026-07-18 (29 DTE):
      ATM IV ~80% → straddle ~$25.6 → IM ≈ 18% over 29 days

    Aug 2026-08-21 (63 DTE):
      ATM IV ~65% → straddle ~$33.5 → IM ≈ 23% over 63 days
    """
    # ── 2026-06-27 weekly (7 DTE, IV~163%) ──
    # ATM calls/puts at strike 143: ~$12.87 each (straddle ~$25.74 = 18%)
    # Call skew: OTM calls carry higher IV than OTM puts (bullish positioning)
    weekly_calls = pd.DataFrame([
        _call(115, 1.45, 28.5, 29.2,  600),
        _call(120, 1.50, 24.5, 25.2,  900),
        _call(125, 1.55, 20.5, 21.2, 1800),
        _call(130, 1.58, 16.8, 17.5, 3200),
        _call(135, 1.60, 13.2, 14.0, 5500),
        _call(140, 1.62,  9.5, 10.3, 9200),   # near ATM
        _call(143, 1.63, 12.5, 13.2, 13000),  # ATM ← straddle mid ~$12.87
        _call(145, 1.64, 11.2, 11.9, 10500),
        _call(150, 1.67,  7.8,  8.5,  7200),
        _call(155, 1.72,  5.0,  5.7,  4800),
        _call(160, 1.78,  3.0,  3.7,  3100),
        _call(165, 1.85,  1.7,  2.3,  1800),
        _call(170, 1.93,  0.9,  1.4,  1000),
        _call(175, 2.02,  0.4,  0.9,   550),
    ])
    weekly_puts = pd.DataFrame([
        _put(115, 2.00,  0.4,  0.9,   400),
        _put(120, 1.95,  0.8,  1.3,   650),
        _put(125, 1.88,  1.5,  2.1,  1100),
        _put(130, 1.78,  2.8,  3.5,  2600),
        _put(135, 1.70,  4.8,  5.5,  4800),
        _put(140, 1.65,  7.5,  8.2,  8500),   # near ATM
        _put(143, 1.52, 12.3, 13.1, 12500),   # ATM ← straddle mid ~$12.70
        _put(145, 1.48, 14.0, 14.8, 9800),
        _put(150, 1.42, 18.2, 19.0,  6200),
        _put(155, 1.35, 23.0, 23.8,  3500),
        _put(160, 1.28, 28.0, 28.8,  1900),
    ])

    # ── 2026-07-18 monthly (29 DTE, IV~80%) ──
    # ATM straddle: 143 * 0.80 * sqrt(2*29/365/pi) ≈ $25.6 → also ~18% IM
    monthly_calls = pd.DataFrame([
        _call(120, 0.68, 26.5, 27.2, 2200),
        _call(125, 0.70, 22.8, 23.5, 3500),
        _call(130, 0.72, 19.5, 20.2, 5000),
        _call(135, 0.74, 16.5, 17.2, 7500),
        _call(140, 0.77, 13.5, 14.2, 11000),
        _call(143, 0.80, 12.8, 13.5, 15200),  # ATM
        _call(145, 0.81, 11.5, 12.2, 12500),
        _call(150, 0.83,  8.8,  9.5,  8500),
        _call(155, 0.86,  6.5,  7.2,  5800),
        _call(160, 0.89,  4.5,  5.2,  3900),
        _call(165, 0.93,  3.0,  3.7,  2600),
        _call(170, 0.98,  1.9,  2.5,  1600),
        _call(175, 1.04,  1.1,  1.7,   900),
        _call(180, 1.10,  0.6,  1.1,   500),
    ])
    monthly_puts = pd.DataFrame([
        _put(120, 1.00,  0.8,  1.4, 1600),
        _put(125, 0.95,  1.5,  2.1, 2500),
        _put(130, 0.88,  2.8,  3.5, 4000),
        _put(135, 0.83,  4.8,  5.5, 6500),
        _put(140, 0.79,  7.5,  8.2, 9500),
        _put(143, 0.75, 11.8, 12.5, 14200),  # ATM
        _put(145, 0.73, 13.5, 14.2, 11000),
        _put(150, 0.70, 18.0, 18.7,  7000),
        _put(155, 0.67, 23.0, 23.7,  4300),
        _put(160, 0.65, 28.2, 28.9,  2700),
    ])

    # ── 2026-08-21 (63 DTE, IV~65%) ──
    # ATM straddle: 143 * 0.65 * sqrt(2*63/365/pi) ≈ $33.5 → ~23% IM
    aug_calls = pd.DataFrame([
        _call(125, 0.57, 25.0, 25.7, 1600),
        _call(130, 0.59, 21.5, 22.2, 2600),
        _call(135, 0.61, 18.0, 18.7, 4000),
        _call(140, 0.63, 15.0, 15.7, 6500),
        _call(143, 0.65, 13.2, 14.0, 9200),  # ATM
        _call(145, 0.65, 11.8, 12.5, 7900),
        _call(150, 0.67,  8.8,  9.5, 5500),
        _call(155, 0.69,  6.2,  6.9, 3800),
        _call(160, 0.72,  4.2,  4.9, 2800),
        _call(165, 0.75,  2.7,  3.4, 1800),
        _call(170, 0.79,  1.6,  2.3, 1100),
        _call(175, 0.84,  1.0,  1.6,  650),
    ])
    aug_puts = pd.DataFrame([
        _put(125, 0.82,  1.2,  1.9, 1100),
        _put(130, 0.77,  2.2,  2.9, 1700),
        _put(135, 0.72,  3.8,  4.5, 3100),
        _put(140, 0.67,  6.2,  6.9, 5200),
        _put(143, 0.63, 12.7, 13.5, 8600),  # ATM
        _put(145, 0.62, 14.5, 15.2, 7000),
        _put(150, 0.60, 19.5, 20.2, 4600),
        _put(155, 0.58, 25.0, 25.7, 2900),
        _put(160, 0.57, 30.8, 31.5, 1700),
    ])

    return {
        "2026-06-27": {"calls": weekly_calls, "puts": weekly_puts},
        "2026-07-18": {"calls": monthly_calls, "puts": monthly_puts},
        "2026-08-21": {"calls": aug_calls,    "puts": aug_puts},
    }


def build_soxx_demo_chains():
    """SOXX options for sector comparison (38% ATM IV, 7 DTE)."""
    soxx_calls = pd.DataFrame([
        _call(245, 0.30, 21.5, 22.2,  450),
        _call(250, 0.32, 17.5, 18.2,  700),
        _call(255, 0.35, 13.5, 14.2, 1100),
        _call(260, 0.37, 10.0, 10.7, 1700),
        _call(265, 0.38,  6.8,  7.5, 2800),  # ATM
        _call(270, 0.40,  4.5,  5.2, 2100),
        _call(275, 0.43,  2.8,  3.4, 1300),
        _call(280, 0.47,  1.5,  2.0,  750),
    ])
    soxx_puts = pd.DataFrame([
        _put(245, 0.46,  1.3,  1.9,  350),
        _put(250, 0.43,  2.5,  3.1,  550),
        _put(255, 0.40,  4.2,  4.9,  850),
        _put(260, 0.38,  6.5,  7.2, 1500),
        _put(265, 0.36,  9.8, 10.5, 2400),  # ATM
        _put(270, 0.34, 14.0, 14.7, 1700),
        _put(275, 0.33, 19.0, 19.7,  950),
        _put(280, 0.31, 24.5, 25.2,  500),
    ])
    return {
        "2026-06-27": {"calls": soxx_calls, "puts": soxx_puts},
    }
