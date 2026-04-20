"""utility functions for fly_in"""
from typing import Optional


def detect_bracket(string: str) -> Optional[str]:
    start = string.find("[")
    end = string.find("]")

    if start == -1 or end == -1:
        return None
    if end < start:
        raise ValueError(f"Malformed brackets in: '{string}'")
    if string.count("[") > 1 or string.count("]") > 1:
        raise ValueError(f"Multiple brackets in: '{string}")

    return string[start: end + 1]
