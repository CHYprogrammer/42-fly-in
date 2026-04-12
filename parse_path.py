import sys
from pydantic import BaseModel, model_validator, ValidationError


def parse_hub(words: list[str]) -> None:
    pass


def parse_connection(words: list[str]) -> None:
    pass


def parse_line(words: list[str]) -> list[str, int, list] | list[str, list]:
    if words[0] == "hub:":
        return parse_hub(words[1:])
    elif words[0] == "connection:":
        return parse_connection(words[1:])
    else:
        raise ValueError("Invalid Input...Usage:"
                         "        hub_style: name x y [config]")


def parse_path(filename: str) -> None:
    try:
        with open(filename, 'r') as f:
            for line in f:
                if "#" in line:
                    line = line.split("#")[0]
                words = line.split()
                if not words:
                    continue
                parse_line(words)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
