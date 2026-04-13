import sys
from utils import detect_brackets


def parse_hub(config: list[str]) -> None:
    config[1], config[2] = int(config[1]), int(config[2])


def parse_start(config: list[str]) -> None:
    pass


def parse_end(config: list[str]) -> None:
    pass


def parse_connection(config: list[str]) -> None:
    pass


def parse_line(line: str) -> list[str, int, list] | list[str, list]:
    words = line.split()

    if words[0] == "connection:":
        return parse_connection(words[1:])

    hub_info = detect_brackets(line)
    if hub_info:
        hub_config = words[1:4]
        hub_config.append(hub_info)
        if words[0] == "hub:":
            return parse_hub(hub_config)
        elif words[0] == "start_hub:":
            return parse_start(hub_config)
        elif words[0] == "end_hub":
            return parse_end(hub_config)
    raise ValueError("Invalid Input...Usage:"
                        "        hub_style: name x y [config]")


def parse_path(filename: str) -> None:
    try:
        with open(filename, 'r') as f:
            for line in f:
                if "#" in line:
                    line = line.split("#")[0]
                if not line:
                    continue
                parse_line(line)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
