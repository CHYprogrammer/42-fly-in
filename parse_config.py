"""
Drone Map Configuration Parser Module.

This module provides a robust framework for parsing and validating drone
navigation maps from plain text files. It handles the extraction of drone
counts, hub coordinates, metadata-rich zones, and network connections.

The module ensures data integrity through strict validation of:
    - Unique hub naming and non-duplicate connections.
    - Coordinate integer conversion and positive drone counts.
    - Specific metadata constraints (zone types, capacities, colors).
    - Mandatory presence of exactly one start and one end hub.

Example file format:
    nb_drones: 10
    start_hub: Alpha 10 20 [color=blue]
    hub: Beta 30 40 [max_drones=5 zone=restricted]
    end_hub: Gamma 50 60
    connection: Alpha-Beta [max_link_capacity=2]
    connection: Beta-Gamma
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Hub():
    """
    Represents a physical hub on the map with coordinates and properties.

    Attributes:
        x (int): The X-coordinate of the hub.
        y (int): The Y-coordinate of the hub.
        metadata (dict[str, str]): A dictionary of additional attributes
            (e.g., 'zone', 'max_drones', 'color').
    """

    x: int
    y: int
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Hub":
        """
        Parses raw configuration tokens to initialize a Hub instance.

        Args:
            config (list[str]): A list of tokens containing [x, y, metadata].

        Returns:
            Hub: A new instance of Hub with validated coordinates and metadata.

        Raises:
            ValueError: If the config type is invalid, coordinates are not
                integers, or metadata parsing fails.
        """

        if not isinstance(config, list):
            raise ValueError("Invalid config type")

        x_str, y_str, *rest = config
        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise ValueError(
                f"coordinates must be integers, got '{x_str}' '{y_str}'")
        data = rest[0] if rest else ""

        return cls(
            x=x,
            y=y,
            metadata=cls._parse_metadata(data)
        )

    @staticmethod
    def _parse_metadata(data: str) -> dict[str, str]:
        """
        Parses and validates metadata strings formatted as
        [key=value key=value].

        Supported keys:
            - zone: Must be 'normal', 'blocked', 'restricted', or 'priority'.
            - max_drones: Must be a positive integer.
            - color: Must be a single word.

        Args:
            data (str): The raw metadata string wrapped in brackets.

        Returns:
            dict[str, str]: A dictionary of validated metadata.

        Raises:
            ValueError: If formatting is incorrect, keys are unknown,
                values are invalid, or duplicate keys are found.
        """

        result: dict[str, str] = {}
        inner = data.strip("[]").strip()
        if not inner:
            return result

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
                        f"got '{val}'")
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
    """
    Represents a link between two hubs with a specific throughput capacity.

    Attributes:
        zone_a (str): The name of the first hub in the connection.
        zone_b (str): The name of the second hub in the connection.
        max_link_capacity (int): The maximum number of drones allowed
            simultaneously on this link. Defaults to 1.
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @classmethod
    def parse_and_init(cls, config: list[str]) -> "Connection":
        """
        Parses raw configuration tokens to initialize a Connection instance.

        Expects a token in the format 'zoneA-zoneB' followed by optional
        metadata.

        Args:
            config (list[str]): A list of tokens containing [connection_string,
                metadata].

        Returns:
            Connection: A new instance of Connection.

        Raises:
            ValueError: If the config is empty, the connection string format
                is invalid, or zone names are empty.
        """

        if not isinstance(config, list) or not config:
            raise ValueError("connection is empty or invalid config type")

        conn_token, *rest = config
        data = rest[0] if rest else ""
        if conn_token.count("-") != 1:
            raise ValueError(
                f"connection must be <zone1>-<zone2>, got '{conn_token}'")
        zone_a, zone_b = conn_token.split("-")
        if not zone_a or not zone_b:
            raise ValueError(
                f"empty zone name in connection '{conn_token}'")

        return cls(
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=cls._parse_metadata(data)
        )

    @staticmethod
    def _parse_metadata(data: str) -> int:
        """
        Parses connection-specific metadata to extract the link capacity.

        Supported keys:
            - max_link_capacity: Must be a positive integer.

        Args:
            data (str): The raw metadata string wrapped in brackets.

        Returns:
            int: The value of max_link_capacity, or 1 if no metadata is
                provided.

        Raises:
            ValueError: If formatting is incorrect, keys are unknown,
                the value is not a positive integer, or duplicate keys are
                found.
        """

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
                    f"got '{value}'")
            result[key] = int(value)

        return int(result[key])


@dataclass
class MapConfig:
    """
    Data class to store the configuration of the drone flight map.

        This class aggregates drone counts, hub locations, connections,
        and identified start/end points parsed from a configuration file.

        Attributes:
            nb_drones (int): The total number of drones available for
                operation.
            hubs (dict[str, Hub]): Dictionary mapping hub names to Hub objects.
            start (dict[str, Hub]): Dictionary containing the designated
                starting hub.
            end (dict[str, Hub]): Dictionary containing the designated ending
                hub.
            connections (list[Connection]): List of established paths between
                hubs.
    """

    nb_drones: int
    hubs: dict[str, Hub] = field(default_factory=dict)
    start: dict[str, Hub] = field(default_factory=dict)
    end: dict[str, Hub] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)

    @classmethod
    def parse_map(cls, filename: str) -> "MapConfig":
        """
        Parses a map configuration file and initializes a MapConfig instance.

        This method reads the file line-by-line, validates the syntax, and
        builds the internal hub and connection structures.

        Args:
            filename (str): Path to the map configuration file.

        Returns:
            MapConfig: A fully initialized configuration object.

        Raises:
            ValueError
            FileNotFoundError
        """

        nb_drones = None
        hubs: dict[str, Hub] = {}
        start: dict[str, Hub] = {}
        end: dict[str, Hub] = {}
        connections: list[Connection] = []
        seen_connections: set[frozenset[str]] = set()

        # parse the file
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # ignore the comments
                line = line.split("#")[0].strip()
                if not line:
                    continue

                # parse the first line for init nb_drones
                if nb_drones is None:
                    nb_drones = cls._parse_nb_drones(line, line_num)
                    continue

                # parse and handle metadata in the line
                metadata = cls._detect_bracket(line, line_num)
                base = line.split(metadata)[0] if metadata else line
                config = base.split()
                if metadata:
                    config.append(metadata)

                # parse and init hub depends on hub type
                if config[0] in ("hub:", "start_hub:", "end_hub:"):
                    cls._parse_hub(
                        line=line,
                        config=config,
                        line_num=line_num,
                        hubs=hubs,
                        start=start,
                        end=end)
                # parse and init connection
                elif config[0] == "connection:":
                    cls._parse_connections(
                        config=config,
                        line_num=line_num,
                        hubs=hubs,
                        connections=connections,
                        seen_connections=seen_connections)
                # handle error while parse_and_init
                else:
                    raise ValueError(
                        f"unrecognised line prefix '{config[0]}'")

        # check for other errors in the file (e.g., incorrect formatting)
        if nb_drones is None:
            raise ValueError(
                "file is empty or missing 'nb_drones'")
        cls._check_start_end_nbr(start, end)

        return cls(
            nb_drones=nb_drones,
            hubs=hubs,
            connections=connections,
            start=start,
            end=end
            )

    # === helper methods ===

    @staticmethod
    def _detect_bracket(string: str, line_num: int) -> Optional[str]:
        """
        Extracts metadata enclosed in brackets [...] from a string.

        Args:
            string (str): The line content to analyze.
            line_num (int): The current line number for error reporting.

        Returns:
            Optional[str]: The substring containing the brackets, or None if
                not found.

        Raises:
            ValueError: If brackets are malformed, nested, or followed by
                extra characters.
        """

        start = string.find("[")
        end = string.find("]")

        if start == -1 and end == -1:
            return None
        if end < start:
            raise ValueError(
                f"line {line_num}: malformed brackets in: '{string}'")
        if string.count("[") > 1 or string.count("]") > 1:
            raise ValueError(
                f"line {line_num}: multiple brackets in: '{string}'")
        if string[end] != string[-1]:
            raise ValueError(
                f"line {line_num}: "
                f"extra string appears after the brackets"
                f" - '... {string[end:]}'")

        return string[start: end + 1]

    @staticmethod
    def _parse_hub(
        line: str,
        config: list[str],
        line_num: int,
        hubs: dict[str, Hub],
        start: dict[str, Hub],
        end: dict[str, Hub]
    ) -> None:
        """
        Parses a hub definition and updates the corresponding hub dictionaries.

        Validates the hub name, coordinates, and type (normal, start, or end).

        Args:
            line (str): The raw line string for error messaging.
            config (list[str]): List of space-separated configuration tokens.
            line_num (int): The current line number.
            hubs (dict[str, Hub]): Reference to the master hub dictionary.
            start (dict[str, Hub]): Reference to the start hub dictionary.
            end (dict[str, Hub]): Reference to the end hub dictionary.

        Raises:
            ValueError: If the name is duplicated, contains invalid characters,
                or if Hub initialization fails.
        """

        if len(config) < 4:
            raise ValueError(
                f"line {line_num}: "
                f"hub must have at least 4 arguments, "
                f"got {len(config)} in '{line}'")
        name = config[1]
        if "-" in name or " " in name:
            raise ValueError(
                f"line {line_num}: "
                f"zone name '{name}' must not contain dashes or spaces")
        if name in hubs:
            raise ValueError(
                f"line {line_num}: "
                f"duplicate zone name '{name}'")
        hub_type = config[0].strip(":")
        try:
            hub_obj = Hub.parse_and_init(config[2:])
            hubs[name] = hub_obj
            if hub_type == "start_hub":
                start[name] = hub_obj
            elif hub_type == "end_hub":
                end[name] = hub_obj

        except ValueError as e:
            raise ValueError(f"line {line_num}: {e}")

    @staticmethod
    def _parse_connections(
        config: list[str],
        line_num: int,
        hubs: dict[str, Hub],
        connections: list[Connection],
        seen_connections: set[frozenset[str]]
    ) -> None:
        """
        Parses a connection definition and updates the connection list.

        Verifies that referenced hubs exist and that the connection is not a
        duplicate.

        Args:
            config (list[str]): List of space-separated configuration tokens.
            line_num (int): The current line number.
            hubs (dict[str, Hub]): Dictionary of existing hubs for reference.
            connections (list[Connection]): The list of connections to append
                to.
            seen_connections (set[frozenset[str]]): Set used for duplicate
                detection.

        Raises:
            ValueError: If a connection refers to an unknown hub or is already
                defined.
        """

        try:
            path = Connection.parse_and_init(config[1:])
        except ValueError as e:
            raise ValueError(f"line {line_num}: {e}")
        if (path.zone_a not in hubs
                or path.zone_b not in hubs):
            raise ValueError(
                f"line {line_num}: "
                f"connection references unknown hub "
                f"'{path.zone_a}-{path.zone_b}'")
        conn_key = frozenset((path.zone_a, path.zone_b))
        if conn_key in seen_connections:
            raise ValueError(
                f"line {line_num}: "
                f"duplicate connection "
                f"'{path.zone_a}-{path.zone_b}'")
        seen_connections.add(conn_key)
        connections.append(path)

    @staticmethod
    def _parse_nb_drones(line: str, line_num: int) -> int:
        """
        Parses the first line of the file to determine the number of drones.

        Args:
            line (str): The first non-empty line of the file.
            line_num (int): The current line number.

        Returns:
            int: The validated number of drones.

        Raises:
            ValueError: If the line does not start with 'nb_drones' or
                the value is not a positive integer.
        """

        if not line.startswith("nb_drones"):
            raise ValueError(
                f"line {line_num}: "
                f"first line must be 'nb_drones: <n>'")
        _, _, value = line.partition(":")
        if not value.strip().isdigit() or int(value) <= 0:
            raise ValueError(
                f"line {line_num}: "
                f"nb_drones must be a positive integer, "
                f"got '{value}'")
        return int(value)

    @staticmethod
    def _check_start_end_nbr(
        start: dict[str, Hub],
        end: dict[str, Hub]
    ) -> None:
        """
        Validates the final count of start and end hubs.

        Args:
            start (dict[str, Hub]): Dictionary of identified start hubs.
            end (dict[str, Hub]): Dictionary of identified end hubs.

        Raises:
            ValueError: If there is not exactly one start hub and one end hub.
        """

        if len(start) != 1:
            raise ValueError(
                f"exactly one start_hub required, got {start}")
        if len(end) != 1:
            raise ValueError(
                f"exactly one end_hub required, got {end}")
