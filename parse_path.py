import sys
from utils import detect_bracket
from dataclasses import dataclass


"""
    parse map file.

    Structure:
        Config
        |_ Hub
        |_ Connection

"""

# 残りのparseタスク
# parse_path, parse_lineをclass Configに入れて、OOPを徹底
# Connection内で、見覚えのないHub名が見つかった場合のエラー処理
# おそらくアルゴリズム内で行うべきことだが
# connection同士がスタートからゴールまでちゃんとくっついているかを確認
# 独立したコネクションに関しては一旦保留


@dataclass
class Hub():
    x: int
    y: int
    metadata: dict[str, str]

    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Hub":
        if not isinstance(config, list):
            raise ValueError("Invalid config type")
        x, y, *rest = config
        data = rest[0] if rest else ""
        return cls(
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
                    raise ValueError(
                        "max_drones must be a positive integer,"
                        f" - '{val}'"
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
    metadata: int = 1

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
            metadata=cls._parse_metadata(data)
        )

    @staticmethod
    def _parse_metadata(data: str) -> int:

        inner = data.strip("[]").strip()
        if not inner:
            return 1
        result: dict[str, int] = {}
        for token in inner.split():
            key, _, value = token[0].partition("=")
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


def parse_line(line: str) -> dict[str, Hub | Connection]:
    metadata = detect_bracket(line)
    line = line.split(metadata)[0] if metadata else line
    config = line.split()
    if metadata:
        config.append(metadata)
    if config[0] == "connection:":
        return {config[1]: Connection.parse_and_init(config[2:])}
    elif config[0] in ("hub:", "start_hub:", "end_hub:"):
        return {config[1]: Hub.parse_and_init(config[1:])}
    else:
        raise ValueError(
            "Invalid Input...Usage:"
            " hub_style: name x y [config]"
            )


def parse_path(filename: str) -> None:
    try:
        result = {}
        nb_drones = None
        with open(filename, 'r') as f:
            for line in f:
                line = line.split("#")[0].strip()
                if not line:
                    continue
                if nb_drones is None:
                    if not line.startwith("nb_drones"):
                        raise ValueError("first line must be 'nb_drones: <n>'")
                    value = line.split(":")[1].strip()
                    if not value.isdigit() or int(value) <= 0:
                        raise ValueError(
                            "nb_drones must be a positive integer, "
                            f"got '{value}"
                            )
                    nb_drones = int(value)
                    continue
                result.update(parse_line(line))

    except FileNotFoundError:
        print("Error: file not found", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
