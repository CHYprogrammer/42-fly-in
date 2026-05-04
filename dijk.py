import heapq
from parse_config import MapConfig


def _build_graph(map: MapConfig) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {name: [] for name in map.hubs}
    for c in map.connections:
        graph[c.zone_a].append(c.zone_b)
        graph[c.zone_b].append(c.zone_a)
    return graph


def dijkstra(graph, start):
    distances = {node: float("inf") for node in graph}
    distances[start] = 0
    queue = [(0, start)]

    while queue:
        cur_dist, cur_node = heapq.heappop(queue)
        if cur_dist > distances[cur_node]:
            continue
        for neighbor, weight in graph[cur_node].items():
            distance = cur_dist + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(queue, (distance, neighbor))

    return distances


if __name__ == "__main__":
    map = MapConfig.parse_map("maps/easy/01_linear_path.txt")
    graph = _build_graph(map)
    print("=== graph ===")
    for node in graph:
        print(f"{node}: {graph[node]}")
    dijkstra(graph, map.start)
