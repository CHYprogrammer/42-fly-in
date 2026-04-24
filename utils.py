"""utility functions for fly_in"""
from typing import Optional


def detect_bracket(string: str) -> Optional[str]:
    start = string.find("[")
    end = string.find("]")

    if start == -1 and end == -1:
        return None
    if end < start:
        raise ValueError(f"malformed brackets in: '{string}'")
    if string.count("[") > 1 or string.count("]") > 1:
        raise ValueError(f"multiple brackets in: '{string}")
    if string[end] != string[-1]:
        raise ValueError("extra string detected after brackets"
                         + f" - '... {string[end:]}'")

    return string[start: end + 1]
