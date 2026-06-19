"""
Signal aggregation and playbook generation.
Combines all 6 axes into a pre-earnings score and post-announcement tracker.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AxisScore:
    name: str
    value: float           # -1.0 to +1.0 (sell_news → buy_news)
    weight: float          # relative weight
    label: str
    detail: str


def score_implied_vs_history(
    current_implied: float,
    hist_avg_implied: float,
    avg_realized_over_implied: float,
) -> AxisScore:
    """
    Axis 1: Implied move relative to historical norm.

    Primary driver: how expensive is current implied vs historical average?
    This dominates for outlier setups (>2x historical).
    Secondary: historical R/I ratio adjusts by ±25% (historical bias).

    Calibration:
    - rel_expense 1.0x → 0, 1.5x → -0.25, 2.0x → -0.50, 2.5x → -0.75
    - roi_factor 1.2x adds +0.10, 0.8x subtracts -0.10 (bounded adjustment)
    """
    rel_expense = current_implied / max(hist_avg_implied, 0.001)

    # Expense penalty: primary signal, strong at outliers
    expense_penalty = -np.clip((rel_expense - 1.0) * 0.5, -0.8, 0.8)

    # Historical roi adjustment: bounded ±0.15 to avoid overriding expense signal
    roi_adj = np.clip((avg_realized_over_implied - 1.0) * 0.15, -0.15, 0.15)

    score = np.clip(expense_penalty + roi_adj, -1, 1)

    if rel_expense > 1.8:
        exp_label = f"과거 평균의 {rel_expense:.1f}x (과열)"
    elif rel_expense > 1.2:
        exp_label = f"과거 평균의 {rel_expense:.1f}x (높음)"
    elif rel_expense < 0.8:
        exp_label = f"과거 평균의 {rel_expense:.1f}x (저렴)"
    else:
        exp_label = f"과거 평균의 {rel_expense:.1f}x (정상)"

    roi_label = f"realized/implied={avg_realized_over_implied:.2f}x — {'과소평가 경향' if avg_realized_over_implied > 1 else '옵션 비쌈'}"

    return AxisScore(
        name="① Implied vs Historical",
        value=float(score),
        weight=1.5,
        label="SELL_VOL" if score < -0.3 else "NEUTRAL" if score < 0.3 else "BUY_VOL",
        detail=f"현재 implied={current_implied*100:.1f}% — {exp_label} | {roi_label}",
    )


def score_iv_crush(
    pre_earnings_iv: float,
    estimated_crush_abs: float,
    hist_avg_crush: float = 0.38,
) -> AxisScore:
    """Axis 2: IV crush risk."""
    crush_ratio = estimated_crush_abs / max(pre_earnings_iv, 0.01)
    # Higher crush → more negative for long option buyers
    relative_to_hist = crush_ratio / hist_avg_crush
    score = np.clip(-(relative_to_hist - 1.0) * 0.8, -1, 1)

    return AxisScore(
        name="② IV Crush Risk",
        value=float(score),
        weight=1.2,
        label="HIGH_CRUSH" if crush_ratio > 0.40 else "MODERATE" if crush_ratio > 0.25 else "LOW_CRUSH",
        detail=f"예상 crush: {estimated_crush_abs*100:.1f}%p ({crush_ratio*100:.0f}%) — 과거 평균 {hist_avg_crush*100:.0f}%",
    )


def score_term_structure(shape: str, slope_short: float) -> AxisScore:
    """Axis 3: Term structure shape."""
    mapping = {
        "STEEP_BACKWARDATION": -0.8,
        "MILD_BACKWARDATION": -0.2,
        "FLAT": 0.2,
        "CONTANGO": 0.7,
        "INSUFFICIENT_DATA": 0.0,
    }
    score = mapping.get(shape, 0.0)
    return AxisScore(
        name="③ Term Structure",
        value=score,
        weight=1.0,
        label=shape,
        detail=f"단기 slope: {slope_short*100:+.1f}%p — {'백워데이션 (IV crush 위험)' if slope_short > 0.05 else '콘탱고 (추세 기대)' if slope_short < -0.05 else '평탄'}",
    )


def score_risk_reversal(rr_percentile: float, current_rr: float) -> AxisScore:
    """Axis 4: 25Δ Risk Reversal percentile."""
    # High percentile (call heavy) → sell in news risk
    # Low percentile (put heavy) → potential relief rally
    score = np.clip(-(rr_percentile - 50) / 50, -1, 1)

    return AxisScore(
        name="④ 25Δ Risk Reversal",
        value=float(score),
        weight=1.0,
        label=f"{rr_percentile:.0f}%ile",
        detail=(
            f"현재 RR: {current_rr*100:+.1f}% | "
            f"percentile: {rr_percentile:.0f}% — "
            f"{'콜 과열 (sell in news 위험)' if rr_percentile >= 80 else '풋 우위 (안도 랠리 가능)' if rr_percentile <= 20 else '중립'}"
        ),
    )


def score_oi_positioning(signal: str, put_call_ratio: float) -> AxisScore:
    """Axis 5: OI-based positioning."""
    mapping = {
        "CROWDED_LONG": -0.8,
        "CALL_DOMINANT": -0.3,
        "NEUTRAL": 0.0,
        "MILD_PUT_BIAS": 0.3,
        "PUT_DOMINANT": 0.6,
    }
    score = mapping.get(signal, 0.0)
    return AxisScore(
        name="⑤ OI Positioning",
        value=score,
        weight=0.8,
        label=signal,
        detail=f"Put/Call OI ratio: {put_call_ratio:.2f} — {signal}",
    )


def score_sector_context(idio_pct: float, mu_beta: float, soxx_iv_relative: float) -> AxisScore:
    """Axis 6: Sector/SOXX adjusted context."""
    # High idio_pct = pure event play (neutral for direction, but cleaner signal)
    # If SOXX IV also elevated, macro noise is high
    if idio_pct >= 70:
        score = 0.1  # clean event signal
    elif idio_pct >= 50:
        score = 0.0
    elif idio_pct >= 30:
        score = -0.1  # macro noise
    else:
        score = -0.3  # macro dominated

    return AxisScore(
        name="⑥ Sector Context",
        value=score,
        weight=0.7,
        label=f"idio={idio_pct:.0f}%",
        detail=f"MU IV의 {idio_pct:.0f}%가 실적 특이 요인 — beta={mu_beta:.2f}",
    )


def aggregate_scores(axes: list[AxisScore]) -> dict:
    """Weighted average of all axis scores → final verdict."""
    total_weight = sum(a.weight for a in axes)
    weighted_sum = sum(a.value * a.weight for a in axes)
    composite = weighted_sum / total_weight if total_weight > 0 else 0

    if composite <= -0.5:
        verdict = "STRONG SELL_IN_NEWS"
        color = "red"
    elif composite <= -0.2:
        verdict = "LEAN SELL_IN_NEWS"
        color = "dark_orange"
    elif composite <= 0.2:
        verdict = "NEUTRAL / WAIT"
        color = "yellow"
    elif composite <= 0.5:
        verdict = "LEAN BUY_THE_NEWS"
        color = "green"
    else:
        verdict = "STRONG BUY_THE_NEWS"
        color = "bright_green"

    # Convert to 0-100 confidence scale
    confidence = abs(composite) * 100

    return {
        "composite_score": composite,
        "verdict": verdict,
        "color": color,
        "confidence": confidence,
        "axes": axes,
    }


def build_pre_earnings_checklist(
    implied_move: float,
    hist_avg_implied: float,
    avg_roi: float,
    pre_iv: float,
    crush_abs: float,
    ts_shape: str,
    ts_slope: float,
    rr_pct: float,
    rr_value: float,
    oi_signal: str,
    pcr: float,
    idio_pct: float,
    mu_beta: float,
    soxx_iv_rel: float = 1.0,
) -> dict:
    """Build complete pre-earnings playbook."""
    axes = [
        score_implied_vs_history(implied_move, hist_avg_implied, avg_roi),
        score_iv_crush(pre_iv, crush_abs),
        score_term_structure(ts_shape, ts_slope),
        score_risk_reversal(rr_pct, rr_value),
        score_oi_positioning(oi_signal, pcr),
        score_sector_context(idio_pct, mu_beta, soxx_iv_rel),
    ]
    return aggregate_scores(axes)


def post_announcement_checklist(
    gap_direction: int,             # +1 up, -1 down
    vwap_held_30min: Optional[bool],
    sector_verdict: str,
    iv_crush_actual: Optional[float],  # actual crush observed
    hbm_commentary: str = "unknown",   # bullish/neutral/bearish/unknown
) -> dict:
    """
    Post-announcement confirmation scoring.
    Returns final trade verdict.
    """
    signals = []

    # Gap direction
    if gap_direction > 0:
        signals.append(("Gap Direction", +1, "갭업"))
    else:
        signals.append(("Gap Direction", -1, "갭다운"))

    # VWAP
    if vwap_held_30min is True:
        signals.append(("30min VWAP", +1 * gap_direction, "VWAP 유지"))
    elif vwap_held_30min is False:
        signals.append(("30min VWAP", -1 * gap_direction, "VWAP 이탈"))
    else:
        signals.append(("30min VWAP", 0, "확인 필요"))

    # Sector
    sector_score_map = {
        "BUY_THE_NEWS": +1,
        "MU_IDIO_SQUEEZE": -0.2,
        "SECTOR_RISK_OFF": -1,
        "MU_INDIVIDUAL_SELL": -0.8,
        "OVERREACTION_BUY_DIP": +0.5,
        "AMBIGUOUS": 0,
        "NO_DATA": 0,
    }
    sec_s = sector_score_map.get(sector_verdict, 0)
    signals.append(("Sector Coherence", sec_s, sector_verdict))

    # HBM commentary
    hbm_score_map = {
        "bullish": +0.8,
        "neutral": 0.0,
        "bearish": -0.8,
        "unknown": 0.0,
    }
    hbm_s = hbm_score_map.get(hbm_commentary, 0)
    signals.append(("HBM Commentary", hbm_s, hbm_commentary))

    avg_score = np.mean([s[1] for s in signals])

    if avg_score >= 0.5:
        verdict = "BUY_THE_NEWS 확증"
    elif avg_score >= 0.1:
        verdict = "약한 BUY_THE_NEWS"
    elif avg_score <= -0.5:
        verdict = "SELL_THE_NEWS 확증"
    elif avg_score <= -0.1:
        verdict = "약한 SELL_THE_NEWS"
    else:
        verdict = "AMBIGUOUS — 추가 대기"

    return {
        "signals": signals,
        "composite": avg_score,
        "verdict": verdict,
    }
