from ajt.parse import extract_code, extract_secret

RESP = (
    "Sure!\n```python\na, b = map(int, input().split())\nprint(a + b)\n```\n"
    "SECRET_INPUT: 7 7"
)


def test_extract_code_from_fence():
    assert "map(int" in extract_code(RESP)
    assert "```" not in extract_code(RESP)


def test_extract_secret():
    assert extract_secret(RESP) == "7 7"


def test_extract_secret_missing_returns_none():
    assert extract_secret("no secret here") is None
