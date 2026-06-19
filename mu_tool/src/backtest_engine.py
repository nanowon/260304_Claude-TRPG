"""
Backtesting engine: evaluates playbook signal accuracy on historical MU earnings.

Key insight: Pre-earnings signals are unreliable for DIRECTION prediction.
The primary testable hypothesis is: "Is implied vol overpriced?"
→ Test straddle P&L (realized/implied ratio) as main metric.
"""
import numpy as np
import pandas as pd
from .earnings_history import get_earnings_df, MU_EARNINGS_HISTORY
from .skew_analyzer import MU_HISTORICAL_RR_25D
from .playbook import (
    score_implied_vs_history,
    score_iv_crush,
    score_term_structure,
    score_risk_reversal,
    score_oi_positioning,
    aggregate_scores,
)


MU_HISTORICAL_TS = {
    "FQ2 2026": ("MILD_BACKWARDATION", 0.08),
    "FQ1 2026": ("MILD_BACKWARDATION", 0.10),
    "FQ4 2025": ("MILD_BACKWARDATION", 0.06),
    "FQ3 2025": ("FLAT", 0.02),
    "FQ2 2025": ("STEEP_BACKWARDATION", 0.18),
    "FQ1 2025": ("STEEP_BACKWARDATION", 0.22),
    "FQ4 2024": ("MILD_BACKWARDATION", 0.12),
    "FQ3 2024": ("MILD_BACKWARDATION", 0.09),
    "FQ2 2024": ("MILD_BACKWARDATION", 0.07),
    "FQ1 2024": ("FLAT", 0.03),
    "FQ4 2023": ("FLAT", 0.01),
    "FQ3 2023": ("STEEP_BACKWARDATION", 0.20),
}

MU_HISTORICAL_OI_SIGNAL = {
    "FQ2 2026": ("CALL_DOMINANT", 0.60),
    "FQ1 2026": ("CALL_DOMINANT", 0.55),
    "FQ4 2025": ("NEUTRAL", 0.85),
    "FQ3 2025": ("NEUTRAL", 0.90),
    "FQ2 2025": ("MILD_PUT_BIAS", 1.10),
    "FQ1 2025": ("PUT_DOMINANT", 1.35),
    "FQ4 2024": ("CROWDED_LONG", 0.45),
    "FQ3 2024": ("CALL_DOMINANT", 0.52),
    "FQ2 2024": ("CALL_DOMINANT", 0.58),
    "FQ1 2024": ("NEUTRAL", 0.82),
    "FQ4 2023": ("NEUTRAL", 0.95),
    "FQ3 2023": ("MILD_PUT_BIAS", 1.15),
}


def run_backtest(verbose: bool = True) -> pd.DataFrame:
    """
    Walk-forward backtest across all historical MU earnings.
    Primary metric: straddle P&L (long straddle vs short straddle).
    Secondary metric: directional accuracy (shown as informational only).
    """
    df = get_earnings_df()
    rr_dict = {fq: rr for fq, _, rr in MU_HISTORICAL_RR_25D}
    results = []
    sorted_df = df.sort_values("announce_date").reset_index(drop=True)

    for i, row in sorted_df.iterrows():
        fq = row["fiscal_quarter"]
        if row["implied_move"] is None or pd.isna(row["realized_1d"]):
            continue

        # Walk-forward: only use prior quarters
        prior = sorted_df.iloc[:i]
        min_prior = 3
        if len(prior) < min_prior:
            hist_avg_implied = 0.068
            avg_roi = 0.82
        else:
            hist_avg_implied = prior["implied_move"].mean()
            avg_roi = (prior["abs_realized"] / prior["implied_move"]).mean()

        ts_shape, ts_slope = MU_HISTORICAL_TS.get(fq, ("FLAT", 0.02))
        rr_value = rr_dict.get(fq, 0.03)
        oi_signal, pcr = MU_HISTORICAL_OI_SIGNAL.get(fq, ("NEUTRAL", 1.0))

        prior_rr_vals = []
        for j in range(i):
            pfq = sorted_df.iloc[j]["fiscal_quarter"]
            if pfq in rr_dict:
                prior_rr_vals.append(rr_dict[pfq])
        rr_pct = float((np.array(prior_rr_vals) < rr_value).mean() * 100) if prior_rr_vals else 50.0

        # Pre-earnings IV estimate from implied move
        # ATM IV ≈ implied_move / (sqrt(2/pi) * sqrt(T)) where T≈7/252 (weekly)
        T_event = 7 / 252
        pre_iv = row["implied_move"] / (np.sqrt(2 / np.pi) * np.sqrt(T_event))
        crush_abs = pre_iv * 0.38

        # Vol-expensive composite (primary signal)
        vol_axes = [
            score_implied_vs_history(row["implied_move"], hist_avg_implied, avg_roi),
            score_iv_crush(pre_iv, crush_abs),
            score_term_structure(ts_shape, ts_slope),
        ]
        vol_agg = aggregate_scores(vol_axes)

        # Full composite including direction signals
        all_axes = vol_axes + [
            score_risk_reversal(rr_pct, rr_value),
            score_oi_positioning(oi_signal, pcr),
        ]
        full_agg = aggregate_scores(all_axes)

        # Outcomes
        realized = row["realized_1d"]
        direction = +1 if realized > 0 else -1
        roi = row["realized_over_implied"]  # realized/implied

        # Straddle P&L (long straddle) = roi - 1
        long_straddle_pl = roi - 1.0
        # Short straddle P&L = 1 - roi (capped at 1.0 since max loss = premium)
        short_straddle_pl = min(1 - roi, 1.0)

        # Vol signal: only fire when composite is outside neutral band (±0.20)
        # Tighter threshold reduces false positives from weak signals
        vol_score = vol_agg["composite_score"]
        sell_vol = vol_score < -0.20
        buy_vol = vol_score > 0.20

        # Signal accuracy for vol
        # If sell_vol: correct when roi < 1 (straddle doesn't pay off)
        if sell_vol:
            vol_signal_correct = roi < 1.0
            vol_trade_pl = short_straddle_pl
        elif buy_vol:
            vol_signal_correct = roi >= 1.0
            vol_trade_pl = long_straddle_pl
        else:
            vol_signal_correct = None  # no signal
            vol_trade_pl = 0.0

        # Direction accuracy (informational only)
        pred_direction = +1 if full_agg["composite_score"] > 0 else -1
        dir_correct = pred_direction == direction

        results.append({
            "fiscal_quarter": fq,
            "announce_date": row["announce_date"],
            "implied_move": row["implied_move"],
            "realized_1d": realized,
            "abs_realized": row["abs_realized"],
            "realized_over_implied": roi,
            "long_straddle_pl": long_straddle_pl,
            "short_straddle_pl": short_straddle_pl,
            "vol_composite": vol_score,
            "full_composite": full_agg["composite_score"],
            "verdict": full_agg["verdict"],
            "sell_vol_signal": sell_vol,
            "buy_vol_signal": buy_vol,
            "vol_signal_correct": vol_signal_correct,
            "vol_trade_pl": vol_trade_pl,
            "pred_direction": pred_direction,
            "actual_direction": direction,
            "dir_correct": dir_correct,
            "ts_shape": ts_shape,
            "oi_signal": oi_signal,
            "guidance_tone": row.get("guidance_tone", "N/A"),
            "prior_n": len(prior),
        })

    return pd.DataFrame(results)


def compute_signal_accuracy(bt_df: pd.DataFrame) -> dict:
    """Calculate accuracy metrics with primary focus on vol signal."""
    if bt_df.empty:
        return {}

    total = len(bt_df)

    # Vol signal stats
    sell_sigs = bt_df[bt_df["sell_vol_signal"]]
    buy_sigs = bt_df[bt_df["buy_vol_signal"]]
    no_sig = bt_df[~bt_df["sell_vol_signal"] & ~bt_df["buy_vol_signal"]]

    n_sell = len(sell_sigs)
    n_buy = len(buy_sigs)

    # Accuracy when signals fired
    sell_acc = sell_sigs["vol_signal_correct"].mean() * 100 if n_sell > 0 else np.nan
    buy_acc = buy_sigs["vol_signal_correct"].mean() * 100 if n_buy > 0 else np.nan

    # Average P&L by signal type
    sell_avg_pl = sell_sigs["vol_trade_pl"].mean() if n_sell > 0 else np.nan
    buy_avg_pl = buy_sigs["vol_trade_pl"].mean() if n_buy > 0 else np.nan

    # Overall straddle stats
    beat_implied_all = (bt_df["realized_over_implied"] >= 1.0).mean() * 100
    avg_roi = bt_df["realized_over_implied"].mean()
    long_straddle_avg = bt_df["long_straddle_pl"].mean() * 100

    # Direction accuracy (note: secondary metric)
    dir_acc = bt_df["dir_correct"].mean() * 100

    # Signal correlation
    corr_vol = bt_df["vol_composite"].corr(bt_df["realized_over_implied"])
    corr_dir = bt_df["full_composite"].corr(bt_df["realized_1d"])

    return {
        "total_quarters": total,
        # Vol signal performance
        "n_sell_signals": n_sell,
        "n_buy_signals": n_buy,
        "n_no_signal": len(no_sig),
        "sell_vol_accuracy_pct": sell_acc,
        "buy_vol_accuracy_pct": buy_acc,
        "sell_vol_avg_pl_pct": sell_avg_pl * 100 if not np.isnan(sell_avg_pl) else np.nan,
        "buy_vol_avg_pl_pct": buy_avg_pl * 100 if not np.isnan(buy_avg_pl) else np.nan,
        # Straddle baseline
        "beat_implied_rate_all_pct": beat_implied_all,
        "avg_realized_over_implied": avg_roi,
        "long_straddle_avg_pl_pct": long_straddle_avg,
        # Direction (informational)
        "direction_accuracy_pct": dir_acc,
        # Correlations
        "vol_composite_vs_roi_corr": corr_vol,
        "full_composite_vs_realized_corr": corr_dir,
    }


def compute_confidence_score(
    accuracy_metrics: dict,
    n_quarters: int,
    signal_strength: float,
) -> dict:
    """
    Confidence score focused on vol signal reliability.
    Primary: vol signal accuracy vs random baseline (50%).
    Secondary: correlation of composite with realized move.
    """
    # Vol signal accuracy (primary)
    sell_acc = accuracy_metrics.get("sell_vol_accuracy_pct", 50)
    buy_acc = accuracy_metrics.get("buy_vol_accuracy_pct", 50)
    n_sell = accuracy_metrics.get("n_sell_signals", 0)
    n_buy = accuracy_metrics.get("n_buy_signals", 0)

    # Weight by signal count (skip NaN components)
    total_sigs = n_sell + n_buy
    components = []
    if n_sell > 0 and not np.isnan(sell_acc):
        components.append((sell_acc, n_sell))
    if n_buy > 0 and not np.isnan(buy_acc):
        components.append((buy_acc, n_buy))
    if components:
        weighted_acc = sum(a * n for a, n in components) / sum(n for _, n in components)
    else:
        weighted_acc = 50.0

    acc_above_random = max(weighted_acc - 50, 0) / 50  # 0 to 1

    # Correlation contribution
    corr = abs(accuracy_metrics.get("vol_composite_vs_roi_corr", 0))
    corr_conf = corr  # 0 to 1

    # Sample size factor (Wilson-style)
    n_eff = min(total_sigs if total_sigs > 0 else n_quarters, 12)
    n_factor = n_eff / 12

    # Beat-implied base rate: if <40%, options are structurally overpriced
    beat_rate = accuracy_metrics.get("beat_implied_rate_all_pct", 50) / 100
    structural_bias = max(0.5 - beat_rate, 0) * 2  # 0 to 1 (higher when cheap to sell)

    raw = (
        acc_above_random * 0.40 +
        corr_conf * 0.25 +
        structural_bias * 0.20 +
        signal_strength * 0.15
    ) * n_factor

    raw = np.clip(raw, 0, 1)

    # Wilson lower bound for vol signal accuracy
    p = weighted_acc / 100
    n_w = max(total_sigs, 1)
    z = 1.645
    wilson = (p + z**2/(2*n_w) - z * np.sqrt(p*(1-p)/n_w + z**2/(4*n_w**2))) / (1 + z**2/n_w)
    stat_lb = wilson * 100

    return {
        "composite_confidence": raw * 100,
        "vol_signal_accuracy": weighted_acc,
        "stat_lower_bound_pct": stat_lb,
        "vol_composite_vs_roi_corr": corr,
        "beat_implied_rate_all": accuracy_metrics.get("beat_implied_rate_all_pct", 50),
        "structural_sell_bias": structural_bias * 100,
        "sample_n_signals": total_sigs,
        "signal_strength_used": signal_strength,
        "interpretation": _conf_label(raw),
        "key_insight": _key_insight(accuracy_metrics),
    }


def _conf_label(c: float) -> str:
    if c >= 0.60:
        return "HIGH — 신호 신뢰도 높음, 실행 가능"
    elif c >= 0.40:
        return "MODERATE — 참고 수준, 리스크 관리 병행"
    elif c >= 0.20:
        return "LOW — 추가 확인 필요, 포지션 축소 권장"
    else:
        return "VERY LOW — 노이즈 수준, 단독 사용 금지"


def _key_insight(acc: dict) -> str:
    roi = acc.get("avg_realized_over_implied", 1.0)
    beat = acc.get("beat_implied_rate_all_pct", 50)
    dir_acc = acc.get("direction_accuracy_pct", 50)

    insights = []
    if roi < 0.70:
        insights.append(f"평균 R/I={roi:.2f}x — 옵션 구조적 과열 (short straddle 유리한 종목)")
    elif roi > 1.20:
        insights.append(f"평균 R/I={roi:.2f}x — 옵션 과소평가 경향 (long straddle 유리)")
    else:
        insights.append(f"평균 R/I={roi:.2f}x — 중립")

    if dir_acc < 45:
        insights.append(f"방향 정확도={dir_acc:.0f}% (랜덤 이하) → 방향 베팅 비권장")
    elif dir_acc > 60:
        insights.append(f"방향 정확도={dir_acc:.0f}% → 방향 신호 참고 가능")

    return " | ".join(insights)
