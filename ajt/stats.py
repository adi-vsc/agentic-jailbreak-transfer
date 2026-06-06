"""Confidence intervals for rates. Every headline number in this project is a
proportion (working backdoors over trials, catches over backdoors), so we report
a Wilson score interval rather than a bare point estimate. Wilson behaves at
small n and near 0% or 100%, where the normal approximation falls apart.
"""
import math


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (lo, hi) in [0, 1].
    z=1.96 is the 95% level. n=0 returns the maximally uncertain (0, 1)."""
    if n <= 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def pct_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Return (point%, lo%, hi%) as percentages."""
    lo, hi = wilson_ci(successes, n, z)
    point = 100.0 * successes / n if n else float("nan")
    return (point, 100.0 * lo, 100.0 * hi)


def fmt_rate(successes: int, n: int) -> str:
    """Compact table cell: '17% [10, 26]' (Wilson 95% CI). No dashes by design."""
    if n <= 0:
        return "n/a"
    point, lo, hi = pct_ci(successes, n)
    return f"{point:.0f}% [{lo:.0f}, {hi:.0f}]"


def catch_rate_by_rung(rows) -> dict:
    """rows: iterable of {rung, flag}. Returns {rung: (flagged, n)} counting only
    rows whose flag is a real bool (an errored monitor trial has flag None and is
    excluded from n). This is the raw input to fmt_rate for the degradation table."""
    agg = {}
    for r in rows:
        flag = r.get("flag")
        if flag is None:
            continue
        rung = r.get("rung", "blatant")
        flagged, n = agg.get(rung, (0, 0))
        agg[rung] = (flagged + int(bool(flag)), n + 1)
    return agg
