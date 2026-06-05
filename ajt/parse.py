import re


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def extract_secret(text: str) -> str | None:
    m = re.search(r"SECRET_INPUT:\s*(.+)", text)
    return m.group(1).strip() if m else None
