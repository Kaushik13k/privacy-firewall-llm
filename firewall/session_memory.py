from collections import defaultdict, deque
from firewall.token_utils import num_tokens_from_string


class MemoryStore:
    def __init__(self, max_tokens_per_session=1000):
        self.history = defaultdict(lambda: deque())
        self.max_tokens = max_tokens_per_session

    def add_message(self, session_id: str, role: str, content: str):
        if not session_id:
            return

        message = {"role": role, "content": content}
        self.history[session_id].append(message)

        while self._token_count(session_id) > self.max_tokens:
            self.history[session_id].popleft()

    def get_context(self, session_id: str):
        return list(self.history[session_id]) if session_id else []

    def clear(self, session_id: str):
        if session_id in self.history:
            del self.history[session_id]

    def _token_count(self, session_id: str):
        return sum(num_tokens_from_string(msg["content"]) for msg in self.history[session_id])
