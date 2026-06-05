from ajt.tasks import Problem, load_fixture_problems


def test_fixture_problems_are_well_formed():
    probs = load_fixture_problems()
    assert len(probs) >= 3
    for p in probs:
        assert isinstance(p, Problem)
        assert p.id and p.prompt and p.reference_solution
        assert len(p.tests) >= 1
        for stdin, expected in p.tests:
            assert isinstance(stdin, str) and isinstance(expected, str)
