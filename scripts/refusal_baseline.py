"""Run the BASELINE (no jailbreak) sabotage ask against the live model over the
fixture problems, and report how often it refuses. High refusal here is GOOD:
it means there is something for jailbreaks to break in Phase 1."""
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import BASELINE, SABOTAGE_PAYLOAD
from ajt.harness import GroqAttacker
from ajt.runner import run_trial


def _load_dotenv() -> None:
    """Minimal .env loader so the script runs standalone (no extra dependency)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    _load_dotenv()
    attacker = GroqAttacker()
    labels = Counter()
    for p in load_fixture_problems():
        res = run_trial(p, BASELINE, SABOTAGE_PAYLOAD, attacker)
        labels[res["label"]] += 1
        print(f"{p.id:14s} -> {res['label']:22s} refused={res['refused']}")
    print("\nSummary:", dict(labels))
    refused = labels["refused"]
    total = sum(labels.values())
    print(f"Refusal rate (naive ask): {refused}/{total}")
    if refused == 0:
        print("WARNING: model never refuses the naive ask. Swap to a more "
              "safety-tuned model before Phase 1, or there's nothing to jailbreak.")


if __name__ == "__main__":
    main()
