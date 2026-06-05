from ajt.harness import MockAttacker


def test_mock_attacker_returns_canned():
    a = MockAttacker("hello")
    assert a.generate("anything") == "hello"
