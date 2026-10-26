#!/usr/bin/env python3
"""Record one practice attempt. The skill calls this after every problem; stats.py reads the result.

Usage (measured problem):
  log_attempt.py --id p7 --problem "Merge Intervals" --category intervals-greedy --difficulty medium \\
      --mode mock --outcome H1 --dims communication=3 clarifying=2 approach=3 complexity=4 code=3 verification=2 \\
      --tests 6/6 --habits skips-trace off-by-one --note "sorted by end instead of start at first"

Usage (study problem, not scored):
  log_attempt.py --id s3 --problem "House Robber" --category dp --difficulty medium --mode guided \\
      --outcome CLEAN --support L2

A dimension the interviewer contaminated is logged as `approach=void` and left out of the score.
"""
import argparse, datetime, difflib, json, os, pathlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I too
from drill_data import (DATA, CATEGORIES, OUTCOMES, MEASURED_MODES, DIFFICULTIES, DIMENSIONS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True, help="problem id, e.g. p7 or s3")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--category", required=True, help="one of: " + ", ".join(CATEGORIES))
    ap.add_argument("--difficulty", required=True, choices=DIFFICULTIES)
    ap.add_argument("--mode", required=True, choices=sorted(MEASURED_MODES | {"guided", "learn", "grind"}))
    ap.add_argument("--outcome", required=True, choices=OUTCOMES)
    ap.add_argument("--dims", nargs="*", default=[], help="name=1..4 or name=void, space- or comma-separated")
    ap.add_argument("--tests", help="passed/total; omit to read the last run.py result for this id")
    ap.add_argument("--workspace", default="~/interview-practice", help="where run.py saved its result")
    ap.add_argument("--support", help="guided support level reached, L0-L3")
    ap.add_argument("--habits", nargs="*", default=[], help="short kebab-case habit tags observed")
    ap.add_argument("--note", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="YYYY-MM-DD")
    ap.add_argument("--new-category", action="store_true", help="allow a category outside the standard list")
    a = ap.parse_args()

    try:
        datetime.date.fromisoformat(a.date)
    except ValueError:
        sys.exit(f"--date must be YYYY-MM-DD, got '{a.date}'")
    if a.category not in CATEGORIES and not a.new_category:
        close = difflib.get_close_matches(a.category.lower(), CATEGORIES, n=1, cutoff=0.5)
        hint = f" Did you mean '{close[0]}'?" if close else ""
        sys.exit(f"'{a.category}' is not a standard category.{hint} "
                 "Pass --new-category to track a custom one on purpose.")

    dims = {}
    for d in (x for chunk in a.dims for x in chunk.replace(",", " ").split()):
        k, _, v = d.partition("=")
        if k not in DIMENSIONS:
            sys.exit(f"unknown dimension '{k}'. Use: {', '.join(DIMENSIONS)}")
        if v == "void":
            dims[k] = "void"
        elif v in {"1", "2", "3", "4"}:
            dims[k] = int(v)
        else:
            sys.exit(f"dimension {k} must be 1-4 or void, got '{v}'")

    if not a.tests:
        ws = pathlib.Path(a.workspace).expanduser()
        last = ws / ".tests" / "last_result.json"
        try:
            r = json.loads(last.read_text())
        except (OSError, ValueError):
            r = {}
        if r.get("id") == a.id.lower():
            files = sorted(ws.glob(f"{a.id.lower()}_*.py"))
            if files and files[0].stat().st_mtime > r.get("file_mtime", 0) + 1:
                sys.exit(f"{files[0].name} changed after the last test run. "
                         f"Run `python3 {ws}/.tests/run.py {a.id}` again, then log.")
            a.tests = f"{r['passed']}/{r['total']}"
            print(f"tests: {a.tests} (from the last run.py result at {r['at']})")
        elif a.mode not in ("guided", "learn"):
            print("note: no test result found for this problem; logging without one")

    if a.tests and a.outcome == "CLEAN":
        passed, _, total = a.tests.partition("/")
        if passed != total:
            sys.exit(f"outcome CLEAN but tests are {a.tests}. A clean solve passes the whole suite; "
                     "re-run run.py on the saved file, or log the real outcome (PARTIAL, H1, ...).")

    measured = a.mode in MEASURED_MODES or a.mode == "grind"
    if measured and len(dims) != len(DIMENSIONS):
        missing = [d for d in DIMENSIONS if d not in dims]
        sys.exit(f"a scored attempt needs all six dimensions; missing: {', '.join(missing)}")

    rec = {
        "date": a.date, "logged_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "id": a.id, "problem": a.problem, "category": a.category, "difficulty": a.difficulty,
        "mode": a.mode, "measured": measured, "outcome": a.outcome, "dims": dims,
        "tests": a.tests, "support": a.support, "habits": a.habits, "note": a.note,
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    scored = [v for v in dims.values() if v != "void"]
    total = f"{sum(scored)}/{4 * len(scored)}" if scored else "unscored"
    print(f"logged {a.id} {a.problem} [{a.category}, {a.difficulty}, {a.mode}] {a.outcome} {total}")


if __name__ == "__main__":
    main()
