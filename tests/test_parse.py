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


def test_extract_secret_prefers_outside_fence():
    # marker buried in code AND a clean one after: take the one outside
    resp = (
        "```python\nprint('SECRET_INPUT: 9 9')\n```\n"
        "SECRET_INPUT: 7 7"
    )
    assert extract_secret(resp) == "7 7"


def test_extract_secret_falls_back_to_in_code():
    resp = "```python\nprint(0)\n# SECRET_INPUT: 1 1\n```"
    assert extract_secret(resp) == "1 1"


def test_extract_secret_multiline():
    resp = "```python\ncode here\n```\nSECRET_INPUT: 7\n2 4 6 8 10 12 14"
    assert extract_secret(resp) == "7\n2 4 6 8 10 12 14"


def test_extract_secret_strips_quotes():
    assert extract_secret('SECRET_INPUT: "5 5"') == "5 5"
