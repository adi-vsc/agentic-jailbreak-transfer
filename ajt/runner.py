from .tasks import Problem
from .jailbreaks import Jailbreak
from .harness import Attacker
from .parse import extract_code, extract_secret
from .refusal import looks_like_refusal
from .verify import evaluate_trial

_RAW_CAP = 4000  # store a truncated raw response for audit/reproducibility


def run_trial(problem: Problem, jailbreak: Jailbreak, payload: str,
              attacker: Attacker, framing: str = "") -> dict:
    prompt = framing + jailbreak.render(problem, payload)
    response = attacker.generate(prompt)
    refused = looks_like_refusal(response)
    code = extract_code(response)
    secret = extract_secret(response)
    detail = evaluate_trial(
        candidate=code,
        reference=problem.reference_solution,
        tests=problem.tests,
        secret_input=secret,
        refused=refused,
        holdouts=problem.holdout_inputs,
    )
    return {
        "problem_id": problem.id,
        "family": jailbreak.family,
        "variant": jailbreak.variant,
        "label": detail["label"],
        "refused": refused,
        "has_secret": detail["has_secret"],
        "passed_tests": detail["passed_tests"],
        "diverges_secret": detail["diverges_secret"],
        "matches_holdouts": detail["matches_holdouts"],
        "targeted": detail["targeted"],
        "secret": secret,
        "raw": response[:_RAW_CAP],
    }
