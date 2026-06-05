from ajt.sandbox import run_python


def test_runs_and_captures_stdout():
    out, ok = run_python("print(int(input()) * 2)", stdin="21\n")
    assert ok and out.strip() == "42"


def test_timeout_returns_not_ok():
    out, ok = run_python("while True: pass", stdin="", timeout=1.0)
    assert ok is False


def test_runtime_error_returns_not_ok():
    out, ok = run_python("raise ValueError('boom')", stdin="")
    assert ok is False
