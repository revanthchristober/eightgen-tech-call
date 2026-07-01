"""
Problem: Rate Limiter
Input: user_id (str), max_requests (int), window_seconds (int)
Output: allow(user_id) -> bool
Constraints: in-memory, thread-safe not required, sliding window
"""
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, deque] = defaultdict(deque)

    def allow(self, user_id: str) -> bool:
        now = time.time()
        q = self.requests[user_id]

        while q and now - q[0] > self.window:
            q.popleft()

        if len(q) < self.max_requests:
            q.append(now)
            return True
        return False


# --- tests ---
import pytest

def test_allows_within_limit():
    rl = RateLimiter(max_requests=3, window_seconds=10)
    assert rl.allow("u1") is True
    assert rl.allow("u1") is True
    assert rl.allow("u1") is True

def test_blocks_over_limit():
    rl = RateLimiter(max_requests=2, window_seconds=10)
    rl.allow("u1")
    rl.allow("u1")
    assert rl.allow("u1") is False

def test_independent_users():
    rl = RateLimiter(max_requests=1, window_seconds=10)
    assert rl.allow("u1") is True
    assert rl.allow("u2") is True
