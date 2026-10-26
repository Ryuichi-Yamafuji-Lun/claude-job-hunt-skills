#!/usr/bin/env python3
"""List open jobs on public boards whose titles match what you're looking for.

Usage:
  list_jobs.py greenhouse:stripe ashby:notion lever:spotify
  list_jobs.py --match "new grad|early career|engineer i\\b|university" greenhouse:stripe ashby:notion
  list_jobs.py --exclude "intern|manager|senior|staff" --days 30 greenhouse:stripe

Defaults: --match picks entry-level titles, --role keeps engineering ones (pass --role "" for any role,
or e.g. --role "data|analyst" for other fields), --exclude drops internships and senior titles.
Each output line starts with a spec (greenhouse:stripe/8212508) that ats_probe.py accepts, so the
next step is verifying the interesting ones:  ats_probe.py greenhouse:stripe/8212508 ...
Newest postings print first.
"""
import argparse, datetime, os, re, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I too
from find_boards import get_json

DEFAULT_MATCH = (r"new ?grad|early.career|university|graduate|entry.level|junior|associate (software|engineer)"
                 r"|engineer i\b|engineer 1\b|developer i\b|emerging talent|20\d\d start|class of 20\d\d")
DEFAULT_ROLE = r"engineer|developer|software|\bswe\b|\bsde\b|programmer"
DEFAULT_EXCLUDE = r"\bintern(ship)?s?\b|co-?op|senior|staff|principal|manager|director|\blead\b|\bhead\b|\bsr\.?\b"


def jobs_for(spec):
    try:
        return _jobs_for(spec)
    except Exception as e:              # a malformed board must not take down the whole list
        print(f"{spec}: couldn't read this board ({type(e).__name__}); skipped", file=sys.stderr)
        return spec, []


def _jobs_for(spec):
    ats, _, org = spec.partition(":")
    out = []
    if ats == "greenhouse":
        j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs") or {}
        for x in j.get("jobs", []):
            out.append((f"greenhouse:{org}/{x['id']}", x.get("title") or "",
                        (x.get("location") or {}).get("name", ""), (x.get("first_published") or "")[:10],
                        x.get("absolute_url", "")))
    elif ats == "ashby":
        j = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}") or {}
        for x in j.get("jobs", []):
            out.append((f"ashby:{org}/{x['id']}", x.get("title") or "", x.get("location", ""),
                        (x.get("publishedAt") or "")[:10], x.get("jobUrl", "")))
    elif ats == "lever":
        j = get_json(f"https://api.lever.co/v0/postings/{org}?mode=json") or []
        for x in j if isinstance(j, list) else []:
            created = x.get("createdAt")
            day = datetime.datetime.utcfromtimestamp(created / 1000).date().isoformat() if created else ""
            out.append((f"lever:{org}/{x['id']}", x.get("text") or "",
                        (x.get("categories") or {}).get("location", ""), day, x.get("hostedUrl", "")))
    else:
        print(f"skipping {spec}: list_jobs handles greenhouse:, ashby:, lever: (use ats_probe.py for others)",
              file=sys.stderr)
    return spec, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("boards", nargs="+", help="greenhouse:<org> / ashby:<org> / lever:<org>")
    ap.add_argument("--match", default=DEFAULT_MATCH, help="level regex a title must match (case-insensitive)")
    ap.add_argument("--role", default=DEFAULT_ROLE, help="role regex a title must ALSO match; '' to allow any role")
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE, help="regex that drops a title")
    ap.add_argument("--location", help="regex the location must match, e.g. 'remote|new york|san francisco'")
    ap.add_argument("--days", type=int, help="only postings from the last N days (where the board reports a date)")
    a = ap.parse_args()

    boards = [b.strip().rstrip(",") for b in a.boards if b.strip().rstrip(",")]
    m, x = re.compile(a.match, re.I), re.compile(a.exclude, re.I) if a.exclude else None
    role = re.compile(a.role, re.I) if a.role else None
    loc = re.compile(a.location, re.I) if a.location else None
    cutoff = (datetime.date.today() - datetime.timedelta(days=a.days)).isoformat() if a.days else None

    rows, empty = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for spec, jobs in pool.map(jobs_for, boards):
            if not jobs:
                empty.append(spec)
            for r in jobs:
                _, title, where, day, _ = r
                if not m.search(title) or (x and x.search(title)) or (role and not role.search(title)):
                    continue
                if loc and not loc.search(where or ""):
                    continue
                if cutoff and day and day < cutoff:
                    continue
                rows.append(r)

    rows.sort(key=lambda r: r[3] or "", reverse=True)
    for spec, title, where, day, url in rows:
        print(f"{day or '—':<11}{spec:<52}{title[:60]:<62}{(where or '')[:40]}")
    print(f"\n{len(rows)} matching roles across {len(boards)} boards", file=sys.stderr)
    if empty:
        print("no jobs returned (wrong slug, or the company moved boards; re-run find_boards.py): "
              + ", ".join(empty), file=sys.stderr)


if __name__ == "__main__":
    main()
