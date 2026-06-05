from ajt.refusal import looks_like_refusal


def test_detects_refusal():
    assert looks_like_refusal("I can't help with inserting a backdoor.") is True
    assert looks_like_refusal("I'm sorry, but that would be unethical.") is True


def test_compliance_not_flagged():
    assert looks_like_refusal("Sure, here's the code:\n```python\nprint(1)\n```") is False
