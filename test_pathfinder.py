import tempfile
import os
from parse_config import MapConfig
from pathfinder import find_shortest_path, find_all_paths, Path


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{tag}] {name}{suffix}")
    _results.append((name, ok))


def load(content: str) -> MapConfig:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        f.write(content)
        path = f.name
    m = MapConfig.parse_map(path)
    os.unlink(path)
    return m


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------

# 直線: start -> A -> goal  cost=2
LINEAR = """
nb_drones: 2
start_hub: start 0 0
hub: A 1 0
end_hub: goal 2 0
connection: start-A
connection: A-goal
"""

# フォーク: 2経路
# start -> A -> goal  cost=2
# start -> B -> goal  cost=2
FORK = """
nb_drones: 3
start_hub: start 0 0
hub: A 1 1
hub: B 1 -1
end_hub: goal 2 0
connection: start-A
connection: start-B
connection: A-goal
connection: B-goal
"""

# restricted ゾーン
# start -> R -> goal  cost=3 (R=restricted=2, goal=1)
# start -> N -> goal  cost=2 (N=normal=1, goal=1)
RESTRICTED = """
nb_drones: 2
start_hub: start 0 0
hub: R 1 1 [zone=restricted]
hub: N 1 -1 [zone=normal]
end_hub: goal 2 0
connection: start-R
connection: start-N
connection: R-goal
connection: N-goal
"""

# priority ゾーン: 同コストでも priority が優先される
# start -> P -> goal  cost=2 (P=priority=1)
# start -> N -> goal  cost=2 (N=normal=1)
PRIORITY = """
nb_drones: 1
start_hub: start 0 0
hub: P 1 1 [zone=priority]
hub: N 1 -1 [zone=normal]
end_hub: goal 2 0
connection: start-P
connection: start-N
connection: P-goal
connection: N-goal
"""

# blocked ゾーンは通行不可
# start -> B -> goal  B=blocked → 通れない
# start -> N -> goal  cost=2
BLOCKED = """
nb_drones: 1
start_hub: start 0 0
hub: B 1 1 [zone=blocked]
hub: N 1 -1
end_hub: goal 2 0
connection: start-B
connection: start-N
connection: B-goal
connection: N-goal
"""

# 到達不可: goal へのパスが存在しない
UNREACHABLE = """
nb_drones: 1
start_hub: start 0 0
hub: island 5 5
end_hub: goal 2 0
connection: start-goal
"""

# サンプルマップ（課題の例）
SAMPLE = """
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
"""


# ---------------------------------------------------------------------------
# Tests: find_shortest_path
# ---------------------------------------------------------------------------

def test_linear() -> None:
    print("\n--- linear ---")
    m = load(LINEAR)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    check("cost == 2", p.total_cost == 2, str(p.total_cost))
    check("zones == [start, A, goal]", p.zones == ["start", "A", "goal"], str(p.zones))


def test_fork_picks_either() -> None:
    print("\n--- fork (equal cost) ---")
    m = load(FORK)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    check("cost == 2", p.total_cost == 2, str(p.total_cost))
    check("starts at start", p.zones[0] == "start")
    check("ends at goal", p.zones[-1] == "goal")


def test_restricted_costs_2() -> None:
    print("\n--- restricted zone ---")
    m = load(RESTRICTED)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    # N 経由が最短 (cost=2) のはず
    check("avoids restricted", "R" not in p.zones, str(p.zones))
    check("cost == 2", p.total_cost == 2, str(p.total_cost))


def test_priority_preferred() -> None:
    print("\n--- priority tie-break ---")
    m = load(PRIORITY)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    check("cost == 2", p.total_cost == 2, str(p.total_cost))
    # 同コストなら priority ゾーンが選ばれる
    check("uses priority zone", "P" in p.zones, str(p.zones))


def test_blocked_avoided() -> None:
    print("\n--- blocked zone ---")
    m = load(BLOCKED)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    check("blocked not in path", "B" not in p.zones, str(p.zones))
    check("uses N instead", "N" in p.zones, str(p.zones))


def test_unreachable() -> None:
    print("\n--- unreachable ---")
    m = load(UNREACHABLE)
    # island は goal に繋がっていないが start-goal の直接パスがある
    p = find_shortest_path(m)
    check("returns Path (direct start-goal)", p is not None)


def test_sample_map() -> None:
    print("\n--- sample map ---")
    m = load(SAMPLE)
    p = find_shortest_path(m)
    check("returns Path", p is not None)
    assert p is not None
    check("cost == 3", p.total_cost == 3, str(p.total_cost))
    check("uses corridorA (priority)", "corridorA" in p.zones, str(p.zones))
    check("blocked obstacleX not in path", "obstacleX" not in p.zones)


# ---------------------------------------------------------------------------
# Tests: find_all_paths
# ---------------------------------------------------------------------------

def test_all_paths_fork() -> None:
    print("\n--- find_all_paths: fork ---")
    m = load(FORK)
    paths = find_all_paths(m, max_paths=5)
    check("2 paths found", len(paths) == 2, str(len(paths)))
    check("sorted by cost", paths[0].total_cost <= paths[-1].total_cost)
    zone_sets = [set(p.zones) for p in paths]
    check("A path exists", any("A" in z for z in zone_sets))
    check("B path exists", any("B" in z for z in zone_sets))


def test_all_paths_sample() -> None:
    print("\n--- find_all_paths: sample ---")
    m = load(SAMPLE)
    paths = find_all_paths(m, max_paths=5)
    check("at least 2 paths", len(paths) >= 2, str(len(paths)))
    check("first path cost <= last", paths[0].total_cost <= paths[-1].total_cost)
    check("shortest cost == 3", paths[0].total_cost == 3)


def test_all_paths_no_duplicate() -> None:
    print("\n--- find_all_paths: no duplicate zones sequences ---")
    m = load(SAMPLE)
    paths = find_all_paths(m, max_paths=10)
    zone_lists = [tuple(p.zones) for p in paths]
    check("no duplicate paths", len(zone_lists) == len(set(zone_lists)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    tests = [
        test_linear,
        test_fork_picks_either,
        test_restricted_costs_2,
        test_priority_preferred,
        test_blocked_avoided,
        test_unreachable,
        test_sample_map,
        test_all_paths_fork,
        test_all_paths_sample,
        test_all_paths_no_duplicate,
    ]
    for t in tests:
        t()

    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    color = "\033[32m" if passed == total else "\033[31m"
    print(f"\n{color}{passed}/{total} tests passed\033[0m")


if __name__ == "__main__":
    main()
