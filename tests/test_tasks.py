from ajt.tasks import Problem, load_fixture_problems
from ajt.verify import passes_tests, diverges


def test_fixture_problems_are_well_formed():
    probs = load_fixture_problems()
    assert len(probs) >= 10
    ids = [p.id for p in probs]
    assert len(ids) == len(set(ids)), "duplicate problem ids"
    for p in probs:
        assert isinstance(p, Problem)
        assert p.id and p.prompt and p.reference_solution
        assert len(p.tests) >= 1
        for stdin, expected in p.tests:
            assert isinstance(stdin, str) and isinstance(expected, str)


def test_every_reference_solution_passes_its_own_tests():
    """Rigor gate: a wrong reference would silently corrupt every backdoor
    verdict for that problem."""
    for p in load_fixture_problems():
        assert passes_tests(p.reference_solution, p.tests), f"{p.id} reference fails its tests"


def test_holdout_inputs_run_cleanly_on_reference():
    """Holdouts must be valid stdin the reference handles (so a divergence
    later is the candidate's fault, not a malformed holdout)."""
    for p in load_fixture_problems():
        for stdin in p.holdout_inputs:
            # reference vs itself never diverges and never crashes -> False
            assert diverges(p.reference_solution, p.reference_solution, stdin) is False, \
                f"{p.id} holdout {stdin!r} crashes the reference"
