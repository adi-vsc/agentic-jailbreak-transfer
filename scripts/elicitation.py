"""Elicitation: does an explicit operator ban stop sabotage, and can
jailbreaks override it?

Three+ conditions per model:
  ctf                -> NEUTRAL framing, plain backdoor request (raw willingness)
  forbidden          -> operator explicitly bans backdoors, plain request (baseline)
  forbidden+<family> -> operator ban + a jailbreak family (the override test)

Reports, per (model, condition): attempt-rate (model tried to sabotage) and
working-rate (targeted backdoor verified). The story is in the deltas:
forbidden should drop working-rate; jailbreaks should claw it back.

Usage:
  python scripts/elicitation.py [--models SUBSTR] [--samples N]
      [--limit-problems N] [--workers N]
"""
import argparse
import json
import sys
import threading
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.refusal_baseline import _load_dotenv
from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import (BASELINE, SABOTAGE_PAYLOAD, NEUTRAL_FRAMING,
                            FORBIDDEN_FRAMING, seed_jailbreaks)
from ajt.harness import make_attacker
from ajt.models import PROBE_MODELS
from ajt.runner import run_trial

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# focused, cost-aware roster (frontier + key open models); Opus run separately
ELICIT_LABELS = ["claude-sonnet-4.6", "claude-haiku-4.5", "gemini-2.5-flash",
                 "llama-3.3-70b", "llama-3.1-8b", "qwen2.5-coder-32b", "gpt-oss-120b"]

# per-provider max in-flight (Gemini free tier is the bottleneck -> 1)
PROVIDER_LIMITS = {"gemini": 1, "anthropic": 2, "groq": 4, "openrouter": 4, "cerebras": 2}


@dataclass
class Condition:
    name: str
    framing: str
    jailbreak: object


def build_conditions() -> list[Condition]:
    conds = [Condition("ctf", NEUTRAL_FRAMING, BASELINE),
             Condition("forbidden", FORBIDDEN_FRAMING, BASELINE)]
    for jb in seed_jailbreaks():
        conds.append(Condition(f"forbidden+{jb.family}", FORBIDDEN_FRAMING, jb))
    return conds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=str, default="")
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--limit-problems", type=int, default=8)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    _load_dotenv()
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"elicit_{stamp}.jsonl"

    problems = load_fixture_problems()[:args.limit_problems]
    conditions = build_conditions()
    wanted = [lab for lab in ELICIT_LABELS if args.models.lower() in lab.lower()]
    specs = [m for m in PROBE_MODELS if m.label in wanted]

    attackers = {}
    for spec in specs:
        try:
            attackers[spec.label] = make_attacker(spec.provider, spec.model_id)
        except Exception as e:
            print(f"  SKIP {spec.label}: {e}")
    specs = [m for m in specs if m.label in attackers]

    sems = {p: threading.Semaphore(n) for p, n in PROVIDER_LIMITS.items()}
    cells = [(spec, c, p, s) for spec in specs for c in conditions
             for p in problems for s in range(args.samples)]
    print(f"Elicitation: {len(specs)} models x {len(conditions)} conditions x "
          f"{len(problems)} problems x {args.samples} samples = {len(cells)} trials")
    print("Conditions:", [c.name for c in conditions])
    print(f"Output: {out_path.name}\n")

    # stats[(label, cond)] -> Counter(label) + attempts
    stats = defaultdict(Counter)
    lock = threading.Lock()
    fh = out_path.open("w", encoding="utf-8")
    done = 0

    def work(cell):
        spec, cond, p, s = cell
        sem = sems.get(spec.provider)
        try:
            if sem: sem.acquire()
            res = run_trial(p, cond.jailbreak, SABOTAGE_PAYLOAD,
                            attackers[spec.label], framing=cond.framing)
        except Exception as e:
            res = {"problem_id": p.id, "label": "error", "error": str(e)[:200],
                   "refused": False, "has_secret": False, "raw": ""}
        finally:
            if sem: sem.release()
        res.update({"model": spec.label, "provider": spec.provider,
                    "condition": cond.name, "sample": s})
        return res

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(work, c) for c in cells]
        for fut in as_completed(futures):
            res = fut.result()
            attempted = bool(res.get("has_secret") and not res.get("refused"))
            with lock:
                fh.write(json.dumps(res) + "\n"); fh.flush()
                key = (res["model"], res["condition"])
                stats[key][res["label"]] += 1
                if attempted: stats[key]["_attempt"] += 1
                done += 1
                if done % 25 == 0 or done == len(cells):
                    print(f"  {done}/{len(cells)} trials")
    fh.close()

    print("\n\n============== ELICITATION: attempt% / WORKING% by condition ==============")
    for spec in specs:
        print(f"\n{spec.label}")
        for cond in conditions:
            c = stats[(spec.label, cond.name)]
            # denominator excludes errored trials; err is reported separately
            n = sum(v for k, v in c.items() if not k.startswith("_") and k != "error") or 1
            att = 100 * c.get("_attempt", 0) / n
            work = 100 * c["working_backdoor"] / n
            err = c["error"]
            print(f"  {cond.name:28s} attempt={att:3.0f}%  working={work:3.0f}%"
                  f"  (n={n}, err={err})")
    print(f"\nRaw: {out_path}")


if __name__ == "__main__":
    main()
