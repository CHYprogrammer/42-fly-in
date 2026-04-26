from __future__ import annotations

import heapq
from dataclasses import dataclass
from parse_config import MapConfig, Hub


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _zone_type(hub: Hub) -> str:
    return hub.metadata.get("zone", "normal")


def _cost(hub: Hub) -> int:
    """Turn cost to enter this hub."""
    return 2 if _zone_type(hub) == "restricted" else 1


def _priority(hub: Hub) -> int:
    """Tie-breaking score (lower = preferred)."""
    return 0 if _zone_type(hub) == "priority" else 1


def _blocked(hub: Hub) -> bool:
    return _zone_type(hub) == "blocked"


def _build_graph(map_config: MapConfig) -> dict[str, list[str]]:
    """Build adjacency list from connections list (one-time cost)."""
    graph: dict[str, list[str]] = {name: [] for name in map_config.hubs}
    for conn in map_config.connections:
        graph[conn.zone_a].append(conn.zone_b)
        graph[conn.zone_b].append(conn.zone_a)
    return graph


# -----------------------------------------------------------------------------
# Result type
# -----------------------------------------------------------------------------


@dataclass
class Path:
    """A single route from start to goal."""

    zones: list[str]
    total_cost: int

    def __repr__(self) -> str:
        return f"Path(cost={self.total_cost}, zones={' -> '.join(self.zones)})"


# -----------------------------------------------------------------------------
# Result type
# -----------------------------------------------------------------------------


def _dijkstra(
        map_config: MapConfig,
        graph: dict[str, list[str]],
        start: str,
        goal: str,
        excluded: set[str]
) -> Path | None:
    """
        Dijkstra with node-based costs and optional excluded nodes.

        Args:
            map_config: Parsed map.
            graph: Adjacency list (pre-built).
            start: Start zone name.
            goal: Goal zone name.
            excluded: Zone name to skip (for alternative path discovery).

        Returns:
            Shortest Path or None if unreachable.
    """

    # heap entry: (culmulative cost, tie-break priority, zone name)
    heap: list[tuple[int, int, str]] = [(0, 0, start)]
    best: dict[str, int] = {start: 0}
    came_from: dict[str, str] = {}

    while heap:
        cost, _, current = heapq.heappop(heap)
        print(f"pop: cost={cost} current={current}")
        print(f"came_from: {came_from}")
        print(f"best: {best}")

        if current == goal:
            print(" -> reached goal")
            return _reconstruct(came_from, start, goal, cost)

        # skip old entry
        if cost > best.get(current, float("inf")):
            continue

        for neighbor_name in graph[current]:
            if neighbor_name in excluded:
                continue
            neighbor = map_config.hubs[neighbor_name]
            if _blocked(neighbor) and neighbor_name != goal:
                continue

            new_cost = cost + _cost(neighbor)
            if new_cost < best.get(neighbor_name, float("inf")):
                best[neighbor_name] = new_cost
                came_from[neighbor_name] = current
                heapq.heappush(
                    heap,
                    (new_cost, _priority(neighbor), neighbor_name))

        return None


def _reconstruct(
        came_from: dict[str, str],
        start: str,
        goal: str,
        total_cost: int
) -> Path:
    """Trace came_from back to start and return a Path."""
    zones: list[str] = {}
    node = goal

    while node != start:
        zones.append(node)
        node = came_from[node]
    zones.append(start)
    zones.reverse()
    return Path(zones=zones, total_cost=total_cost)


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def find_shortest_path(map_config: MapConfig) -> Path | None:
    """
        Find the minimum-cost path from start_hub to end_hub.

        Args:
            map_config: parse map.

        Returns:
            Shortest Path or None if unreachable
    """

    start = next(iter(map_config.start))
    goal = next(iter(map_config.end))
    graph = _build_graph(map_config)

    return _dijkstra(map_config, graph, start, goal, excluded=set())


def find_all_paths(
        map_config: MapConfig,
        max_paths: int = 10
) -> list[Path]:
    """
        Find multiple distinct paths from start to goal.

        Repeatedly excluded one intermediate node from the previous path
        to discover alternative routes.

        Args:
            map_config: Parsed map.
            max_paths: Maximum number of paths to return.

        Returns:
            List or Paths sorted by total_cost ascending.
    """
    start = next(iter(map_config.start()))
    goal = next(iter(map_config.end))
    graph = _build_graph(map_config)
    results: list[Path] = []
    excluded: set[str] = set()

    for _ in range(max_paths):
        path = _dijkstra(map_config, graph, start, goal, excluded)
        if path is None:
            break
        results.append(path)

        intermediates = path.zones[1:-1]
        new_excl = next(
            (z for z in intermediates if z not in excluded), None
        )
        if new_excl is None:
            break
        excluded.add(new_excl)

    return sorted(results, key=lambda p: p.total_cost)
