from mapconfig import MapConfig, Hub, HubType

# tasks:
# MapConfigに保管されたデータをダイクストラ法で扱えるように成形
# graph = {hub: ({accessible_hub1, accessible_hub2, ...}}
# for文でdrone一つ一つの最短距離を弾き出す(metadataを書き換える)
#
# ある地点からある地点までの最短距離(最短経路)を求めたいときに必要な思考の作法 - Graph Theory：
# step1: 問題を抽象化する。
#        「何がノードで何がエッジか」を定義
#        この課題の場合、コストが道ではなくノードについている。"どこを通るか"ではなく"どこに着くか"
# step2: 探索の性質を問う。
#        コストについて、要求された最短距離の数について
# step3: Dijkstraの直観を掴む
#        「今まで確定した中で最もコストが低いノードから次を探す」という貪欲戦略
# step4: データ構造を学ぶ。
#        「今まで確定した中で最もコストが低いノードを取り出す」操作→"優先度つきキュー(mini-heap)"
# step5: "最短経路"と"最短距離"を区別する
#        距離だけでなく経路も必要な場合は、came_from辞書で追跡する。

# この課題での注意点：blockedゾーンは探索から除外、priorityゾーンはコストが同じ場合に優先して通す。
# ！！ simulate(visualize)するときのことを頭の片隅においたままコードを書く！！

"""

ゴール：視覚化時に使いやすい形のデータとして、それぞれのドローンの最短経路の塊（辞書型？）を出力
辞書：{drone_name: shortest_path}
algorithm: dijkstra

"""

import heapq


node_weights = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 1,
    "E": 3,
    "F": 1
}

graph = {
    "A": ["B", "C"],
    "B": ["A", "D", "E"],
    "C": ["A", "F"],
    "D": ["B", "F"],
    "E": ["B", "F"],
    "F": ["C", "D", "E"]
}


def dijkstra(graph, weights, start, goal) -> tuple | None:
    heap = [(0, start)]
    best = {start, 0}
    came_from = {}

    while heap:
        cost, current = heapq.heappop(heap)
        if current == goal:
            path = []
            node = goal
            while node != start:
                path.append(node)
                node = came_from[node]
            path.append(start)
            path.reverse()
            return cost, path

        if cost > best.get(current, float("inf")):
            continue

        for neighbor in graph[current]:
            new_cost = cost + weights[neighbor]

            if new_cost < best.get(neighbor, float("inf")):
                best[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(heap, (new_cost, neighbor))

    return None


if __name__ == "__main__":
    result = dijkstra(graph, node_weights, start="A", goal="F")
    if result:
        cost, path = result
        print(f"cost: {cost}")
        print(f"path: {' -> '.join(path)}")
    else:
        print("unreachable")
