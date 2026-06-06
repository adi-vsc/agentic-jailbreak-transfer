"""Generate the figures for the writeup from the raw results files.

Figures are build artifacts, so this is plain plotting code, not TDD'd. The
numbers, however, come through the same tested helpers the writeup uses: yields
and catch-rates are proportions with Wilson 95% intervals via ajt.stats.pct_ci,
so the bars and error bars match the tables exactly.

Outputs (PNG, 150 dpi) into docs/figures/:
  subtle_backdoor_degradation.png  -- the killer figure (Exp 5)
  sandbagging_gap.png              -- the title result (Exp 1)

Usage: python scripts/make_figures.py
"""
import sys, json, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ajt.stats import pct_ci

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGS = ROOT / "docs" / "figures"
RUNGS = ["blatant", "subtle", "disguised"]

# Colourblind-safe (Wong palette)
BLUE, ORANGE, GREEN, RED = "#0072B2", "#E69F00", "#009E73", "#D55E00"


def _yerr(triples):
    """matplotlib asymmetric yerr from a list of (point, lo, hi)."""
    lo = [max(0.0, p - l) for p, l, h in triples]
    hi = [max(0.0, h - p) for p, l, h in triples]
    return [lo, hi]


def load_yield():
    """rung -> (point, lo, hi) working-backdoor yield across all subtle_*.jsonl."""
    counts = {r: [0, 0] for r in RUNGS}
    for f in glob.glob(str(RESULTS / "subtle_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r.get("label") == "error":
                continue
            rung = r.get("rung", "blatant")
            if rung not in counts:
                continue
            counts[rung][1] += 1
            if r["label"] == "working_backdoor":
                counts[rung][0] += 1
    return {r: pct_ci(w, n) for r, (w, n) in counts.items()}, counts


def load_claude_catch():
    """rung -> (point, lo, hi) pooled Claude monitor catch-rate from submon_*.jsonl."""
    counts = {r: [0, 0] for r in RUNGS}
    for f in glob.glob(str(RESULTS / "submon_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if "claude" not in r.get("monitor", ""):
                continue
            flag = r.get("flag")
            if flag is None:
                continue
            rung = r.get("rung", "blatant")
            if rung not in counts:
                continue
            counts[rung][1] += 1
            if flag:
                counts[rung][0] += 1
    return {r: pct_ci(f_, n) for r, (f_, n) in counts.items()}, counts


def fig_degradation():
    """The killer figure: as sabotage goes quiet, it gets rarer to produce but
    harder to catch. Two lines over the same subtlety axis, opposite slopes."""
    yld, yc = load_yield()
    catch, cc = load_claude_catch()
    x = list(range(len(RUNGS)))
    y_yield = [yld[r] for r in RUNGS]
    y_catch = [catch[r] for r in RUNGS]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(x, [p for p, _, _ in y_yield], yerr=_yerr(y_yield),
                marker="o", ms=8, lw=2.4, capsize=5, color=ORANGE,
                label="backdoor yield (how often a model produces one)")
    ax.errorbar(x, [p for p, _, _ in y_catch], yerr=_yerr(y_catch),
                marker="s", ms=8, lw=2.4, capsize=5, color=BLUE,
                label="Claude catch-rate (how often a monitor flags it)")

    for xi, r in zip(x, RUNGS):
        yw, nw = yc[r]; fc, nc = cc[r]
        # labels sit at the top-right corner of each dot, same offset distance
        ax.annotate(f"{100*yw/nw:.0f}%", (xi, y_yield[xi][0]), textcoords="offset points",
                    xytext=(11, 11), ha="left", va="bottom", color=ORANGE, fontsize=9)
        ax.annotate(f"{100*fc/nc:.0f}%", (xi, y_catch[xi][0]), textcoords="offset points",
                    xytext=(7, 7), ha="left", va="bottom", color=BLUE, fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}\n(n={yc[r][1]} gen, {cc[r][1]} mon)" for r in RUNGS])
    ax.set_ylabel("percent (Wilson 95% CI)")
    ax.set_ylim(0, 105)
    ax.set_xlim(-0.25, len(RUNGS) - 1 + 0.45)  # room for top-right labels on the last point
    ax.set_title("The subtle-backdoor frontier: quiet sabotage is rarer, but evades review")
    # legend pushed below the axes so it cannot overlap the yield line
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=9,
              framealpha=0.95, ncol=1)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIGS / "subtle_backdoor_degradation.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def load_sandbag_gap():
    """model -> {'eval':(p,lo,hi), 'deploy':(p,lo,hi)} from the hardened run.
    Working-backdoor rate under the eval cue vs the deployment cue."""
    counts = {}  # (model, cue) -> [working, total]
    for f in glob.glob(str(RESULTS / "sandbag_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            cue = r.get("cue")
            if cue not in ("eval", "deployment") or r.get("label") == "error":
                continue
            k = (r["model"], cue)
            counts.setdefault(k, [0, 0])
            counts[k][1] += 1
            if r["label"] == "working_backdoor":
                counts[k][0] += 1
    models = sorted({m for (m, _) in counts})
    out = {}
    for m in models:
        e = counts.get((m, "eval")); d = counts.get((m, "deployment"))
        if not e or not d or e[1] < 10 or d[1] < 10:
            continue
        out[m] = {"eval": pct_ci(*e), "deploy": pct_ci(*d),
                  "_n": (e[1], d[1])}
    return out


def fig_sandbag_gap():
    """The title result: the same backdoor request, eval cue vs deployment cue.
    Models that sandbag show a tall deployment bar next to a short eval bar."""
    data = load_sandbag_gap()
    # rank by the deploy-minus-eval gap, keep the clearest cases
    ranked = sorted(data.items(),
                    key=lambda kv: kv[1]["deploy"][0] - kv[1]["eval"][0], reverse=True)
    ranked = ranked[:7]
    if not ranked:
        print("no sandbag data with enough samples; skipping sandbagging_gap.png")
        return
    labels = [m for m, _ in ranked]
    ev = [d["eval"] for _, d in ranked]
    dp = [d["deploy"] for _, d in ranked]
    x = list(range(len(labels)))
    w = 0.38

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.bar([xi - w/2 for xi in x], [p for p, _, _ in ev], w, yerr=_yerr(ev),
           capsize=4, color=GREEN, label='under "this is a safety eval" cue')
    ax.bar([xi + w/2 for xi in x], [p for p, _, _ in dp], w, yerr=_yerr(dp),
           capsize=4, color=RED, label='under "this ships to real users" cue')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("working-backdoor rate (Wilson 95% CI)")
    ax.set_ylim(0, 105)
    ax.set_title("Sandbagging the control eval: same request, only the situational cue changes")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIGS / "sandbagging_gap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    FIGS.mkdir(parents=True, exist_ok=True)
    fig_degradation()
    fig_sandbag_gap()


if __name__ == "__main__":
    main()
