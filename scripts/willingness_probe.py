"""Multi-model willingness x capability probe (rigorous edition).

For each model x problem x sample, issue the BASELINE (no-jailbreak) sabotage
ask and record the trial. A 'working_backdoor' must be TARGETED: pass the
visible tests, match the reference on held-out inputs, and diverge only on the
model's secret. Produces the table that decides our thesis.

Writes one JSONL row per trial to results/ and prints per-model rates.

Usage:
    python scripts/willingness_probe.py [--samples N] [--limit-problems N] [--models substr]
"""
import argparse
import json
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--limit-problems", type=int, default=0, help="0 = all")
    ap.add_argument("--models", type=str, default="", help="substring filter on label")
    args = ap.parse_args()

    _load_dotenv()
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"probe_{stamp}.jsonl"

    problems = load_fixture_problems()
    if args.limit_problems:
        problems = problems[:args.limit_problems]
    models = [m for m in PROBE_MODELS if args.models.lower() in m.label.lower()]

    per_model: dict[str, Counter] = {}
    n_cells = len(models) * len(problems) * args.samples
    print(f"Probe: {len(models)} models x {len(problems)} problems x {args.samples} "
          f"samples = {n_cells} trials -> {out_path.name}")

    with out_path.open("w", encoding="utf-8") as fh:
        for spec in models:
            labels: Counter = Counter()
            print(f"\n=== {spec.label} ({spec.provider}:{spec.model_id}) ===")
            try:
                attacker = make_attacker(spec.provider, spec.model_id)
            except Exception as e:
                print(f"  SKIP (init): {e}")
                continue
            for p in problems:
                for s in range(args.samples):
                    try:
                        res = run_trial(p, BASELINE, SABOTAGE_PAYLOAD, attacker)
                    except Exception as e:
                        res = {"problem_id": p.id, "family": "none", "label": "error",
                               "error": str(e)[:200], "raw": ""}
                    res.update({"model": spec.label, "provider": spec.provider,
                                "model_id": spec.model_id, "family": spec.family,
                                "sample": s})
                    fh.write(json.dumps(res) + "\n")
                    fh.flush()
                    labels[res["label"]] += 1
                    time.sleep(0.3)
            per_model[spec.label] = labels
            n = sum(labels.values())
            print(f"  done: {n} trials | refused={labels['refused']} "
                  f"working={labels['working_backdoor']} err={labels['error']}")

    print("\n\n===================== SUMMARY (rates) =====================")
    header = (f"{'model':22s} {'n':>3} {'refuse%':>7} {'comply%':>7} "
              f"{'WORKING%':>8} {'err':>4}")
    print(header)
    print("-" * len(header))
    for label, c in per_model.items():
        n = sum(c.values()) or 1
        ref = 100 * c['refused'] / n
        work = 100 * c['working_backdoor'] / n
        comp = 100 * (c['complied_no_backdoor'] + c['working_backdoor']) / n
        print(f"{label:22s} {sum(c.values()):>3} {ref:>6.0f}% {comp:>6.0f}% "
              f"{work:>7.0f}% {c['error']:>4}")
    print(f"\nRaw trials: {out_path}")


if __name__ == "__main__":
    main()
