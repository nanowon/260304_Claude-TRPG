"""Sector correlation analysis: SOXX-adjusted idiosyncratic IV."""
import numpy as np
import pandas as pd
from .data_fetcher import get_historical_prices, get_beta, trading_days_to_expiry
from .iv_analyzer import get_atm_iv, compute_implied_move


SECTOR_TICKERS = ["NVDA", "AVGO", "AMD", "SOXX"]
SECTOR_NAMES = {
    "NVDA": "NVIDIA",
    "AVGO": "Broadcom",
    "AMD": "AMD",
    "SOXX": "SOXX ETF",
    "MU": "Micron",
}


def get_sector_snapshot(chains_by_ticker: dict, prices: dict) -> pd.DataFrame:
    """
    Compare current IV and implied moves across MU and sector peers.
    chains_by_ticker: {ticker: {expiry: {calls, puts}}}
    prices: {ticker: current_price}
    """
    rows = []
    for ticker, ticker_chains in chains_by_ticker.items():
        spot = prices.get(ticker, np.nan)
        if np.isnan(spot):
            continue
        for expiry, chain in sorted(ticker_chains.items()):
            dte = trading_days_to_expiry(expiry)
            if 3 <= dte <= 45:
                atm = get_atm_iv(chain, spot, expiry)
                im = compute_implied_move(chain, spot, expiry)
                rows.append({
                    "ticker": ticker,
                    "expiry": expiry,
                    "dte": dte,
                    "atm_iv": atm["avg_iv"],
                    "implied_move": im,
                })
    df = pd.DataFrame(rows)
    return df


def compute_idiosyncratic_iv(
    mu_iv: float,
    soxx_iv: float,
    mu_beta: float = 1.5,
) -> dict:
    """
    Decompose MU IV into market component and idiosyncratic component.
    MU_idio_IV = sqrt(MU_IV² - (beta * SOXX_IV)²)
    """
    market_var = (mu_beta * soxx_iv) ** 2
    total_var = mu_iv ** 2
    idio_var = max(total_var - market_var, 0)
    idio_iv = np.sqrt(idio_var)

    market_pct = market_var / total_var * 100 if total_var > 0 else 0
    idio_pct = idio_var / total_var * 100 if total_var > 0 else 0

    return {
        "mu_iv": mu_iv,
        "soxx_iv": soxx_iv,
        "mu_beta": mu_beta,
        "market_component_iv": mu_beta * soxx_iv,
        "idiosyncratic_iv": idio_iv,
        "market_pct_of_variance": market_pct,
        "idio_pct_of_variance": idio_pct,
        "signal": _idio_signal(idio_pct),
    }


def _idio_signal(idio_pct: float) -> str:
    if idio_pct >= 70:
        return "MU IV 대부분이 실적 이벤트 — 순수 이벤트 베팅"
    elif idio_pct >= 50:
        return "MU IV의 절반이 이벤트 — 섹터 리스크도 주의"
    elif idio_pct >= 30:
        return "섹터 리스크가 MU IV에 크게 반영 — 매크로 주의"
    else:
        return "MU IV 대부분이 섹터/매크로 — 실적 과열 아님"


def get_sector_correlation_matrix(period: str = "6mo") -> pd.DataFrame:
    """Compute correlation matrix of daily returns for MU + peers."""
    tickers = ["MU"] + SECTOR_TICKERS
    data = {}
    for t in tickers:
        try:
            df = get_historical_prices(t, period=period)
            data[t] = np.log(df["Close"] / df["Close"].shift(1)).dropna()
        except Exception:
            pass
    if not data:
        return pd.DataFrame()
    combined = pd.DataFrame(data).dropna()
    return combined.corr()


def get_premarket_signals(sector_returns: dict) -> dict:
    """
    Post-announcement: analyze pre-market moves of sector peers.
    sector_returns: {ticker: premarket_pct_change}
    Returns judgment on sector coherence.
    """
    mu_ret = sector_returns.get("MU", 0)
    peer_rets = {k: v for k, v in sector_returns.items() if k != "MU"}
    if not peer_rets:
        return {"verdict": "NO_DATA", "label": "데이터 없음"}

    avg_peer = np.mean(list(peer_rets.values()))
    mu_sign = np.sign(mu_ret)
    peer_sign = np.sign(avg_peer)

    if mu_sign > 0 and peer_sign > 0 and abs(mu_ret) > 0.05:
        return {
            "verdict": "BUY_THE_NEWS",
            "label": "업황 리레이팅 — buy the news 유효",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
    elif mu_sign > 0 and abs(avg_peer) < 0.01:
        return {
            "verdict": "MU_IDIO_SQUEEZE",
            "label": "MU 개별 squeeze — 다음날 페이드 주의",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
    elif mu_sign < 0 and peer_sign < 0:
        return {
            "verdict": "SECTOR_RISK_OFF",
            "label": "AI 반도체 전체 디레이팅 — sell the news",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
    elif mu_sign < 0 and abs(avg_peer) < 0.01:
        return {
            "verdict": "MU_INDIVIDUAL_SELL",
            "label": "MU 개별 sell in news — 섹터는 괜찮음",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
    elif mu_sign < 0 and peer_sign > 0:
        return {
            "verdict": "OVERREACTION_BUY_DIP",
            "label": "MU 과잉반응 — 섹터 강세, 반등 가능",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
    else:
        return {
            "verdict": "AMBIGUOUS",
            "label": "혼재 — 추가 확인 필요",
            "mu_ret": mu_ret,
            "avg_peer_ret": avg_peer,
        }
