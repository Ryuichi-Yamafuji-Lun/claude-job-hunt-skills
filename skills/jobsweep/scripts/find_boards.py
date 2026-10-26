#!/usr/bin/env python3
"""Find which public job board (Greenhouse, Ashby, Lever) each company uses.

Usage:
  find_boards.py Stripe Notion "Scale AI" Ramp
  find_boards.py -f companies.txt

Prints one line per company, e.g.
  Stripe       greenhouse:stripe   (717 open roles)
  Notion       ashby:notion        (141 open roles)
  Acme Corp    not found: check their careers page by hand (may use Workday or their own site)

The `greenhouse:stripe` style spec is what goes into the profile's "Public boards to check"
and what ats_probe.py accepts. No login, no API key: these are the boards' public JSON feeds.
"""
import argparse, json, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) job-hunt-kit/find_boards"
TIMEOUT = 15


def get_json(url, tries=2):
    """Parsed JSON, or None. Never raises: one flaky board must not end a sweep."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code < 500:            # 404 = no board here; retrying won't change that
                return None
        except Exception:               # dropped connection, partial read, TLS reset, bad JSON, ...
            pass
        if attempt + 1 < tries:
            time.sleep(1.5)
    return None


def slugs(name):
    base = name.lower().strip()
    base = re.sub(r"[&+]", " and ", base)
    base = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|technologies|technology|labs|hq)\b\.?", " ", base)
    words = re.findall(r"[a-z0-9]+", base)
    out = []
    for s in ("".join(words), "-".join(words), words[0] if words else ""):
        if s and s not in out:
            out.append(s)
    return out


def check(slug):
    """Every board that answers for this slug, as (spec, open_roles)."""
    hits = []
    gh = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    if isinstance(gh, dict) and isinstance(gh.get("jobs"), list):
        hits.append((f"greenhouse:{slug}", len(gh["jobs"])))
    ab = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if isinstance(ab, dict) and isinstance(ab.get("jobs"), list):
        hits.append((f"ashby:{slug}", len(ab["jobs"])))
    lv = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if isinstance(lv, list):
        hits.append((f"lever:{slug}", len(lv)))
    return hits


# Big companies with their own careers systems; ats_probe.py handles the first two directly.
SPECIAL = {"google": "google:<job id> (use ats_probe.py; search at google.com/about/careers)",
           "amazon": 'amazon:"<search terms>" (use ats_probe.py)',
           "aws": 'amazon:"<search terms>" (use ats_probe.py)',
           "microsoft": "careers.microsoft.com (no public API; check by hand or with a scout)",
           "meta": "metacareers.com (no public API; check by hand or with a scout)",
           "apple": "jobs.apple.com (no public API; check by hand or with a scout)"}


def find(name):
    key = slugs(name)[0] if slugs(name) else ""
    if key in SPECIAL:
        return name, ("special", SPECIAL[key])
    hits = [h for s in slugs(name) for h in check(s)]
    # Companies that moved ATS often leave an old board behind with a handful of stale posts:
    # the busiest board is the live one.
    hits = [h for h in hits if h[1] > 0]
    return name, (max(hits, key=lambda h: h[1]) if hits else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("companies", nargs="*")
    ap.add_argument("-f", "--file", help="one company per line")
    a = ap.parse_args()
    names = list(a.companies)
    if a.file:
        with open(a.file) as fh:
            names += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    if not names:
        sys.exit(__doc__)

    width = max(len(n) for n in names) + 2
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, hit in pool.map(find, names):
            if hit and hit[0] == "special":
                print(f"{name:<{width}}{hit[1]}")
            elif hit:
                spec, n = hit
                print(f"{name:<{width}}{spec:<28}({n} open roles)")
            else:
                print(f"{name:<{width}}not found: check their careers page by hand "
                      "(may use Workday or their own site)")


if __name__ == "__main__":
    main()
