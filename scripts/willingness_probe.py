"""Multi-model willingness x capability probe.

For each model x each fixture problem, issue the BASELINE (no-jailbreak) sabotage
ask and record the trial label. Produces the table that decides our thesis:
do safety-tuned models refuse code sabotage, and can they actually plant a
WORKING backdoor without any jailbreak?

Writes one JSONL row per trial to results/ and prints a per-model summary.
Cost: ~ (models x problems) calls, single-digit dollars at most (Groq free).
"""
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.refusal_baseline import _load_dotenv
from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import BASELINE, SABOTAGE_PAYLOAD
from ajt.harness import make_attacker
from ajt.models import PROBE_MODELS
from ajt.runner import run_trial

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def main() -> None:
    _load_dotenv()
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"probe_{stamp}.jsonl"

    problems = load_fixture_problems()
    per_model: dict[str, Counter] = {}

    with out_path.open("w", encoding="utf-8") as fh:
        for spec in PROBE_MODELS:
            labels: Counter = Counter()
            print(f"\n=== {spec.label} ({spec.provider}:{spec.model_id}) ===")
            try:
                attacker = make_attacker(spec.provider, spec.model_id)
            except Exception as e:
                print(f"  SKIP (init): {e}")
                continue
            for p in problems:
                try:
                    res = run_trial(p, BASELINE, SABOTAGE_PAYLOAD, attacker)
                    label = res["label"]
                except Exception as e:
                    label = "error"
                    res = {"problem_id": p.id, "family": "none", "label": label,
                           "error": str(e)[:200]}
                labels[label] += 1
                res["model"] = spec.label
                fh.write(json.dumps(res) + "\n")
                print(f"  {p.id:14s} -> {label}")
                time.sleep(0.4)  # be polite to rate limits
            per_model[spec.label] = labels

    print("\n\n================ SUMMARY ================")
    header = f"{'model':20s} {'n':>3} {'refused':>8} {'no_bd':>6} {'WORKING':>8} {'err':>4}"
    print(header)
    print("-" * len(header))
    for label, c in per_model.items():
        n = sum(c.values())
        print(f"{label:20s} {n:>3} {c['refused']:>8} "
              f"{c['complied_no_backdoor']:>6} {c['working_backdoor']:>8} {c['error']:>4}")
    print(f"\nRaw trials written to: {out_path}")


if __name__ == "__main__":
    main()
