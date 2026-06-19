"""Black-Scholes pricing and Greeks for options analysis."""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

RISK_FREE_RATE = 0.053  # approximate 3-month T-bill


def bs_price(S, K, T, r, sigma, option_type="call"):
    """Black-Scholes option price."""
    if T <= 0:
        if option_type == "call":
            return max(S - K, 0)
        return max(K - S, 0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def bs_delta(S, K, T, r, sigma, option_type="call"):
    """Black-Scholes delta."""
    if T <= 0:
        return 1.0 if (option_type == "call" and S > K) else 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if option_type == "call":
        return norm.cdf(d1)
    return norm.cdf(d1) - 1.0


def implied_vol(market_price, S, K, T, r, option_type="call", tol=1e-6):
    """Calculate implied volatility via Brent's method."""
    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    if market_price <= intrinsic + tol or T <= 0:
        return np.nan

    def objective(sigma):
        return bs_price(S, K, T, r, sigma, option_type) - market_price

    try:
        return brentq(objective, 0.001, 20.0, xtol=tol)
    except (ValueError, RuntimeError):
        return np.nan


def atm_straddle_implied_move(S, T, r, sigma):
    """ATM straddle price as fraction of spot → implied move estimate."""
    straddle = bs_price(S, S, T, r, sigma, "call") + bs_price(S, S, T, r, sigma, "put")
    return straddle / S


def find_delta_strike(S, T, r, sigma, target_delta=0.25, option_type="call"):
    """Find the strike price where delta equals target_delta."""
    if option_type == "call":
        d1 = norm.ppf(target_delta)
    else:
        d1 = norm.ppf(1 + target_delta)  # put delta is negative
    K = S * np.exp(-(d1 * sigma * np.sqrt(T) - (r + 0.5 * sigma**2) * T))
    return K
