#!/usr/bin/env python3
"""Practice stats: what you've done per category, how strong you are at each, and what's due.

Usage:
  stats.py              full report
  stats.py --due        just the review queue (problems due for a re-do today or earlier)
  stats.py --focus      just the recommended focus categories (the skill uses this to pick problems)
  stats.py --json       machine-readable

How mastery is computed (0-100 per category, from scored attempts only):
  attempt value = average of (a) rubric % (scored dimensions only) and
                  (b) outcome weight (CLEAN 1.0, H1 .85, H2 .70, SLOW .60, H3 .55, PARTIAL .35, MISS .10),
                  x difficulty factor (easy .85, medium 1.0, hard 1.1), capped at 100.
                  Half how you interviewed, half whether you got there: a near-miss with a strong
                  approach lands in Developing, not Weak.
  mastery       = recency-weighted average of the last 5 attempts (newest counts most)

Levels:
  Not started  nothing logged
  Studied      study sessions only (guided/learn), not yet tested cold
  Weak         < 40
  Developing   40-64
  Proficient   65-84
  Mastered     >= 85, with at least 3 scored attempts and at least one clean medium/hard solve
"""
import argparse, collections, datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I too
from drill_data import (load, CATEGORIES, OUTCOME_WEIGHT, DIMENSIONS, REVIEW_INTERVALS)

DIFF_FACTOR = {"easy": 0.85, "medium": 1.0, "hard": 1.1}


def attempt_value(r):
    scored = [v for v in r.get("dims", {}).values() if v != "void"]
    if not scored:
        return None
    pct = sum(scored) / (4 * len(scored))
    blend = (pct + OUTCOME_WEIGHT.get(r["outcome"], 0)) / 2
    return min(100.0, 100 * blend * DIFF_FACTOR.get(r["difficulty"], 1))


def mastery(rows):
    vals = [v for v in (attempt_value(r) for r in rows) if v is not None][-5:]
    if not vals:
        return None
    w = range(1, len(vals) + 1)
    return sum(v * k for v, k in zip(vals, w)) / sum(w)


def level(m, rows):
    if m is None:
        return "Not started"
    clean_hard = any(r["outcome"] == "CLEAN" and r["difficulty"] in ("medium", "hard") for r in rows)
    if m >= 85 and len(rows) >= 3 and clean_hard:
        return "Mastered"
    if m >= 65:
        return "Proficient"
    if m >= 40:
        return "Developing"
    return "Weak"


def bar(m, width=10):
    if m is None:
        return "·" * width
    n = round(m / 100 * width)
    return "█" * n + "░" * (width - n)


def review_queue(rows, today):
    """Anything not CLEAN is re-done at +3, then +10, then +30 days; a non-clean re-do restarts at +3."""
    by_id = collections.defaultdict(list)
    for r in rows:
        if r.get("measured"):
            by_id[r["id"]].append(r)
    due = []
    for pid, att in by_id.items():
        last_bad = max((i for i, r in enumerate(att) if r["outcome"] != "CLEAN"), default=None)
        if last_bad is None:
            continue
        clean_after = len(att) - 1 - last_bad
        if clean_after >= len(REVIEW_INTERVALS):
            continue                                    # graduated
        anchor = datetime.date.fromisoformat(att[-1]["date"])
        due_on = anchor + datetime.timedelta(days=REVIEW_INTERVALS[clean_after])
        due.append({"id": pid, "problem": att[-1]["problem"], "category": att[-1]["category"],
                    "due": due_on.isoformat(), "overdue": due_on <= today,
                    "last_outcome": att[-1]["outcome"]})
    return sorted(due, key=lambda d: d["due"])


def build(rows, today):
    cats = collections.OrderedDict((k, []) for k in CATEGORIES)
    for r in rows:
        cats.setdefault(r["category"], [])
    report = {"categories": [], "dimensions": {}, "habits": [], "due": review_queue(rows, today)}
    for key, _ in cats.items():
        cat_rows = [r for r in rows if r["category"] == key]
        scored = [r for r in cat_rows if r.get("measured")]
        m = mastery(scored)
        report["categories"].append({
            "key": key, "name": CATEGORIES.get(key, key),
            "problems_completed": len({r["id"] for r in cat_rows if r["outcome"] != "MISS"}),
            "attempts": len(cat_rows), "scored_attempts": len(scored),
            "clean": sum(r["outcome"] == "CLEAN" for r in scored),
            "study": sum(not r.get("measured") for r in cat_rows),
            "mastery": None if m is None else round(m),
            "level": level(m, scored) if scored or not cat_rows else "Studied",
            "last": cat_rows[-1]["date"] if cat_rows else None,
        })
    scored_rows = [r for r in rows if r.get("measured")]
    for d in DIMENSIONS:
        vals = [r["dims"][d] for r in scored_rows if isinstance(r.get("dims", {}).get(d), int)]
        recent = vals[-8:]
        report["dimensions"][d] = round(sum(recent) / len(recent), 2) if recent else None
    habit_counts = collections.Counter(h for r in rows for h in r.get("habits", []))
    report["habits"] = habit_counts.most_common(8)

    started = [c for c in report["categories"] if c["mastery"] is not None]
    untested = [c for c in report["categories"] if c["mastery"] is None and c["key"] in CATEGORIES]
    # Weak/Developing first (that's where practice pays most), then untested, then Proficient.
    def entry(c, why):
        return {"key": c["key"], "name": c["name"], "why": why}
    lagging = sorted((c for c in started if c["level"] in ("Weak", "Developing")), key=lambda c: c["mastery"])
    proficient = sorted((c for c in started if c["level"] == "Proficient"), key=lambda c: c["mastery"])
    report["focus"] = ([entry(c, f"{c['level'].lower()}, {c['mastery']}/100") for c in lagging]
                       + [entry(c, "not tested yet") for c in untested]
                       + [entry(c, f"proficient, {c['mastery']}/100") for c in proficient])[:3]
    report["totals"] = {"attempts": len(rows), "scored": len(scored_rows),
                        "problems": len({r["id"] for r in rows}),
                        "clean": sum(r["outcome"] == "CLEAN" for r in scored_rows)}
    return report


def print_report(rep):
    t = rep["totals"]
    if not t["attempts"]:
        print("No practice logged yet. Run /interview-drill to start; it asks a few setup questions first.")
        return
    print(f"\nPractice so far: {t['problems']} problems, {t['attempts']} attempts "
          f"({t['scored']} scored, {t['clean']} clean)\n")
    print(f"{'Category':<30}{'Done':>5}{'Scored':>8}{'Clean':>7}  {'Mastery':<16}{'Level':<12}Last")
    print("-" * 90)
    for c in rep["categories"]:
        m = "  –" if c["mastery"] is None else f"{c['mastery']:>3}"
        print(f"{c['name']:<30}{c['problems_completed']:>5}{c['scored_attempts']:>8}{c['clean']:>7}  "
              f"{bar(c['mastery'])} {m}  {c['level']:<12}{c['last'] or ''}")
    dims = {k: v for k, v in rep["dimensions"].items() if v is not None}
    if dims:
        print("\nInterview skills (average of last 8 scored attempts, out of 4; 3 = hire bar)")
        for k, v in dims.items():
            flag = "  ← below hire bar" if v < 3 else ""
            print(f"  {k:<15}{v:>5}{flag}")
    if rep["habits"]:
        print("\nRecurring habits to fix")
        for h, n in rep["habits"]:
            print(f"  {h} ×{n}")
    if rep["focus"]:
        print("\nFocus next: " + ", ".join(f"{f['name']} ({f['why']})" for f in rep["focus"]))
    due = [d for d in rep["due"] if d["overdue"]]
    upcoming = [d for d in rep["due"] if not d["overdue"]]
    if due:
        print("\nDue for review now: " + ", ".join(f"{d['id']} {d['problem']}" for d in due))
    if upcoming:
        print("Coming up: " + ", ".join(f"{d['id']} on {d['due']}" for d in upcoming[:5]))
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--focus", action="store_true")
    ap.add_argument("--today", default=datetime.date.today().isoformat(), help=argparse.SUPPRESS)
    a = ap.parse_args()
    rep = build(load(), datetime.date.fromisoformat(a.today))
    if a.json:
        json.dump(rep, sys.stdout, indent=2)
        print()
    elif a.due:
        due = [d for d in rep["due"] if d["overdue"]]
        print("\n".join(f"{d['id']}  {d['problem']}  ({d['category']}, due {d['due']})" for d in due) or "nothing due")
    elif a.focus:
        print("\n".join(f"{f['key']}  {f['name']}: {f['why']}" for f in rep["focus"]))
    else:
        print_report(rep)


if __name__ == "__main__":
    main()
