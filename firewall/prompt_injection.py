from typing import List

ATTACK_PATTERNS = [
    "ignore previous instructions",
    "forget all previous",
    "disregard prior rules",
    "simulate a harmful",
    "you are now",
    "repeat this exactly",
    "bypass restrictions",
    "jailbreak",
    "override the system",
    "act as"
]


def detect_prompt_injection(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(pattern in lowered for pattern in ATTACK_PATTERNS)


def get_triggered_phrases(prompt: str) -> List[str]:
    lowered = prompt.lower()
    return [pattern for pattern in ATTACK_PATTERNS if pattern in lowered]
