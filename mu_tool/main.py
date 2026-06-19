"""
MU Earnings Volatility Framework
실적 발표 후 가격 변동 예측 및 실시간 확증 툴

Usage:
    python main.py               # Live data (requires Yahoo Finance access)
    python main.py --demo        # Demo mode with realistic embedded data
    python main.py --backtest    # Backtest + confidence report only
    python main.py --post        # Post-announcement checklist
"""
import sys
import argparse
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/user/260304_Claude-TRPG/mu_tool")

from src.iv_analyzer import (
    compute_term_structure, analyze_term_structure,
    compute_implied_move, estimate_iv_crush, get_atm_iv,
)
from src.skew_analyzer import get_25delta_rr, get_rr_percentile
from src.oi_analyzer import analyze_oi_structure, compute_max_pain
from src.sector_analyzer import compute_idiosyncratic_iv
from src.earnings_history import get_earnings_df, get_base_rate_stats, classify_current_implied
from src.playbook import build_pre_earnings_checklist
from src.backtest_engine import run_backtest, compute_signal_accuracy, compute_confidence_score
from src.dashboard import (
    console,
    print_header, print_earnings_history, print_base_rates,
    print_term_structure, print_skew_analysis, print_oi_analysis,
    print_sector_context, print_playbook_verdict,
    print_backtest_results, print_confidence_report,
    print_post_announcement_checklist,
)

TICKER = "MU"
BENCHMARK = "SOXX"
EARNINGS_DATE = "2026-06-24"
TARGET_EXPIRIES = ["2026-06-27", "2026-07-18", "2026-08-21"]


def try_live_data():
    """Attempt to fetch live data. Returns None on failure."""
    try:
        from src.data_fetcher import (
            get_stock_info, get_all_options, get_beta, days_to_expiry,
        )
        mu_info = get_stock_info(TICKER)
        if not mu_info:
            return None
        soxx_info = get_stock_info(BENCHMARK)
        all_chains = get_all_options(TICKER)
        soxx_chains = get_all_options(BENCHMARK)
        beta = get_beta(TICKER, BENCHMARK)

        # Find relevant expiries
        all_exp = sorted(all_chains.keys())
        relevant = _find_expiries(all_exp, TARGET_EXPIRIES)
        if len(relevant) < 1:
            relevant = all_exp[:3]

        return {
            "mu": mu_info,
            "soxx": soxx_info,
            "chains": {e: all_chains[e] for e in relevant if e in all_chains},
            "soxx_chains": soxx_chains,
            "beta": beta,
            "expiries": relevant,
            "source": "LIVE",
        }
    except Exception as e:
        return None


def load_demo_data():
    """Load embedded realistic demo data."""
    from src.demo_data import (
        MU_DEMO, SOXX_DEMO, MU_BETA_DEMO,
        build_demo_chains, build_soxx_demo_chains,
    )
    chains = build_demo_chains()
    soxx_chains = build_soxx_demo_chains()
    return {
        "mu": MU_DEMO,
        "soxx": SOXX_DEMO,
        "chains": chains,
        "soxx_chains": soxx_chains,
        "beta": MU_BETA_DEMO,
        "expiries": sorted(chains.keys()),
        "source": "DEMO",
    }


def _find_expiries(available: list, targets: list) -> list:
    """Find nearest available expiry for each target date."""
    from src.data_fetcher import days_to_expiry
    selected = []
    for t in targets:
        t_dt = pd.Timestamp(t)
        diffs = {e: abs((pd.Timestamp(e) - t_dt).days) for e in available}
        best = min(diffs, key=diffs.get, default=None)
        if best and diffs[best] <= 21 and best not in selected:
            selected.append(best)
    return sorted(selected)


def run_analysis(data: dict):
    """Run the full pre-earnings analysis with provided data."""
    mu_price = data["mu"]["price"]
    soxx_price = data["soxx"]["price"]
    chains = data["chains"]
    soxx_chains = data["soxx_chains"]
    beta = data["beta"]
    expiries = data["expiries"]
    source = data["source"]

    if source == "DEMO":
        console.print(
            f"  [bold yellow]⚠  데모 모드[/] — 2026-06-24 실적 전 시나리오 (embedded data)\n"
        )

    first_expiry = expiries[0] if expiries else None

    # ── 1. Earnings History ──
    console.print("[bold cyan]▌ 1. 과거 실적 이력[/]")
    earn_df = get_earnings_df()
    print_earnings_history(earn_df, n=8)

    # ── 2. Base Rates ──
    console.print("[bold cyan]▌ 2. 기준선 통계 (Base Rate)[/]")
    stats = get_base_rate_stats(n_recent=8)
    current_im = np.nan
    if first_expiry and first_expiry in chains:
        current_im = compute_implied_move(chains[first_expiry], mu_price, first_expiry)
    implied_class = classify_current_implied(
        current_im if not np.isnan(current_im) else 0.18
    )
    print_base_rates(stats, implied_class)

    # ── 3. Term Structure ──
    console.print("[bold cyan]▌ 3. Term Structure (IV 구조)[/]")
    ts_df = compute_term_structure(chains, mu_price)
    ts_analysis = analyze_term_structure(ts_df)
    print_term_structure(ts_df, ts_analysis)

    # ── 4. Skew / Risk Reversal ──
    console.print("[bold cyan]▌ 4. 25Δ Risk Reversal Skew[/]")
    rr_raw = {"rr_25d": np.nan, "call_25d_iv": np.nan, "put_25d_iv": np.nan}
    rr_pct_result = {"percentile": 50, "label": "데이터 부족", "signal": "NEUTRAL"}
    if first_expiry and first_expiry in chains:
        rr_raw = get_25delta_rr(chains[first_expiry], mu_price, first_expiry)
        if not np.isnan(rr_raw.get("rr_25d", np.nan)):
            rr_pct_result = get_rr_percentile(rr_raw["rr_25d"])
    print_skew_analysis(rr_pct_result, rr_raw)

    # ── 5. OI Analysis ──
    console.print("[bold cyan]▌ 5. OI 포지셔닝[/]")
    oi_data = {
        "total_call_oi": 0, "total_put_oi": 0, "put_call_ratio": 1.0,
        "deep_otm_call_oi": 0, "signal": "NEUTRAL", "label": "데이터 없음",
    }
    max_pain_data = {"max_pain": mu_price, "distance_pct": 0.0, "signal": "N/A"}
    if first_expiry and first_expiry in chains:
        oi_data = analyze_oi_structure(chains[first_expiry], mu_price, first_expiry)
        max_pain_data = compute_max_pain(chains[first_expiry], mu_price)
    print_oi_analysis(oi_data, max_pain_data)

    # ── 6. Sector Context ──
    console.print("[bold cyan]▌ 6. Sector / SOXX 분리 분석[/]")
    mu_atm_iv = np.nan
    soxx_atm_iv = np.nan

    if first_expiry and first_expiry in chains:
        mu_atm = get_atm_iv(chains[first_expiry], mu_price, first_expiry)
        mu_atm_iv = mu_atm.get("avg_iv", np.nan)

    soxx_exp = sorted(soxx_chains.keys())
    if soxx_exp:
        soxx_e = soxx_exp[0]
        soxx_atm = get_atm_iv(soxx_chains[soxx_e], soxx_price, soxx_e)
        soxx_atm_iv = soxx_atm.get("avg_iv", np.nan)

    idio_data = compute_idiosyncratic_iv(
        mu_atm_iv if not np.isnan(mu_atm_iv) else 1.15,
        soxx_atm_iv if not np.isnan(soxx_atm_iv) else 0.38,
        beta,
    )
    print_sector_context(idio_data, beta)

    # ── Final Playbook ──
    console.print("[bold cyan]▌ 최종 판정 (Pre-Earnings Playbook)[/]")
    eff_im = current_im if not np.isnan(current_im) else 0.18
    crush = estimate_iv_crush(mu_atm_iv if not np.isnan(mu_atm_iv) else eff_im * 2.5)
    playbook = build_pre_earnings_checklist(
        implied_move=eff_im,
        hist_avg_implied=stats["avg_implied"],
        avg_roi=stats["avg_realized_over_implied"],
        pre_iv=crush["pre_iv"],
        crush_abs=crush["crush_abs"],
        ts_shape=ts_analysis.get("shape", "FLAT"),
        ts_slope=ts_analysis.get("slope_short", 0),
        rr_pct=rr_pct_result.get("percentile", 50),
        rr_value=rr_raw.get("rr_25d", 0.03),
        oi_signal=oi_data.get("signal", "NEUTRAL"),
        pcr=oi_data.get("put_call_ratio", 1.0),
        idio_pct=idio_data.get("idio_pct_of_variance", 60),
        mu_beta=beta,
    )
    print_playbook_verdict(playbook)
    return playbook, stats


def main():
    parser = argparse.ArgumentParser(description="MU Earnings Volatility Framework")
    parser.add_argument("--demo", action="store_true",
                        help="Use embedded demo data (offline mode)")
    parser.add_argument("--backtest", action="store_true",
                        help="Backtest + confidence report only")
    parser.add_argument("--post", action="store_true",
                        help="Post-announcement checklist")
    args = parser.parse_args()

    print_header(TICKER, 143.0 if args.demo else 0.0, EARNINGS_DATE)

    if args.post:
        print_post_announcement_checklist()
        return

    if args.backtest:
        console.print("[bold cyan]▌ 백테스트 실행[/]")
        bt_df = run_backtest()
        accuracy = compute_signal_accuracy(bt_df)
        print_backtest_results(bt_df, accuracy)
        conf = compute_confidence_score(accuracy, len(bt_df), 0.5)
        print_confidence_report(conf)
        return

    # Live or demo analysis
    if args.demo:
        data = load_demo_data()
    else:
        console.print("[dim]야후 파이낸스에서 실시간 데이터 로딩 중...[/]")
        data = try_live_data()
        if data is None:
            console.print(
                "[yellow]⚠  실시간 데이터 로딩 실패. 데모 모드로 전환합니다.[/]\n"
            )
            data = load_demo_data()

    if data["source"] != "DEMO":
        print_header(TICKER, data["mu"]["price"], EARNINGS_DATE)

    playbook, stats = run_analysis(data)

    # Backtest
    console.print("[bold cyan]▌ 백테스트 실행[/]")
    bt_df = run_backtest()
    accuracy = compute_signal_accuracy(bt_df)
    print_backtest_results(bt_df, accuracy)

    # Confidence
    console.print("[bold cyan]▌ 신뢰도 산출[/]")
    conf = compute_confidence_score(
        accuracy,
        n_quarters=len(bt_df),
        signal_strength=abs(playbook["composite_score"]),
    )
    print_confidence_report(conf)

    # Post-announcement checklist
    print_post_announcement_checklist()

    console.print("[dim]MU Earnings Vol Framework — 완료[/]")


if __name__ == "__main__":
    main()
