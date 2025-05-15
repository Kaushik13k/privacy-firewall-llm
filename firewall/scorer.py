from typing import List


SUSPICIOUS_KEYWORDS = {"bypass", "jailbreak",
                       "ignore previous", "simulate", "exploit", "hack", "hacker", "attack",
                       "malicious", "unauthorized", "intrusion", "breach",
                       "malware", "spyware", "phishing", "ransomware", "trojan",
                       "virus", "worm", "rootkit", "keylogger", "backdoor",}


def compute_risk_score(prompt: str, pii_entities: List[str]) -> int:
    score = 0
    if pii_entities:
        score += 20

    if any(keyword in prompt.lower() for keyword in SUSPICIOUS_KEYWORDS):
        score += 10

    if len(prompt) > 300:
        score += 5

    return score
