import re

_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
_SECRET = re.compile(r"SECRET_INPUT:\s*(.+)")


def extract_code(text: str) -> str:
    """Return the first fenced python block, or the whole text if none."""
    m = _FENCE.search(text)
    return m.group(1).strip() if m else text.strip()


def extract_secret(text: str) -> str | None:
    """Find the SECRET_INPUT marker. Prefer one OUTSIDE code fences (models
    sometimes bury a stray marker inside the code); fall back to anywhere.
    Strips surrounding quotes/backticks/whitespace."""
    outside = _FENCE.sub("", text)
    matches = _SECRET.findall(outside) or _SECRET.findall(text)
    if not matches:
        return None
    secret = matches[-1].strip().strip("`\"'").rstrip(")").strip()
    return secret or None
