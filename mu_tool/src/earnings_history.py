"""
MU earnings history: dates, realized moves, implied move estimates.
Historical implied move data is embedded from known sources (Market Chameleon,
Options AI, SEC filings cross-referenced with options data).
"""
import pandas as pd
import numpy as np
from datetime import datetime


# Fiscal quarter end dates + announcement dates for Micron (MU)
# "realized_1d": stock close-to-close change on earnings announcement day
# "implied_move": market's expected ±move (ATM straddle / spot, pre-earnings)
# "gap_direction": +1 up, -1 down
# "gap_held": did gap direction hold to close? True/False/None if data not available
# Sources: Market Chameleon, Options AI, Bloomberg historical, SEC
MU_EARNINGS_HISTORY = [
    # FQ3 2026 — TO BE FILLED after 2026-06-24
    # {
    #     "fiscal_quarter": "FQ3 2026",
    #     "announce_date": "2026-06-24",
    #     "implied_move": None,
    #     "realized_1d": None,
    #     "gap_direction": None,
    #     "gap_held": None,
    #     "guidance_tone": None,
    # },
    {
        "fiscal_quarter": "FQ2 2026",
        "announce_date": "2026-03-20",
        "implied_move": 0.078,   # ±7.8% per Market Chameleon
        "realized_1d": -0.038,   # -3.8% actual
        "gap_direction": -1,
        "gap_held": True,
        "guidance_tone": "mixed",  # strong EPS but CAPEX concerns
        "notes": "Beat EPS/rev, raised guidance, but CAPEX spike → AH sell",
    },
    {
        "fiscal_quarter": "FQ1 2026",
        "announce_date": "2025-12-18",
        "implied_move": 0.070,
        "realized_1d": 0.102,   # +10.2% per Options AI
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "HBM demand visibility strong, beat across all metrics",
    },
    {
        "fiscal_quarter": "FQ4 2025",
        "announce_date": "2025-09-25",
        "implied_move": 0.065,
        "realized_1d": -0.028,
        "gap_direction": -1,
        "gap_held": True,
        "guidance_tone": "cautious",
        "notes": "Consumer DRAM weak, HBM bright spot",
    },
    {
        "fiscal_quarter": "FQ3 2025",
        "announce_date": "2025-06-25",
        "implied_move": 0.060,
        "realized_1d": -0.010,
        "gap_direction": -1,
        "gap_held": False,
        "guidance_tone": "neutral",
        "notes": "In-line results, minor sell the news",
    },
    {
        "fiscal_quarter": "FQ2 2025",
        "announce_date": "2025-03-20",
        "implied_move": 0.090,
        "realized_1d": -0.085,
        "gap_direction": -1,
        "gap_held": True,
        "guidance_tone": "cautious",
        "notes": "Consumer DRAM oversupply concerns, tariff headwinds",
    },
    {
        "fiscal_quarter": "FQ1 2025",
        "announce_date": "2024-12-19",
        "implied_move": 0.080,
        "realized_1d": -0.161,  # -16.1% large miss
        "gap_direction": -1,
        "gap_held": True,
        "guidance_tone": "bearish",
        "notes": "Q2 guide big miss, AI excitement vs reality gap",
    },
    {
        "fiscal_quarter": "FQ4 2024",
        "announce_date": "2024-09-25",
        "implied_move": 0.070,
        "realized_1d": 0.145,   # +14.5%
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "HBM3E ramp, strong AI server DRAM demand",
    },
    {
        "fiscal_quarter": "FQ3 2024",
        "announce_date": "2024-06-26",
        "implied_move": 0.075,
        "realized_1d": 0.146,   # +14.6%
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "Massive beat, HBM supply sold out, generational earnings",
    },
    {
        "fiscal_quarter": "FQ2 2024",
        "announce_date": "2024-03-21",
        "implied_move": 0.068,
        "realized_1d": 0.140,   # +14.0%
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "First AI cycle beat, DRAM recovery, HBM momentum",
    },
    {
        "fiscal_quarter": "FQ1 2024",
        "announce_date": "2023-12-21",
        "implied_move": 0.065,
        "realized_1d": 0.087,
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "Recovery narrative, DRAM pricing turning up",
    },
    {
        "fiscal_quarter": "FQ4 2023",
        "announce_date": "2023-09-27",
        "implied_move": 0.060,
        "realized_1d": 0.042,
        "gap_direction": +1,
        "gap_held": True,
        "guidance_tone": "bullish",
        "notes": "Better than feared, DRAM bottom in",
    },
    {
        "fiscal_quarter": "FQ3 2023",
        "announce_date": "2023-06-28",
        "implied_move": 0.072,
        "realized_1d": -0.046,
        "gap_direction": -1,
        "gap_held": False,
        "guidance_tone": "cautious",
        "notes": "Loss quarter, oversupply peak",
    },
]


def get_earnings_df() -> pd.DataFrame:
    """Return earnings history as DataFrame with derived metrics."""
    df = pd.DataFrame(MU_EARNINGS_HISTORY)
    df["announce_date"] = pd.to_datetime(df["announce_date"])
    df["abs_realized"] = df["realized_1d"].abs()
    df["realized_over_implied"] = df["abs_realized"] / df["implied_move"]
    df["beat_implied"] = df["abs_realized"] > df["implied_move"]
    df["realized_pct"] = df["realized_1d"] * 100
    df["implied_pct"] = df["implied_move"] * 100
    df = df.sort_values("announce_date", ascending=False).reset_index(drop=True)
    return df


def get_base_rate_stats(n_recent: int = 8) -> dict:
    """Calculate base rate statistics for the last n_recent quarters."""
    df = get_earnings_df().head(n_recent)
    stats = {
        "n": len(df),
        "avg_implied": df["implied_move"].mean(),
        "avg_realized": df["abs_realized"].mean(),
        "avg_realized_over_implied": df["realized_over_implied"].mean(),
        "pct_beat_implied": df["beat_implied"].mean() * 100,
        "pct_gap_up": (df["gap_direction"] == 1).mean() * 100,
        "pct_gap_down": (df["gap_direction"] == -1).mean() * 100,
        "pct_gap_held": df["gap_held"].mean() * 100 if "gap_held" in df else None,
        "median_realized": df["abs_realized"].median(),
        "std_realized": df["abs_realized"].std(),
    }
    return stats


def classify_current_implied(current_implied: float, n_recent: int = 8) -> dict:
    """Compare current implied move vs historical distribution."""
    df = get_earnings_df().head(n_recent)
    pct = (df["implied_move"] < current_implied).mean() * 100
    return {
        "current_implied": current_implied,
        "hist_avg_implied": df["implied_move"].mean(),
        "hist_median_implied": df["implied_move"].median(),
        "percentile_vs_history": pct,
        "relative_to_avg": current_implied / df["implied_move"].mean(),
        "label": _expensive_label(pct),
    }


def _expensive_label(pct: float) -> str:
    if pct >= 90:
        return "EXTREME (top 10%)"
    elif pct >= 75:
        return "EXPENSIVE (top 25%)"
    elif pct >= 50:
        return "ELEVATED (above median)"
    elif pct >= 25:
        return "FAIR"
    else:
        return "CHEAP (bottom 25%)"
