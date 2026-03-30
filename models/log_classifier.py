"""Deterministic log classifier for the simulator's incident labels."""

from __future__ import annotations

from typing import Iterable

LABEL_KEYWORDS = {
    "disk_full": (
        "no space left on device",
        "disk full",
        "filesystem full",
        "storage full",
        "write failed",
        "i/o error writing",
    ),
    "memory_leak": (
        "out of memory",
        "oom",
        "oom-killer",
        "memory leak",
        "killed process",
        "anon-rss",
    ),
    "crash": (
        "segmentation fault",
        "core dumped",
        "dumped core",
        "stack trace",
        "fatal error",
        "main process exited",
    ),
    "network_issue": (
        "connection timeout",
        "connection timed out",
        "temporary failure in name resolution",
        "tls handshake",
        "link is down",
        "network is unreachable",
        "name resolution",
    ),
}

LABEL_PRIORITY = ("disk_full", "memory_leak", "crash", "network_issue")
DEFAULT_LABEL = "memory_leak"


def _count_matches(text: str, patterns: Iterable[str]) -> int:
    return sum(text.count(pattern) for pattern in patterns)


def classify_log(text: str) -> str:
    normalized = (text or "").lower()
    if not normalized.strip():
        return DEFAULT_LABEL

    scores = {
        label: _count_matches(normalized, patterns)
        for label, patterns in LABEL_KEYWORDS.items()
    }

    best_label = max(
        LABEL_PRIORITY,
        key=lambda label: (scores[label], -LABEL_PRIORITY.index(label)),
    )
    if scores[best_label] == 0:
        return DEFAULT_LABEL
    return best_label
