import sys
from utils import detect_bracket
from dataclasses import dataclass, field
from enum import Enum


"""
    parse map file.

    Structure:
        Config
        |_ Hub
        |_ Connection

"""

# remained tasks:
# おそらくアルゴリズム内で行うべきことだが
# connection同士がスタートからゴールまでちゃんとくっついているかを確認
# 独立したコネクションに関しては一旦保留


class HubType(Enum):
    HUB = "hub"
    START = "start_hub"
    END = "end_hub"


@dataclass
class Hub():
    x: int
    y: int
    hub_type: HubType = HubType.HUB
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse_and_init(cls, config: list[str], hub_type: str = "hub") -> "Hub":
        if not isinstance(config, list):
            raise ValueError("Invalid config type")
        x, y, *rest = config
        try:
            x, y = int(x), int(y)
        except ValueError:
            raise ValueError(f"coordinates must be integers, got '{x}' '{y}'")
        data = rest[0] if rest else ""
        return cls(
            x=x,
            y=y,
            hub_type=HubType(hub_type),
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
                    raise ValueError(
                        "max_drones must be a positive integer, "
                        f"got '{val}'"
                        )
            elif key == "zone":
                if val not in valid_zone_types:
                    raise ValueError(f"invalid zone type - '{val}'")
            elif key == "color":
                if not val or " " in val:
                    raise ValueError(f"color must be a single word - '{val}'")
            else:
                raise ValueError(f"unknown metadata key '{key}'")

        return result


@dataclass
class Connection:
    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Connection":
        if not isinstance(config, list) or not config:
            raise ValueError("Invalid config type")
        conn_token, *rest = config
        data = rest[0] if rest else ""

        if conn_token.count("-") != 1:
            raise ValueError(
                f"connection must be <zone1>-<zone2>, got '{conn_token}'"
                )
        zone_a, zone_b = conn_token.split("-")
        if not zone_a or not zone_b:
            raise ValueError(
                f"empry zone name in connection '{conn_token}'"
                )

        return cls(
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=cls._parse_metadata(data)
        )

    @staticmethod
    def _parse_metadata(data: str) -> int:

        inner = data.strip("[]").strip()
        if not inner:
            return 1
        result: dict[str, int] = {}
        for token in inner.split():
            key, _, value = token.partition("=")
            if not key or not value:
                raise ValueError(f"empty key or value in '{token}'")
            if key in result:
                raise ValueError(f"duplicate metadata key '{key}'")
            if key != "max_link_capacity":
                raise ValueError(f"unknown connection metadata key '{key}'")
            if not value.isdigit() or int(value) <= 0:
                raise ValueError(
                    "max_link_capacity must be a positive integer, "
                    f"got '{value}'"
                    )
            result[key] = int(value)
        return int(result[key])


@dataclass
class MapConfig:
    nb_drones: int
    hubs: dict[str, Hub] = field(default_factory=dict)
    connections: dict[str, Connection] = field(default_factory=dict)

    @classmethod
    def parse_map(cls, filename: str) -> "MapConfig":
        try:
            nb_drones = None
            hubs: dict[str, Hub] = {}
            connections: dict[str, Connection] = {}
            seen_connections: set[frozenset[str]] = set()

            with open(filename, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.split("#")[0].strip()
                    if not line:
                        continue

                    if nb_drones is None:
                        if not line.startswith("nb_drones"):
                            raise ValueError(
                                f"line {line_num}: "
                                + "first line must be 'nb_drones: <n>'"
                                )
                        _, _, value = line.partition(":")
                        if not value.strip().isdigit() or int(value) <= 0:
                            raise ValueError(
                                f"line {line_num}: "
                                + "nb_drones must be a positive integer, "
                                + f"got '{value}'"
                                )
                        nb_drones = int(value)
                        continue

                    # parse a line practically
                    try:
                        parsed = cls.parse_line(line)
                    except ValueError as e:
                        raise ValueError(
                            f"line {line_num}: {e}"
                        )

                    for key, obj in parsed.items():
                        if isinstance(obj, Connection):
                            if (obj.zone_a not in hubs
                               or obj.zone_b not in hubs):
                                raise ValueError(
                                    f"line {line_num}: "
                                    + "connection references unknown hub "
                                    + f"'{obj.zone_a}-{obj.zone_b}'"
                                )
                            conn_key = frozenset((obj.zone_a, obj.zone_b))
                            if conn_key in seen_connections:
                                raise ValueError(
                                    f"line {line_num}: "
                                    + "duplicate connection "
                                    + f"'{obj.zone_a}-{obj.zone_b}'"
                                )
                            seen_connections.add(conn_key)
                            connections[key] = obj
                        else:  # isinstance(obj, Hub)
                            if key in hubs:
                                raise ValueError(
                                    f"line {line_num}: "
                                    + f"duplicate zone name '{key}'"
                                )
                            hubs[key] = obj

            if nb_drones is None:
                raise ValueError(
                    "file is empty or missing 'nb_drones'"
                    )

            # check number of start_hub and end_hub
            starts, ends = 0, 0
            for h in hubs.values():
                if h.hub_type == HubType.START:
                    starts += 1
                elif h.hub_type == HubType.END:
                    ends += 1
            if starts != 1:
                raise ValueError(
                    f"exactly one start_hub required, got {starts}"
                    )
            if ends != 1:
                raise ValueError(
                    f"exactly one end_hub required, got {ends}"
                    )

            return cls(nb_drones=nb_drones, hubs=hubs, connections=connections)

        except FileNotFoundError:
            print("Error: file not found", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def parse_line(cls, line: str) -> dict[str, Hub | Connection]:
        metadata = detect_bracket(line)
        base = line.split(metadata)[0] if metadata else line
        config = base.split()
        if metadata:
            config.append(metadata)

        if config[0] in ("hub:", "start_hub:", "end_hub:"):
            name = config[1]
            if "-" in name or " " in name:
                raise ValueError(
                    f"zone name '{name}' must not contain dashes or spaces"
                    )
            hub_type = config[0].strip(":")
            return {name: Hub.parse_and_init(config[2:], hub_type)}
        elif config[0] == "connection:":
            conn_token = config[1]
            return {conn_token: Connection.parse_and_init(config[1:])}
        else:
            raise ValueError(f"unrecognised line prefix '{config[0]}'")
