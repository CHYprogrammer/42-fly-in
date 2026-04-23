import heapq


h = []

for v in [3, 1, 2]:
    heapq.heappush(h, v)
print(h), print()

h_p = heapq.heappop(h)
print(h_p), print(h), print()


val = -heapq.heappop(h)
print(val), print(h), print()

yet_heap = [3, 1, 4, 1, 5, 9]
heapq.heapify(yet_heap)
print(yet_heap), print()


def my_heapify(arr):
    n = len(arr)
    for i in range(n // 2 -1, -1, -1):
        sift_down(arr, i, n)


def sift_down(arr, i, n):
    while True:
        smallest = i
        left = 2 * i + 1
        right = 2 * i + 2

        if left < n and arr[left] < arr[smallest]:
            smallest = right
        if right < n and arr[right] < arr[smallest]:
            smallest = right

        if smallest == i:
            break

        arr[i], arr[smallest] = arr[smallest], arr[i]
        i = smallest

arr = [3, 1, 4, 1, 5, 9]
my_heapify(arr)
print(arr)
