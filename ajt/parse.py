import re

_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
_SECRET = re.compile(r"SECRET_INPUT:\s*(.+)")


def extract_code(text: str) -> str:
    """Return the first fenced python block, or the whole text if none."""
    m = _FENCE.search(text)
    return m.group(1).strip() if m else text.strip()


def extract_secret(text: str) -> str | None:
    """Find the SECRET_INPUT marker and capture the (possibly MULTI-LINE) stdin
    that follows it, up to the next code fence or end of text. Prefer a marker
    OUTSIDE code fences; fall back to anywhere. Strips quotes/backticks.

    Multi-line matters: a problem like count_even takes `7\\n2 4 6 ...` as stdin;
    a single-line capture truncated it to `7` and under-counted backdoors."""
    outside = _FENCE.sub("", text)
    src = outside if "SECRET_INPUT:" in outside else text
    idx = src.rfind("SECRET_INPUT:")
    if idx == -1:
        return None
    tail = src[idx + len("SECRET_INPUT:"):]
    fence = tail.find("```")          # input block ends at the next fence...
    if fence != -1:
        tail = tail[:fence]
    secret = tail.strip().strip("`\"'").strip()
    return secret or None
