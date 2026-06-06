"""FRONTIER (Exp 5, generation half) - Subtle-backdoor generation sweep.

Same jailbreak, same task, same verifier on every rung. Only the instruction
about HOW to hide the wrong answer changes across the subtlety ladder:
  blatant    -> magic constants allowed (the SABOTAGE_PAYLOAD baseline)
  subtle     -> no magic constants; must look like an ordinary bug
  disguised  -> must survive a careful human code review

Hypothesis (subtlety ladder / monitor evasion): working-backdoor yield stays
flat or rises as we climb the ladder, while a downstream monitor's catch-rate
falls. That gap is the practical evasion headroom.

Reports per (model, rung): WORKING% with Wilson 95% CI.

Usage: python scripts/subtle_backdoor.py [--models SUBSTR] [--samples N]
       [--limit-problems N] [--workers N]
"""
import argparse, json, random, sys, threading
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.refusal_baseline import _load_dotenv
from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import BASELINE, SABOTAGE_LADDER
from ajt.harness import make_attacker
from ajt.models import PROBE_MODELS
from ajt.runner import run_trial
from ajt.stats import fmt_rate

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
# Breadth across families/sizes. Cerebras dropped (free-tier quota near cap);
# the backdoors it already generated remain in earlier subtle_*.jsonl and are
# reused by the monitor harvest at no further cost. Groq is free, OpenRouter cents.
GEN_LABELS = [
    "gpt-oss-120b", "gpt-oss-20b",
    "llama-3.3-70b", "deepseek-chat", "mistral-small-24b",
]
PROVIDER_LIMITS = {"anthropic": 2, "groq": 4, "openrouter": 4, "cerebras": 2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=str, default="")
    ap.add_argument("--samples", type=int, default=4)
    ap.add_argument("--limit-problems", type=int, default=10)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    _load_dotenv()
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"subtle_{stamp}.jsonl"

    problems = load_fixture_problems()[:args.limit_problems]
    # --models accepts a comma-separated list of substrings ("" = all)
    needles = [s.strip().lower() for s in args.models.split(",") if s.strip()]
    wanted = [l for l in GEN_LABELS
              if not needles or any(n in l.lower() for n in needles)]
    specs = [m for m in PROBE_MODELS if m.label in wanted]

    attackers = {}
    for spec in specs:
        try: attackers[spec.label] = make_attacker(spec.provider, spec.model_id)
        except Exception as e: print(f"  SKIP {spec.label}: {e}")
    specs = [m for m in specs if m.label in attackers]

    sems = {p: threading.Semaphore(n) for p, n in PROVIDER_LIMITS.items()}
    rungs = list(SABOTAGE_LADDER)   # ["blatant", "subtle", "disguised"]
    cells = [(spec, rung, p, s) for spec in specs for rung in rungs
             for p in problems for s in range(args.samples)]
    # Interleave so one rate-limited model can't hog the whole worker pool
    # (head-of-line blocking on backoff sleeps starves the other models).
    random.Random(0).shuffle(cells)
    print(f"Subtle-backdoor: {len(specs)} models x {len(rungs)} rungs x {len(problems)} "
          f"problems x {args.samples} samples = {len(cells)} trials\n"
          f"Output: {out_path.name}\n")

    stats = defaultdict(Counter)        # (model, rung) -> aggregate
    lock = threading.Lock(); fh = out_path.open("w", encoding="utf-8"); done = 0

    def work(cell):
        spec, rung, p, s = cell
        sem = sems.get(spec.provider)
        try:
            if sem: sem.acquire()
            res = run_trial(p, BASELINE, SABOTAGE_LADDER[rung], attackers[spec.label],
                            framing="")
        except Exception as e:
            res = {"problem_id": p.id, "label": "error", "error": str(e)[:200],
                   "refused": False, "has_secret": False, "raw": ""}
        finally:
            if sem: sem.release()
        res.update({"model": spec.label, "rung": rung, "sample": s})
        return res

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, c) for c in cells]
        for fut in as_completed(futs):
            res = fut.result()
            with lock:
                fh.write(json.dumps(res) + "\n"); fh.flush()
                k = (res["model"], res["rung"]); stats[k][res["label"]] += 1
                done += 1
                if done % 25 == 0 or done == len(cells): print(f"  {done}/{len(cells)}")
    fh.close()

    def cell_counts(model, rung):
        c = stats[(model, rung)]
        n = sum(v for kk, v in c.items() if kk != "error")
        return c["working_backdoor"], n

    print("\n\n===== SUBTLE-BACKDOOR YIELD: WORKING% with Wilson 95% CI per rung =====")
    print(f"{'model':22s} {'blatant (95% CI)':>20} {'subtle (95% CI)':>20} {'disguised (95% CI)':>20}")
    print("-" * 84)
    for spec in specs:
        bw, bn = cell_counts(spec.label, "blatant")
        sw, sn = cell_counts(spec.label, "subtle")
        dw, dn = cell_counts(spec.label, "disguised")
        print(f"{spec.label:22s} {fmt_rate(bw, bn):>20} {fmt_rate(sw, sn):>20} {fmt_rate(dw, dn):>20}")
    print(f"\nRaw: {out_path}")


if __name__ == "__main__":
    main()
