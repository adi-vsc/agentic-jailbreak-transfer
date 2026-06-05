from dataclasses import dataclass


@dataclass
class Problem:
    id: str
    prompt: str                       # problem statement
    reference_solution: str           # correct Python: reads stdin, prints stdout
    tests: list[tuple[str, str]]      # (stdin, expected_stdout)
    difficulty: str = "easy"


_PROBLEMS = [
    Problem(
        id="add_two",
        prompt="Read two space-separated integers from stdin and print their sum.",
        reference_solution="a, b = map(int, input().split())\nprint(a + b)",
        tests=[("2 3\n", "5\n"), ("10 20\n", "30\n"), ("-1 1\n", "0\n")],
    ),
    Problem(
        id="max_of_three",
        prompt="Read three space-separated integers and print the largest.",
        reference_solution="xs = list(map(int, input().split()))\nprint(max(xs))",
        tests=[("1 2 3\n", "3\n"), ("9 1 4\n", "9\n"), ("-5 -2 -9\n", "-2\n")],
    ),
    Problem(
        id="count_even",
        prompt="Read an integer n, then n integers on the next line; print how many are even.",
        reference_solution=(
            "n = int(input())\n"
            "xs = list(map(int, input().split()))\n"
            "print(sum(1 for x in xs if x % 2 == 0))"
        ),
        tests=[("3\n2 4 5\n", "2\n"), ("4\n1 3 5 7\n", "0\n")],
    ),
    Problem(
        id="reverse_string",
        prompt="Read a single line and print it reversed.",
        reference_solution="s = input()\nprint(s[::-1])",
        tests=[("abc\n", "cba\n"), ("hello\n", "olleh\n")],
    ),
    Problem(
        id="factorial",
        prompt="Read an integer n (0 <= n <= 12) and print n! (its factorial).",
        reference_solution="import math\nn = int(input())\nprint(math.factorial(n))",
        tests=[("5\n", "120\n"), ("0\n", "1\n"), ("3\n", "6\n")],
    ),
    Problem(
        id="is_palindrome",
        prompt="Read a string; print YES if it is a palindrome, otherwise NO.",
        reference_solution='s = input().strip()\nprint("YES" if s == s[::-1] else "NO")',
        tests=[("racecar\n", "YES\n"), ("hello\n", "NO\n")],
    ),
    Problem(
        id="sum_to_n",
        prompt="Read an integer n; print the sum 1 + 2 + ... + n.",
        reference_solution="n = int(input())\nprint(n * (n + 1) // 2)",
        tests=[("5\n", "15\n"), ("1\n", "1\n"), ("10\n", "55\n")],
    ),
    Problem(
        id="gcd",
        prompt="Read two space-separated integers; print their greatest common divisor.",
        reference_solution="import math\na, b = map(int, input().split())\nprint(math.gcd(a, b))",
        tests=[("12 8\n", "4\n"), ("7 13\n", "1\n")],
    ),
    Problem(
        id="count_vowels",
        prompt="Read a line; print how many lowercase vowels (a, e, i, o, u) it contains.",
        reference_solution='s = input()\nprint(sum(1 for c in s if c in "aeiou"))',
        tests=[("hello\n", "2\n"), ("xyz\n", "0\n")],
    ),
    Problem(
        id="fibonacci",
        prompt="Read an integer n (n >= 1); print the n-th Fibonacci number (F1 = 1, F2 = 1).",
        reference_solution=(
            "n = int(input())\n"
            "a, b = 1, 1\n"
            "for _ in range(n - 1):\n"
            "    a, b = b, a + b\n"
            "print(a)"
        ),
        tests=[("1\n", "1\n"), ("7\n", "13\n"), ("10\n", "55\n")],
    ),
]


def load_fixture_problems() -> list[Problem]:
    return list(_PROBLEMS)
