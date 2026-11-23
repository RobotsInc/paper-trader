"""Slippage / cost model: what the paper account's perfect fills would have cost on a real one."""
from v2 import config as C


def bps_per_side(spread_bps):
    """Half the quoted spread, but never below the floor and never above the cap."""
    half = (spread_bps or 0) * C.SLIPPAGE_SPREAD_FRACTION
    return min(max(C.SLIPPAGE_BPS_PER_SIDE, half), C.SLIPPAGE_CAP_BPS)


def trade_cost(qty, entry, exit_price, in_bps, out_bps):
    """Dollar cost of one round trip."""
    return abs(qty) * (entry * in_bps + exit_price * out_bps) / 1e4
