import sys
from utils import detect_brackets
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any


class Hub(BaseModel):
    name: str
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    metadata: Optional[dict[str, str]] = {}

    @model_validator(mode="before")
    @classmethod
    def parse_hub(cls, config: list[str]) -> dict[str, Any]:
        if not isinstance(config, list):
            raise ValueError("Invalid config type")
        name, x, y, *rest = config
        meta = rest[0] if rest else ""
        return {
            "name": name,
            "x": int(x),
            "y": int(y),
            "metadata": cls._parse_metadata(meta)
            }

    @staticmethod
    def _parse_metadata(meta: str) -> dict[str, str]:
        inner = meta.strip("[]").strip()
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
        return result


def parse_line(line: str) -> None:
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
        elif words[0] == "end_hub:":
            return parse_end(hub_config)
    raise ParseError("Invalid Input...Usage:"
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
    except ParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
