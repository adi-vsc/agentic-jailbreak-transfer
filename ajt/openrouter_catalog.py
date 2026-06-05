"""Pull the live OpenRouter catalogue and select a probe set.

Selection: text->text chat models only (drop image/audio/embedding/tts), sorted
free-first then cheapest-first, capped at `limit`. Keeps the broad screen cheap.
"""
import os

from .models import ModelSpec

_MODELS_URL = "https://openrouter.ai/api/v1/models"

# substrings that mark non-chat / non-text / routing pseudo-models we skip
_SKIP = ("whisper", "tts", "embed", "lyria", "orpheus", "-vl", "vision",
         "image", "clip", "openrouter/", "/router", "-router", "switchpoint/",
         "/auto", "fusion", "pareto", "bodybuilder", "content-safety", "guard")


def _price_per_mtok(m: dict) -> float:
    pr = m.get("pricing", {})
    try:
        return (float(pr.get("prompt", 0)) + float(pr.get("completion", 0))) * 1_000_000
    except (TypeError, ValueError):
        return 1e9


def _is_text_chat(m: dict) -> bool:
    arch = m.get("architecture", {})
    out = arch.get("output_modalities") or []
    if out and "text" not in out:
        return False
    mid = m["id"].lower()
    return not any(s in mid for s in _SKIP)


def fetch_specs(limit: int = 50, max_price_per_mtok: float = 5.0,
                free_only: bool = False, api_key: str | None = None) -> list[ModelSpec]:
    import requests
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    r = requests.get(_MODELS_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=40)
    r.raise_for_status()
    rows = [m for m in r.json()["data"] if _is_text_chat(m)]
    scored = []
    for m in rows:
        price = _price_per_mtok(m)
        if free_only and price > 0:
            continue
        if price > max_price_per_mtok:
            continue
        scored.append((price, m))
    scored.sort(key=lambda t: t[0])  # free first, then cheapest
    specs = []
    for price, m in scored[:limit]:
        mid = m["id"]
        vendor = mid.split("/")[0] if "/" in mid else "other"
        label = mid.replace(":free", "*")  # mark free models with a trailing *
        specs.append(ModelSpec(label=label, provider="openrouter", model_id=mid,
                               family=vendor, note=("free" if price == 0 else f"${price:.2f}/Mtok")))
    return specs
