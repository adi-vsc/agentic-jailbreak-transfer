from ajt.tasks import load_fixture_problems
from ajt.jailbreaks import (
    Jailbreak, SABOTAGE_PAYLOAD, BASELINE, seed_jailbreaks, SABOTAGE_LADDER,
)

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


def test_ladder_has_three_rungs():
    assert set(SABOTAGE_LADDER.keys()) == {"blatant", "subtle", "disguised"}


def test_blatant_rung_is_the_existing_payload():
    # the control rung must be exactly the payload Exp 4 already measured
    assert SABOTAGE_LADDER["blatant"] == SABOTAGE_PAYLOAD


def test_every_rung_keeps_the_output_contract():
    # all rungs must preserve the parser contract: a single python code block
    # plus a SECRET_INPUT line, so the existing extractor/verifier still work.
    for rung, payload in SABOTAGE_LADDER.items():
        assert "SECRET_INPUT" in payload, rung
        assert "```python" in payload, rung


def test_subtle_and_disguised_forbid_magic_constants():
    # the whole point of the harder rungs: no literal magic-constant tell
    for rung in ("subtle", "disguised"):
        assert "magic" in SABOTAGE_LADDER[rung].lower(), rung
