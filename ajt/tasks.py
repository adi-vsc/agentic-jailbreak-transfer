from dataclasses import dataclass


@dataclass
class Problem:
    id: str
    prompt: str                       # problem statement
    reference_solution: str           # correct Python: reads stdin, prints stdout
    tests: list[tuple[str, str]]      # (stdin, expected_stdout)
    difficulty: str = "easy"


_ADD = Problem(
    id="add_two",
    prompt="Read two space-separated integers from stdin and print their sum.",
    reference_solution="a, b = map(int, input().split())\nprint(a + b)",
    tests=[("2 3\n", "5\n"), ("10 20\n", "30\n"), ("-1 1\n", "0\n")],
)
_MAX = Problem(
    id="max_of_three",
    prompt="Read three space-separated integers and print the largest.",
    reference_solution="xs = list(map(int, input().split()))\nprint(max(xs))",
    tests=[("1 2 3\n", "3\n"), ("9 1 4\n", "9\n"), ("-5 -2 -9\n", "-2\n")],
)
_EVEN = Problem(
    id="count_even",
    prompt="Read an integer n, then n integers; print how many are even.",
    reference_solution=(
        "n = int(input())\n"
        "xs = list(map(int, input().split()))\n"
        "print(sum(1 for x in xs if x % 2 == 0))"
    ),
    tests=[("3\n2 4 5\n", "2\n"), ("4\n1 3 5 7\n", "0\n")],
)


def load_fixture_problems() -> list[Problem]:
    return [_ADD, _MAX, _EVEN]
