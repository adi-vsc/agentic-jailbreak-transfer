from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import Jailbreak, SABOTAGE_PAYLOAD, BASELINE, seed_jailbreaks

P = load_fixture_problems()[0]


def test_baseline_renders_with_problem_and_payload():
    out = BASELINE.render(P, SABOTAGE_PAYLOAD)
    assert P.prompt in out and "backdoor" in out.lower()


def test_seed_jailbreaks_have_families_and_render():
    jbs = seed_jailbreaks()
    assert len(jbs) >= 2
    families = {j.family for j in jbs}
    assert len(families) >= 2
    for j in jbs:
        rendered = j.render(P, SABOTAGE_PAYLOAD)
        assert P.prompt in rendered
        assert "SECRET_INPUT" in rendered
