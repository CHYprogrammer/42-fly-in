"""utility functions for fly_in"""


def detect_brackets(string: str) -> str:
    for c in string:
        if c in "[":
            start = string.index(c)
        if c in "]":
            end = string.index(c)
    return string[start: end+1]
