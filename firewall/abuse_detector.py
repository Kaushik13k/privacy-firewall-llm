import time
from collections import defaultdict, deque


class AbuseDetector:
    def __init__(self, window_seconds=300, max_failures=5):
        self.failed_attempts = defaultdict(lambda: deque())
        self.window_seconds = window_seconds
        self.max_failures = max_failures

    def record_failure(self, session_id: str):
        now = time.time()
        attempts = self.failed_attempts[session_id]
        attempts.append(now)
        self._prune_old_attempts(attempts, now)

    def is_abusive(self, session_id: str) -> bool:
        now = time.time()
        attempts = self.failed_attempts[session_id]
        self._prune_old_attempts(attempts, now)
        return len(attempts) >= self.max_failures

    def _prune_old_attempts(self, attempts: deque, current_time: float):
        while attempts and (current_time - attempts[0]) > self.window_seconds:
            attempts.popleft()
