import os
import tiktoken


def num_tokens_from_string(text: str) -> int:
    encoding = tiktoken.get_encoding(os.getenv("LLM_ENCODING", "cl100k_base"))
    return len(encoding.encode(text))
