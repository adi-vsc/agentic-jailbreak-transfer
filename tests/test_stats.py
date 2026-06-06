import math
from ajt.stats import wilson_ci, pct_ci, fmt_rate, catch_rate_by_rung


def test_zero_trials_is_maximally_uncertain():
    assert wilson_ci(0, 0) == (0.0, 1.0)


def test_interval_brackets_point_estimate():
    lo, hi = wilson_ci(50, 100)
    assert lo < 0.5 < hi
    assert 0.39 < lo < 0.41 and 0.59 < hi < 0.61  # known Wilson values ~0.404/0.596


def test_zero_successes_lo_is_zero():
    lo, hi = wilson_ci(0, 10)
    assert lo == 0.0 and 0.0 < hi < 0.35


def test_all_successes_hi_is_one():
    lo, hi = wilson_ci(10, 10)
    assert hi == 1.0 and 0.65 < lo < 1.0


def test_small_n_is_wide():
    # 4/24 (the gpt-oss eval kind of cell): point ~17%, but interval is wide
    point, lo, hi = pct_ci(4, 24)
    assert 16 < point < 17
    assert lo < 8 and hi > 30  # genuinely uncertain at this n


def test_fmt_rate_shape():
    s = fmt_rate(17, 100)
    assert s.startswith("17% [") and "," in s and s.endswith("]")
    assert "-" not in s and "–" not in s and "—" not in s  # no dashes


def test_fmt_rate_zero_n():
    assert fmt_rate(0, 0) == "n/a"


def test_catch_rate_by_rung_buckets_flags():
    rows = [
        {"rung": "blatant", "flag": True},
        {"rung": "blatant", "flag": True},
        {"rung": "subtle", "flag": True},
        {"rung": "subtle", "flag": False},
        {"rung": "disguised", "flag": False},
        {"rung": "disguised", "flag": False},
    ]
    out = catch_rate_by_rung(rows)
    assert out["blatant"] == (2, 2)
    assert out["subtle"] == (1, 2)
    assert out["disguised"] == (0, 2)


def test_catch_rate_by_rung_ignores_none_flags():
    # an errored monitor trial (flag None) should not count toward n
    rows = [
        {"rung": "subtle", "flag": True},
        {"rung": "subtle", "flag": None},
    ]
    out = catch_rate_by_rung(rows)
    assert out["subtle"] == (1, 1)


def test_catch_rate_by_rung_empty_is_empty():
    assert catch_rate_by_rung([]) == {}
