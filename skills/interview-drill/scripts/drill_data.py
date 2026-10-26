"""Shared definitions for the drill scripts: categories, outcome weights, the attempts file."""
import json, os, pathlib

DATA = pathlib.Path(os.environ.get("DRILL_DATA", "~/.claude/job-search/drill-attempts.jsonl")).expanduser()

# key -> display name. Order = curriculum order. Unknown keys are still accepted and shown last.
CATEGORIES = {
    "arrays-hashing": "Arrays & hashing",
    "two-pointers": "Two pointers",
    "sliding-window": "Sliding window",
    "stack": "Stack / monotonic stack",
    "binary-search": "Binary search",
    "linked-list": "Linked lists",
    "trees": "Trees",
    "heaps": "Heaps / priority queue",
    "intervals-greedy": "Intervals & greedy",
    "graphs": "Graphs",
    "backtracking": "Backtracking",
    "dp": "Dynamic programming",
    "design": "Design (classes)",
    "math-bits": "Math & bit manipulation",
    "strings": "String manipulation",
    "oa-format": "OA-style (primitive + twist)",
}

OUTCOMES = ["CLEAN", "H1", "H2", "H3", "SLOW", "PARTIAL", "MISS"]
# How much of the rubric percentage an outcome keeps. A clean solve keeps it all; a miss keeps little.
OUTCOME_WEIGHT = {"CLEAN": 1.0, "H1": 0.85, "H2": 0.7, "H3": 0.55, "SLOW": 0.6, "PARTIAL": 0.35, "MISS": 0.1}
MEASURED_MODES = {"mock", "oa", "review", "diagnose"}
DIFFICULTIES = ["easy", "medium", "hard"]
DIMENSIONS = ["communication", "clarifying", "approach", "complexity", "code", "verification"]
REVIEW_INTERVALS = [3, 10, 30]   # days after a non-clean attempt, then after each clean re-do


def load():
    if not DATA.exists():
        return []
    rows = []
    for n, line in enumerate(DATA.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warning: skipping malformed line {n} in {DATA}")
    rows.sort(key=lambda r: (r.get("date", ""), r.get("logged_at", "")))
    return rows
