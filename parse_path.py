import sys
from utils import detect_bracket
from dataclasses import dataclass


# !!claude メッセージ保留中！！


@dataclass
class Hub():
    name: str
    x: int
    y: int
    metadata: dict[str, str]

    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Hub":
        if not isinstance(config, list):
            raise ValueError("Invalid config type")
        name, x, y, *rest = config
        data = rest[0] if rest else ""
        return cls(
            name=name,
            x=int(x),
            y=int(y),
            metadata=cls._parse_metadata(data)
        )

    @staticmethod
    def _parse_metadata(data: str) -> dict[str, str]:

        inner = data.strip("[]").strip()
        if not inner:
            return {}
        result: dict[str, str] = {}
        for token in inner.split():
            key, _, value = token.partition("=")
            if not key or not value:
                raise ValueError(f"empty key or value in '{token}'")
            if key in result:
                raise ValueError(f"duplicate metadata key '{key}'")
            result[key] = value

        valid_zone_types = ["normal", "blocked", "restricted", "priority"]
        for key, val in result.items():
            if key == "max_drones":
                if not val.isdigit() or int(val) <= 0:
                    raise ValueError("max_drones must be a positive integer, "
                                     f"- '{val}'")
            elif key == "zone":
                if val not in valid_zone_types:
                    raise ValueError(f"invalid zone type - '{val}'")
            elif key == "color":
                if not val or " " in val:
                    raise ValueError(f"color must be a single word - '{val}'")
            else:
                raise ValueError(f"unknown metadata key '{key}'")

        return result


class Connection:
    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Connection":
        return cls()


def parse_line(line: str) -> Hub | Connection:
    metadata = detect_bracket(line)
    line = line.split(metadata)[0] if metadata else line
    config = line.split()
    if metadata:
        config.append(metadata)
    if config[0] == "connection:":
        return Connection.parse_and_init(config[1:])
    elif config[0] in ("hub:", "start_hub", "end_hub"):
        return Hub.parse_and_init(config[1:])
    else:
        raise ValueError("Invalid Input...Usage:"
                         " hub_style: name x y [config]")


def parse_path(filename: str) -> None:
    try:
        with open(filename, 'r') as f:
            for line in f:
                if "#" in line:
                    line = line.split("#")[0]
                if not line:
                    continue
                parse_line(line)

    except FileNotFoundError:
        print("Error: file not found", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
