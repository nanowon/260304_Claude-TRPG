"""
Demo/offline mode: realistic MU data for FQ3 2026 earnings (2026-06-24).
Based on user-provided context:
- MU price: $1171.5 (actual, June 22 2026)
- Expected move: ~18% (Options AI 17.9%)
- SOXX: ~$2170 (estimated, proportional scale)
- ATM IV for 4-DTE weekly (~215%) to produce 18% straddle move

Straddle approximation: IM ≈ IV_ATM * sqrt(2T/π)
For T=4/365, IM=18%: IV_ATM = 0.18 / sqrt(2*4/365/π) ≈ 215%

All strikes/prices scaled 8.19x from original $143 baseline.
Weekly IV recalibrated from 163% (7 DTE) → 215% (4 DTE) for same 18% IM.
"""
import numpy as np
import pandas as pd

MU_DEMO = {
    "ticker": "MU",
    "price": 1171.5,
    "prev_close": 1167.5,
    "change_pct": 0.34,
}

SOXX_DEMO = {
    "ticker": "SOXX",
    "price": 2170.0,
    "prev_close": 2154.0,
    "change_pct": 0.74,
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
    Build realistic demo options chain for MU at $1171.5.

    Weekly 2026-06-27 (4 DTE):
      ATM IV ~215% → straddle ~$209 → IM ≈ 17.9% of $1171.5
      Steep backwardation vs monthly.
      Slight call skew: RR ≈ +7% (calls > puts at 25Δ)

    Monthly 2026-07-18 (26 DTE):
      ATM IV ~85% → straddle ~$207 → IM ≈ 17.7%

    Aug 2026-08-21 (60 DTE):
      ATM IV ~65% → straddle ~$274 → IM ≈ 23.4%
    """
    # ── 2026-06-27 weekly (4 DTE, IV~215%) ──
    # ATM calls/puts at strike 1170: ~$105.4 each (straddle ~$209 = 17.9%)
    # Call skew: OTM calls carry higher IV than OTM puts (bullish positioning)
    weekly_calls = pd.DataFrame([
        _call( 940, 1.91, 233.4, 239.3,  600),
        _call( 985, 1.98, 200.7, 206.5,  900),
        _call(1025, 2.04, 167.9, 173.7, 1800),
        _call(1065, 2.08, 137.6, 143.4, 3200),
        _call(1105, 2.11, 108.1, 114.7, 5500),
        _call(1145, 2.14,  77.8,  84.4, 9200),   # near ATM
        _call(1170, 2.15, 102.4, 108.1, 13000),  # ATM ← straddle mid ~$105.2
        _call(1190, 2.16,  91.7,  97.5, 10500),
        _call(1230, 2.20,  63.9,  69.7,  7200),
        _call(1270, 2.27,  41.0,  46.7,  4800),
        _call(1310, 2.35,  24.6,  30.3,  3100),
        _call(1350, 2.44,  13.9,  18.8,  1800),
        _call(1390, 2.55,   7.4,  11.5,  1000),
        _call(1435, 2.66,   3.3,   7.4,   550),
    ])
    weekly_puts = pd.DataFrame([
        _put( 940, 2.64,   3.3,   7.4,  400),
        _put( 985, 2.57,   6.6,  10.7,  650),
        _put(1025, 2.48,  12.3,  17.2, 1100),
        _put(1065, 2.35,  22.9,  28.7, 2600),
        _put(1105, 2.24,  39.3,  45.1, 4800),
        _put(1145, 2.18,  61.5,  67.2, 8500),    # near ATM
        _put(1170, 2.01, 100.7, 107.4, 12500),   # ATM ← straddle mid ~$104.0
        _put(1190, 1.95, 114.7, 121.3,  9800),
        _put(1230, 1.87, 149.1, 155.7,  6200),
        _put(1270, 1.78, 188.4, 195.2,  3500),
        _put(1310, 1.69, 229.3, 236.1,  1900),
    ])

    # ── 2026-07-18 monthly (26 DTE, IV~85%) ──
    # ATM straddle: 1171.5 * 0.85 * sqrt(2*26/365/pi) ≈ $207 → ~17.7% IM
    monthly_calls = pd.DataFrame([
        _call( 985, 0.70, 217.1, 222.8, 2200),
        _call(1025, 0.72, 186.8, 192.5, 3500),
        _call(1065, 0.74, 159.7, 165.4, 5000),
        _call(1105, 0.76, 135.1, 140.9, 7500),
        _call(1145, 0.79, 110.6, 116.3, 11000),
        _call(1170, 0.85, 104.8, 110.6, 15200),  # ATM
        _call(1190, 0.86,  94.2, 100.0, 12500),
        _call(1230, 0.88,  72.1,  77.8,  8500),
        _call(1270, 0.91,  53.2,  59.0,  5800),
        _call(1310, 0.94,  36.9,  42.6,  3900),
        _call(1350, 0.98,  24.6,  30.3,  2600),
        _call(1390, 1.03,  15.6,  20.5,  1600),
        _call(1435, 1.09,   9.0,  13.9,   900),
        _call(1475, 1.15,   4.9,   9.0,   500),
    ])
    monthly_puts = pd.DataFrame([
        _put( 985, 1.03,   6.6,  11.5, 1600),
        _put(1025, 0.98,  12.3,  17.2, 2500),
        _put(1065, 0.91,  22.9,  28.7, 4000),
        _put(1105, 0.86,  39.3,  45.1, 6500),
        _put(1145, 0.82,  61.5,  67.2, 9500),
        _put(1170, 0.78,  96.6, 102.4, 14200),   # ATM
        _put(1190, 0.75, 110.6, 116.3, 11000),
        _put(1230, 0.72, 147.4, 153.2,  7000),
        _put(1270, 0.69, 188.4, 194.2,  4300),
        _put(1310, 0.67, 231.0, 237.0,  2700),
    ])

    # ── 2026-08-21 (60 DTE, IV~65%) ──
    # ATM straddle: 1171.5 * 0.65 * sqrt(2*60/365/pi) ≈ $274 → ~23.4% IM
    aug_calls = pd.DataFrame([
        _call(1025, 0.57, 204.8, 210.5, 1600),
        _call(1065, 0.59, 176.1, 181.8, 2600),
        _call(1105, 0.61, 147.4, 153.2, 4000),
        _call(1145, 0.63, 122.9, 128.6, 6500),
        _call(1170, 0.65, 108.1, 114.7, 9200),   # ATM
        _call(1190, 0.65,  96.6, 102.4, 7900),
        _call(1230, 0.67,  72.1,  77.8, 5500),
        _call(1270, 0.69,  50.8,  56.5, 3800),
        _call(1310, 0.72,  34.4,  40.1, 2800),
        _call(1350, 0.75,  22.1,  27.8, 1800),
        _call(1390, 0.79,  13.1,  18.8, 1100),
        _call(1435, 0.84,   8.2,  13.1,  650),
    ])
    aug_puts = pd.DataFrame([
        _put(1025, 0.82,   9.8,  15.6, 1100),
        _put(1065, 0.77,  18.0,  23.7, 1700),
        _put(1105, 0.72,  31.1,  36.9, 3100),
        _put(1145, 0.67,  50.8,  56.5, 5200),
        _put(1170, 0.63, 104.1, 110.6, 8600),    # ATM
        _put(1190, 0.62, 118.8, 124.5, 7000),
        _put(1230, 0.60, 159.7, 165.5, 4600),
        _put(1270, 0.58, 204.8, 210.5, 2900),
        _put(1310, 0.57, 252.2, 258.0, 1700),
    ])

    return {
        "2026-06-27": {"calls": weekly_calls, "puts": weekly_puts},
        "2026-07-18": {"calls": monthly_calls, "puts": monthly_puts},
        "2026-08-21": {"calls": aug_calls,    "puts": aug_puts},
    }


def build_soxx_demo_chains():
    """SOXX options for sector comparison (~38% ATM IV, 4 DTE). Price ~$2170."""
    soxx_calls = pd.DataFrame([
        _call(2005, 0.30, 176.1, 181.8,  450),
        _call(2050, 0.32, 143.4, 148.9,  700),
        _call(2090, 0.35, 110.6, 116.3, 1100),
        _call(2130, 0.37,  81.9,  87.7, 1700),
        _call(2170, 0.38,  55.7,  61.5, 2800),   # ATM
        _call(2210, 0.40,  36.9,  42.6, 2100),
        _call(2250, 0.43,  22.9,  27.9, 1300),
        _call(2290, 0.47,  12.3,  16.4,  750),
    ])
    soxx_puts = pd.DataFrame([
        _put(2005, 0.46,  10.7,  15.6,  350),
        _put(2050, 0.43,  20.5,  25.4,  550),
        _put(2090, 0.40,  34.4,  40.1,  850),
        _put(2130, 0.38,  53.2,  59.0, 1500),
        _put(2170, 0.36,  80.3,  86.0, 2400),    # ATM
        _put(2210, 0.34, 114.7, 120.4, 1700),
        _put(2250, 0.33, 155.6, 161.4,  950),
        _put(2290, 0.31, 200.7, 206.5,  500),
    ])
    return {
        "2026-06-27": {"calls": soxx_calls, "puts": soxx_puts},
    }
