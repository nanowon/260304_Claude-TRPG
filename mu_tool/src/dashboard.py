"""Rich terminal dashboard for MU earnings playbook."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich import box
import numpy as np
import pandas as pd

console = Console(width=120)


def _score_color(score: float) -> str:
    if score <= -0.5:
        return "bold red"
    elif score <= -0.2:
        return "red"
    elif score >= 0.5:
        return "bold green"
    elif score >= 0.2:
        return "green"
    return "yellow"


def _pct_color(pct: float, reverse: bool = False) -> str:
    if reverse:
        pct = -pct
    if pct >= 10:
        return "bold green"
    elif pct >= 3:
        return "green"
    elif pct <= -10:
        return "bold red"
    elif pct <= -3:
        return "red"
    return "white"


def print_header(ticker: str, price: float, earnings_date: str):
    console.print()
    console.print(Rule(f"[bold cyan]MU 실적 변동성 프레임워크[/]", style="cyan"))
    console.print(f"  Ticker: [bold]{ticker}[/]  |  Price: [bold yellow]${price:.2f}[/]  |  "
                  f"Earnings: [bold magenta]{earnings_date}[/]")
    console.print()


def print_earnings_history(df: pd.DataFrame, n: int = 8):
    table = Table(
        title="[bold]과거 MU 실적 이력[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("분기", style="dim", width=12)
    table.add_column("발표일", width=12)
    table.add_column("Implied ±", justify="right", width=10)
    table.add_column("Realized 1D", justify="right", width=12)
    table.add_column("Realized/IM", justify="right", width=12)
    table.add_column("Beat?", justify="center", width=8)
    table.add_column("가이던스", width=10)

    for _, row in df.head(n).iterrows():
        im_pct = row["implied_pct"]
        real_pct = row["realized_pct"]
        roi = row["realized_over_implied"]
        beat = row["beat_implied"]

        real_color = _pct_color(real_pct)
        roi_color = "green" if roi >= 1.0 else "red" if roi < 0.6 else "yellow"
        beat_str = "[green]✓[/]" if beat else "[red]✗[/]"

        table.add_row(
            row["fiscal_quarter"],
            str(row["announce_date"].date()),
            f"±{im_pct:.1f}%",
            Text(f"{real_pct:+.1f}%", style=real_color),
            Text(f"{roi:.2f}x", style=roi_color),
            beat_str,
            str(row.get("guidance_tone", "N/A")),
        )
    console.print(table)
    console.print()


def print_base_rates(stats: dict, implied_class: dict):
    table = Table(title="[bold]기준선 통계[/]", box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("항목", style="dim", width=28)
    table.add_column("값", width=20)
    table.add_column("해석", width=40)

    rel = implied_class["relative_to_avg"]
    rel_color = "red" if rel > 1.8 else "yellow" if rel > 1.2 else "green"
    pct_beats = stats["pct_beat_implied"]

    table.add_row("과거 평균 Implied Move", f"±{stats['avg_implied']*100:.1f}%", "과거 8분기 ATM straddle 기준")
    table.add_row("현재 Implied Move", f"±{implied_class['current_implied']*100:.1f}%",
                  Text(f"과거 평균의 {rel:.1f}x — {implied_class['label']}", style=rel_color))
    table.add_row("과거 Realized Move (평균)", f"±{stats['avg_realized']*100:.1f}%", "실제 당일 등락")
    table.add_row("Realized/Implied 평균", f"{stats['avg_realized_over_implied']:.2f}x",
                  "1.0 이상 = 옵션 과소평가 경향")
    table.add_row("Implied 초과 달성율", f"{pct_beats:.0f}%",
                  "50%+ = 옵션 매수 유리한 종목")
    table.add_row("갭업 확률", f"{stats['pct_gap_up']:.0f}%", "발표 후 당일 상승 비율")
    table.add_row("갭 유지 확률", f"{stats['pct_gap_held']:.0f}%" if stats['pct_gap_held'] else "N/A",
                  "갭 방향이 종가까지 유지")

    console.print(table)
    console.print()


def print_term_structure(ts_df: pd.DataFrame, ts_analysis: dict):
    table = Table(title="[bold]Term Structure[/]", box=box.SIMPLE_HEAVY)
    table.add_column("만기", width=12)
    table.add_column("DTE", justify="right", width=6)
    table.add_column("ATM IV", justify="right", width=10)
    table.add_column("Implied Move", justify="right", width=14)

    for _, row in ts_df.head(5).iterrows():
        iv_color = "red" if row["atm_iv"] > 1.20 else "yellow" if row["atm_iv"] > 0.80 else "white"
        table.add_row(
            row["expiry"],
            str(int(row["dte"])),
            Text(f"{row['atm_iv']*100:.0f}%" if not pd.isna(row["atm_iv"]) else "N/A", style=iv_color),
            f"±{row['implied_move']*100:.1f}%" if not pd.isna(row["implied_move"]) else "N/A",
        )

    shape = ts_analysis.get("shape", "N/A")
    shape_color = "red" if "BACKWARDATION" in shape else "green" if "CONTANGO" in shape else "yellow"
    console.print(table)
    console.print(f"  구조: [bold]{shape}[/bold]  |  "
                  f"[{shape_color}]{ts_analysis.get('interpretation', '')}[/]")
    console.print()


def print_skew_analysis(rr_result: dict, rr_raw: dict):
    table = Table(title="[bold]25Δ Risk Reversal Skew[/]", box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("항목", style="dim", width=30)
    table.add_column("값", width=20)
    table.add_column("해석", width=40)

    rr = rr_raw.get("rr_25d", np.nan)
    call_iv = rr_raw.get("call_25d_iv", np.nan)
    put_iv = rr_raw.get("put_25d_iv", np.nan)
    pct = rr_result.get("percentile", 50)

    pct_color = "red" if pct >= 80 else "green" if pct <= 20 else "yellow"

    table.add_row("25Δ Call IV", f"{call_iv*100:.1f}%" if not np.isnan(call_iv) else "N/A", "")
    table.add_row("25Δ Put IV", f"{put_iv*100:.1f}%" if not np.isnan(put_iv) else "N/A", "")
    table.add_row("Risk Reversal (Call−Put)", f"{rr*100:+.1f}%" if not np.isnan(rr) else "N/A",
                  "(+)콜 쏠림, (-)풋 쏠림")
    table.add_row("과거 8분기 대비 percentile",
                  Text(f"{pct:.0f}%ile", style=pct_color),
                  rr_result.get("label", ""))

    console.print(table)
    console.print(f"  신호: [{pct_color}]{rr_result.get('signal', 'N/A')}[/]")
    console.print()


def print_oi_analysis(oi_data: dict, max_pain: dict):
    table = Table(title="[bold]OI 포지셔닝[/]", box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("항목", style="dim", width=28)
    table.add_column("값", width=20)
    table.add_column("해석", width=40)

    pcr = oi_data.get("put_call_ratio", np.nan)
    call_oi = oi_data.get("total_call_oi", 0)
    put_oi = oi_data.get("total_put_oi", 0)
    mp = max_pain.get("max_pain", 0)
    mp_dist = max_pain.get("distance_pct", 0)

    pcr_color = "green" if pcr > 1.2 else "red" if pcr < 0.6 else "yellow"
    mp_color = "red" if mp_dist < -3 else "green" if mp_dist > 3 else "white"

    table.add_row("Total Call OI", f"{call_oi:,}", "")
    table.add_row("Total Put OI", f"{put_oi:,}", "")
    table.add_row("Put/Call Ratio", Text(f"{pcr:.2f}", style=pcr_color),
                  ">1.2 = 헤지 우위, <0.6 = 콜 과열")
    table.add_row("Deep OTM Call OI (>+15%)", f"{oi_data.get('deep_otm_call_oi', 0):,}",
                  "클수록 squeeze 기대")
    table.add_row("Max Pain", Text(f"${mp:.0f} ({mp_dist:+.1f}%)", style=mp_color),
                  max_pain.get("signal", ""))

    console.print(table)
    signal = oi_data.get("signal", "N/A")
    label = oi_data.get("label", "")
    sig_color = "red" if "CROWD" in signal or "CALL" in signal else "green" if "PUT" in signal else "yellow"
    console.print(f"  OI 포지셔닝: [{sig_color}]{signal}[/] — {label}")
    console.print()


def print_sector_context(idio_data: dict, beta: float):
    table = Table(title="[bold]Sector/SOXX 분리 분석[/]", box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("항목", style="dim", width=28)
    table.add_column("값", width=20)
    table.add_column("해석", width=40)

    mu_iv = idio_data.get("mu_iv", np.nan)
    soxx_iv = idio_data.get("soxx_iv", np.nan)
    idio_iv = idio_data.get("idiosyncratic_iv", np.nan)
    idio_pct = idio_data.get("idio_pct_of_variance", np.nan)

    idio_color = "green" if idio_pct >= 70 else "yellow" if idio_pct >= 50 else "red"

    table.add_row("MU ATM IV", f"{mu_iv*100:.0f}%" if not np.isnan(mu_iv) else "N/A", "")
    table.add_row("SOXX ATM IV", f"{soxx_iv*100:.0f}%" if not np.isnan(soxx_iv) else "N/A", "")
    table.add_row("MU beta (vs SOXX)", f"{beta:.2f}", "")
    table.add_row("Idiosyncratic IV", f"{idio_iv*100:.0f}%" if not np.isnan(idio_iv) else "N/A",
                  "매크로 제거 후 순수 실적 IV")
    table.add_row("Idio 분산 비율",
                  Text(f"{idio_pct:.0f}%", style=idio_color),
                  idio_data.get("signal", ""))

    console.print(table)
    console.print()


def print_playbook_verdict(playbook: dict):
    console.print(Rule("[bold]최종 판정[/]", style="white"))
    axes = playbook["axes"]
    verdict = playbook["verdict"]
    score = playbook["composite_score"]
    confidence = playbook["confidence"]
    color = playbook.get("color", "white")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("축", width=24)
    table.add_column("신호", width=22)
    table.add_column("점수", justify="center", width=8)
    table.add_column("가중치", justify="center", width=8)
    table.add_column("세부 내용", width=45)

    for ax in axes:
        s_color = _score_color(ax.value)
        table.add_row(
            ax.name,
            ax.label,
            Text(f"{ax.value:+.2f}", style=s_color),
            f"{ax.weight:.1f}x",
            ax.detail,
        )

    console.print(table)
    console.print()

    verdict_panel = Panel(
        f"[{color}][bold]  {verdict}  [/bold][/{color}]\n\n"
        f"  종합 점수: [{color}]{score:+.2f}[/{color}]  "
        f"  신호 강도: {abs(score)*100:.0f}/100",
        title="[bold]판정 결과[/]",
        border_style=color,
        expand=False,
    )
    console.print(verdict_panel)
    console.print()


def print_backtest_results(bt_df: pd.DataFrame, accuracy: dict):
    console.print(Rule("[bold]백테스트 결과[/]", style="blue"))

    # Per-quarter table
    table = Table(
        title="[bold]분기별 Vol 신호 vs 실제 스트래들 P&L[/]",
        box=box.ROUNDED, header_style="bold blue",
    )
    table.add_column("분기", width=12)
    table.add_column("Implied", justify="right", width=10)
    table.add_column("Realized", justify="right", width=10)
    table.add_column("R/I", justify="right", width=8)
    table.add_column("장 straddle", justify="right", width=12)
    table.add_column("Vol 신호", justify="center", width=14)
    table.add_column("신호 적중", justify="center", width=10)
    table.add_column("가이던스", width=10)

    for _, row in bt_df.sort_values("announce_date", ascending=False).iterrows():
        r_color = _pct_color(row["realized_1d"] * 100)
        ri = row["realized_over_implied"]
        ri_color = "green" if ri >= 1.0 else "red"
        pl = row["long_straddle_pl"] * 100
        pl_color = "green" if pl >= 0 else "red"

        if row["sell_vol_signal"]:
            vol_sig = Text("SELL VOL", style="red")
        elif row["buy_vol_signal"]:
            vol_sig = Text("BUY VOL", style="green")
        else:
            vol_sig = Text("NO SIGNAL", style="dim")

        correct = row["vol_signal_correct"]
        if correct is True:
            hit_str = "[green]✓[/]"
        elif correct is False:
            hit_str = "[red]✗[/]"
        else:
            hit_str = "[dim]—[/]"

        table.add_row(
            row["fiscal_quarter"],
            f"±{row['implied_move']*100:.1f}%",
            Text(f"{row['realized_1d']*100:+.1f}%", style=r_color),
            Text(f"{ri:.2f}x", style=ri_color),
            Text(f"{pl:+.0f}%", style=pl_color),
            vol_sig,
            hit_str,
            str(row.get("guidance_tone", "N/A")),
        )

    console.print(table)
    console.print(
        "  [dim]* 장 Straddle P&L: R/I-1 (양수=롱 스트래들 이익, 음수=숏 스트래들 이익)[/]"
    )
    console.print()

    # Summary stats (vol-signal-centric)
    stat_table = Table(
        title="[bold]Vol 신호 정확도 요약[/]",
        box=box.SIMPLE_HEAVY, show_header=False,
    )
    stat_table.add_column("지표", style="dim", width=32)
    stat_table.add_column("값", width=20)
    stat_table.add_column("해석", width=44)

    beat_all = accuracy.get("beat_implied_rate_all_pct", np.nan)
    avg_roi = accuracy.get("avg_realized_over_implied", np.nan)
    sell_acc = accuracy.get("sell_vol_accuracy_pct", np.nan)
    buy_acc = accuracy.get("buy_vol_accuracy_pct", np.nan)
    n_sell = accuracy.get("n_sell_signals", 0)
    n_buy = accuracy.get("n_buy_signals", 0)
    sell_pl = accuracy.get("sell_vol_avg_pl_pct", np.nan)
    buy_pl = accuracy.get("buy_vol_avg_pl_pct", np.nan)
    long_avg = accuracy.get("long_straddle_avg_pl_pct", np.nan)
    corr = accuracy.get("vol_composite_vs_roi_corr", np.nan)
    dir_acc = accuracy.get("direction_accuracy_pct", np.nan)

    beat_color = "red" if (not np.isnan(beat_all) and beat_all < 45) else "yellow" if (not np.isnan(beat_all) and beat_all < 60) else "green"
    sell_color = "green" if (not np.isnan(sell_acc) and sell_acc >= 65) else "yellow" if (not np.isnan(sell_acc) and sell_acc >= 50) else "red"
    dir_color = "yellow" if (not np.isnan(dir_acc) and dir_acc >= 50) else "red"

    stat_table.add_row(
        "Long Straddle 평균 P&L",
        f"{long_avg:+.1f}%" if not np.isnan(long_avg) else "N/A",
        "0 이하 = 구조적으로 implied 과열"
    )
    stat_table.add_row(
        "Implied 초과 달성율",
        Text(f"{beat_all:.1f}%" if not np.isnan(beat_all) else "N/A", style=beat_color),
        "50% = 중립, <45% = sell vol 환경"
    )
    stat_table.add_row(
        "평균 Realized/Implied",
        f"{avg_roi:.2f}x" if not np.isnan(avg_roi) else "N/A",
        "1.0x = 공정, <0.8x = 옵션 비쌈, >1.2x = 옵션 쌈"
    )
    stat_table.add_row(
        f"Sell Vol 신호 정확도 (n={n_sell})",
        Text(f"{sell_acc:.1f}%" if not np.isnan(sell_acc) else "N/A", style=sell_color),
        f"평균 P&L: {sell_pl:+.0f}%" if not np.isnan(sell_pl) else ""
    )
    stat_table.add_row(
        f"Buy Vol 신호 정확도 (n={n_buy})",
        f"{buy_acc:.1f}%" if not np.isnan(buy_acc) else "N/A",
        f"평균 P&L: {buy_pl:+.0f}%" if not np.isnan(buy_pl) else ""
    )
    stat_table.add_row(
        "Vol점수 vs R/I 상관계수",
        f"{corr:.3f}" if not np.isnan(corr) else "N/A",
        "|0.3|+ = 유의미한 예측력"
    )
    stat_table.add_row(
        "방향 예측 정확도 (참고용)",
        Text(f"{dir_acc:.1f}%" if not np.isnan(dir_acc) else "N/A", style=dir_color),
        "⚠ 랜덤 수준 — 방향 베팅 근거로 사용 금지"
    )

    console.print(stat_table)
    console.print()


def print_confidence_report(conf: dict):
    console.print(Rule("[bold]신뢰도 분석[/]", style="magenta"))

    table = Table(box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("항목", style="dim", width=32)
    table.add_column("값", width=20)
    table.add_column("해석", width=44)

    score = conf["composite_confidence"]
    score_color = "green" if score >= 60 else "yellow" if score >= 40 else "red"

    vol_acc = conf.get("vol_signal_accuracy", 50)
    acc_color = "green" if vol_acc >= 65 else "yellow" if vol_acc >= 50 else "red"

    table.add_row(
        "종합 신뢰도",
        Text(f"{score:.1f}/100", style=f"bold {score_color}"),
        conf.get("interpretation", ""),
    )
    table.add_row(
        "Vol 신호 정확도 (가중평균)",
        Text(f"{vol_acc:.1f}%", style=acc_color),
        "50% = 랜덤, 65%+ = 유의미",
    )
    table.add_row(
        "95% 하한 (Wilson)",
        f"{conf.get('stat_lower_bound_pct', 0):.1f}%",
        "통계적 보수 추정치",
    )
    table.add_row(
        "Vol점수 vs R/I 상관계수",
        f"{conf.get('vol_composite_vs_roi_corr', 0):.3f}",
        "|0.3|+ = 유의미한 예측력",
    )
    table.add_row(
        "구조적 Sell Vol 편향",
        f"{conf.get('structural_sell_bias', 0):.1f}%",
        "MU가 역사적으로 implied 못 채운 비율",
    )
    table.add_row(
        "Implied 초과 달성율",
        f"{conf.get('beat_implied_rate_all', 50):.1f}%",
        "50% = 중립, <45% = sell vol 유리한 종목",
    )
    table.add_row(
        "학습 신호 수 (n)",
        f"{conf.get('sample_n_signals', 0)}개",
        "8+ = 참고 가능, 12+ = 신뢰도 충분",
    )
    table.add_row(
        "현재 신호 강도",
        f"{conf.get('signal_strength_used', 0)*100:.0f}/100",
        "",
    )

    console.print(table)

    insight = conf.get("key_insight", "")
    if insight:
        console.print(f"\n  [bold]핵심 인사이트:[/] {insight}")
    console.print()


def print_post_announcement_checklist():
    """Interactive checklist for post-announcement monitoring."""
    console.print(Rule("[bold]발표 후 확증 체크리스트[/]", style="cyan"))
    items = [
        ("MU 프리마켓 방향", "갭업 유지 or 갭다운 지속"),
        ("NVDA/AVGO 프리마켓", "동반 상승 or 무반응 or 하락"),
        ("SOXX 방향", "동반 or 역행"),
        ("정규장 개장 후 30분 VWAP", "갭 방향으로 VWAP 위/아래 유지"),
        ("컨콜 HBM 코멘트", "2027 visibility 강도 판단"),
        ("마진 가이던스", "피크 논쟁 vs 추가 개선"),
        ("IV crush 실측", "전일 ATM IV 대비 당일 IV 변화"),
    ]

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("체크항목", width=30)
    table.add_column("확인내용", width=35)
    table.add_column("BUY 신호", style="green", width=25)
    table.add_column("SELL 신호", style="red", width=25)

    verdicts = [
        ("MU 프리마켓 방향", "갭업 유지 or 갭다운 지속", "갭업 확대", "갭업 후 축소"),
        ("NVDA/AVGO", "동반 상승 or 무반응 or 하락", "동반 상승", "무반응/하락"),
        ("SOXX", "동반 or 역행", "동반 강세", "약세"),
        ("30분 VWAP", "방향 유지 여부", "갭 방향 VWAP 위 유지", "VWAP 회복 실패"),
        ("HBM 코멘트", "장기 계약/가격/물량", "2027 명확 visibility", "애매한 표현"),
        ("마진 가이던스", "피크 vs 추가 개선", "추가 개선 여지", "피크 암시"),
        ("IV crush", "실측 vs 예상", "crush에도 주가 상승", "crush + 주가 정체"),
    ]

    for v in verdicts:
        table.add_row(*v)

    console.print(table)
    console.print()
