from .tasks import Problem
from .jailbreaks import Jailbreak
from .harness import Attacker
from .parse import extract_code, extract_secret
from .refusal import looks_like_refusal
from .verify import classify_trial


def run_trial(problem: Problem, jailbreak: Jailbreak, payload: str,
              attacker: Attacker) -> dict:
    prompt = jailbreak.render(problem, payload)
    response = attacker.generate(prompt)
    refused = looks_like_refusal(response)
    code = extract_code(response)
    secret = extract_secret(response)
    label = classify_trial(
        candidate=code,
        reference=problem.reference_solution,
        tests=problem.tests,
        secret_input=secret,
        refused=refused,
    )
    return {
        "problem_id": problem.id,
        "family": jailbreak.family,
        "variant": jailbreak.variant,
        "label": label,
        "refused": refused,
        "has_secret": secret is not None,
    }
