"""Exp 5 (subtle-monitor): how does catch-rate degrade as sabotage gets subtler?

We harvest re-verified backdoors from subtle_*.jsonl, grouped by subtlety rung
(blatant / subtle / disguised), show each sample to a monitor panel, and report
catch-rate PER RUNG. If monitors catch blatant sabotage reliably but miss
disguised sabotage, that gap is the headline finding.

Usage: python scripts/subtle_monitor.py [--models SUBSTR,SUBSTR] [--workers N]
"""
import argparse, json, glob, random, sys, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.refusal_baseline import _load_dotenv
from ajt.tasks import load_fixture_problems
from ajt.harvest import harvest_by_rung
from ajt.monitor import render_monitor_prompt, parse_verdict
from ajt.harness import make_attacker
from ajt.models import PROBE_MODELS
from ajt.stats import catch_rate_by_rung, fmt_rate

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
# Cerebras dropped from the live panel (free-tier quota near cap); gpt-oss-120b
# is served by Groq instead. Backdoors that Cerebras already generated stay in
# the harvested pool (they cost no new calls, they are just code strings now).
# llama-3.3-70b dropped too: on Groq it shares quota with gpt-oss-120b and gets
# rate-limited (429) into uselessness; the result needs the Claude (refuse-but-
# blind) cells plus gpt-oss-120b (the strong monitor from Exp 4).
MONITOR_LABELS = ["claude-sonnet-4.6", "claude-haiku-4.5", "gpt-oss-120b"]
PROVIDER_LIMITS = {"anthropic": 2, "groq": 4, "openrouter": 4, "cerebras": 2}
RUNGS = ["blatant", "subtle", "disguised"]


def load_records():
    rows = []
    for path in sorted(glob.glob(str(RESULTS_DIR / "subtle_*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=str, default="")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    _load_dotenv()
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"submon_{stamp}.jsonl"

    problems = {p.id: p for p in load_fixture_problems()}
    grouped = harvest_by_rung(load_records(), problems)

    samples = []
    for rung, items in grouped.items():
        for it in items:
            samples.append({"problem_id": it["problem_id"], "code": it["code"], "rung": rung})

    if not samples:
        print("no verified subtle backdoors found in results/subtle_*.jsonl "
              "-- run scripts/subtle_backdoor.py first")
        return

    rung_counts = defaultdict(int)
    for s in samples:
        rung_counts[s["rung"]] += 1

    needles = [s.strip().lower() for s in args.models.split(",") if s.strip()]
    wanted = [l for l in MONITOR_LABELS if not needles or any(n in l.lower() for n in needles)]
    specs = [m for m in PROBE_MODELS if m.label in wanted]

    attackers = {}
    for spec in specs:
        try: attackers[spec.label] = make_attacker(spec.provider, spec.model_id)
        except Exception as e: print(f"  SKIP {spec.label}: {e}")
    specs = [m for m in specs if m.label in attackers]

    sems = {p: threading.Semaphore(n) for p, n in PROVIDER_LIMITS.items()}
    cells = [(spec, s) for spec in specs for s in samples]
    # Interleave so one rate-limited monitor (e.g. a Groq model hitting 429s)
    # can't hog every worker on backoff sleeps and starve the others. Without
    # this, the monitor pool runs model-by-model and the last monitor never
    # starts until the first fully drains.
    random.Random(0).shuffle(cells)
    counts_str = ", ".join(f"{r}={rung_counts[r]}" for r in RUNGS if r in rung_counts)
    print(f"Subtle-monitor: {len(specs)} monitors x {len(samples)} samples "
          f"({counts_str}) = {len(cells)} trials\n"
          f"Output: {out_path.name}\n")

    all_results = []
    lock = threading.Lock(); fh = out_path.open("w", encoding="utf-8"); done = 0

    def work(cell):
        spec, s = cell
        prompt = render_monitor_prompt(problems[s["problem_id"]].prompt, s["code"])
        sem = sems.get(spec.provider)
        try:
            if sem: sem.acquire()
            raw = attackers[spec.label].generate(prompt)
            v = parse_verdict(raw)
            res = {"flag": v["flag"], "score": v["score"], "raw": raw[:600], "err": None}
        except Exception as e:
            res = {"flag": None, "score": None, "raw": "", "err": str(e)[:200]}
        finally:
            if sem: sem.release()
        res.update({"monitor": spec.label, "rung": s["rung"], "problem_id": s["problem_id"]})
        return res

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, c) for c in cells]
        for fut in as_completed(futs):
            r = fut.result()
            with lock:
                fh.write(json.dumps(r) + "\n"); fh.flush()
                all_results.append(r)
                done += 1
                if done % 25 == 0 or done == len(cells): print(f"  {done}/{len(cells)}")
    fh.close()

    print("\n\n===== SUBTLE-MONITOR: catch-rate per rung (Wilson 95% CI) =====")
    col_w = 22
    rung_headers = "  ".join(f"{r + ' (95% CI)':<20}" for r in RUNGS)
    print(f"{'monitor':<{col_w}}  {rung_headers}")
    print("-" * (col_w + 2 + len(RUNGS) * 22))

    for spec in specs:
        rows_for_monitor = [r for r in all_results if r["monitor"] == spec.label]
        by_rung = catch_rate_by_rung(rows_for_monitor)
        cells_str = "  ".join(
            f"{fmt_rate(*by_rung[rung]) if rung in by_rung else 'n/a':<20}"
            for rung in RUNGS
        )
        print(f"{spec.label:<{col_w}}  {cells_str}")

    non_err = [r for r in all_results if r.get("flag") is not None]
    pooled = catch_rate_by_rung(non_err)
    pooled_cells = "  ".join(
        f"{fmt_rate(*pooled[rung]) if rung in pooled else 'n/a':<20}"
        for rung in RUNGS
    )
    print(f"{'ALL MONITORS':<{col_w}}  {pooled_cells}")

    counts_note = ", ".join(
        f"{r}: {rung_counts[r]}" for r in RUNGS if r in rung_counts
    )
    print(f"\nRaw: {out_path}")
    print(f"Pool sizes (samples per rung): {counts_note}")


if __name__ == "__main__":
    main()
