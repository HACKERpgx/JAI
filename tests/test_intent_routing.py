"""Offline checks for JAI intent classification and math detection.

Extracts the pure-logic classifiers from jai_assistant.py so they can be
exercised without the assistant's runtime dependencies.
"""
import ast
import difflib
import re
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "jai_assistant.py"
WANTED = {"classify_intent", "is_mathematical_query", "is_likely_math"}


class _Fuzz:
    @staticmethod
    def partial_ratio(a, b):
        return int(difflib.SequenceMatcher(None, a, b).ratio() * 100)


def load_functions():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
    module = ast.Module(
        body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in WANTED],
        type_ignores=[],
    )
    namespace = {"re": re, "fuzz": _Fuzz, "Tuple": tuple, "Dict": dict, "Any": object, "Optional": object}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace


INTENT_CASES = [
    ("hello there", "greeting"),
    ("what time is it", "current_time"),
    ("weather in Lahore", "weather"),
    ("my name is Abdul", "set name"),
    ("remind me to call mom at 5pm", "remind_me"),
    ("news", "news"),
    ("Lorem ipsum dolor sit amet, consectetur adipiscing elit", "query"),
    ("can you explain how photosynthesis works", "query"),
    ("I could not sleep last night, any tips", "query"),
    ("what is this thing called", "query"),
    ("tell me about the history of restaurants", "query"),
]

MATH_CASES = [
    ("solve 2x + 3 = 11", True),
    ("what is 15% of 200", True),
    ("integrate x^2 dx", True),
    ("Lorem ipsum dolor sit amet, consectetur adipiscing elit", False),
    ("can you help me plan my week", False),
    ("i.e. the report is due tomorrow", False),
]


def test_classify_intent():
    classify_intent = load_functions()["classify_intent"]
    for text, expected in INTENT_CASES:
        intent, _args = classify_intent(text)
        assert intent == expected, f"{text!r} -> {intent!r}, expected {expected!r}"


def test_is_mathematical_query():
    is_mathematical_query = load_functions()["is_mathematical_query"]
    for text, expected in MATH_CASES:
        assert is_mathematical_query(text) is expected, f"{text!r} -> {not expected}"


def main():
    failures = []
    for check in (test_classify_intent, test_is_mathematical_query):
        try:
            check()
        except AssertionError as exc:
            failures.append(f"{check.__name__}: {exc}")
    for line in failures:
        print("FAIL:", line)
    print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
