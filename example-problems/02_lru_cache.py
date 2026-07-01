"""
Problem: LRU Cache
Input: capacity (int)
Output: get(key) -> int, put(key, val) -> None
Constraints: O(1) get and put, capacity >= 1
"""
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)


# --- tests ---
def test_basic():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)          # evicts key 2
    assert c.get(2) == -1
    assert c.get(3) == 3

def test_update_existing():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(1, 10)
    assert c.get(1) == 10
