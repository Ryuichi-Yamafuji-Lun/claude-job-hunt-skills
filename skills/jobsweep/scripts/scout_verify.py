#!/usr/bin/env python3
"""
Mechanically verify a jd-scout report against tier-0 ground truth.

Why this exists: /jobsweep's safety property is "the scout quotes the qualification block
verbatim, Opus scores from the quote." But Opus never sees the source page, so it cannot catch a
scout that silently paraphrased or truncated. A self-consistent wrong quote gets scored with
confidence. This script is the missing check, and it is mechanical — no model, no judgment.

Usage:
  scout_verify.py --report scout_haiku.md   --truth jd/Some_Title.truth.json
  scout_verify.py --report-dir reports/     --truth-dir jd/          # batch
  scout_verify.py --ab reports_sonnet/ reports_haiku/ --truth-dir jd/   # A/B two scout tiers

Exit code 0 = every check passed. 1 = at least one FAIL. Use it to gate a model swap.
"""
import argparse, json, os, re, sys, unicodedata

REQUIRED_FIELDS = ["STATUS", "URL", "TYPE", "LOCATION", "START / GRADUATION WINDOW",
                   "POSTED / UPDATED", "SPONSORSHIP LINE", "CAPS / LIMITS",
                   "LANGUAGES / STACK NAMED", "QUALIFICATIONS", "RED FLAGS"]
TRANS = {0x2018: "'", 0x2019: "'", 0x201c: '"', 0x201d: '"', 0x2013: "-", 0x2014: "-",
         0x00a0: " ", 0x2022: "-", 0x2026: "...", 0x00ad: ""}


def norm(s):
    """Whitespace/punctuation-insensitive form for substring comparison."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).translate(TRANS)
    s = re.sub(r"(?m)^\s*>\s?", "", s)          # markdown quote markers
    s = re.sub(r"(?m)^\s*[-*•]\s*", " ", s)  # bullet markers
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def parse_report(text):
    """Pull the scout's fields out of its fixed template."""
    out, cur, buf = {}, None, []
    for raw in text.splitlines():
        ln = raw.rstrip()
        m = re.match(r"^\s*(QUALIFICATIONS|PREFERRED)\s*\([^)]*\)\s*:\s*$", ln, re.I)
        if m:
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1).upper(), []
            continue
        m = re.match(r"^\s*([A-Z][A-Z /]{2,40}?)\s*:\s*(.*)$", ln)
        if m and m.group(1).strip().upper() in [f.upper() for f in REQUIRED_FIELDS] + ["COMP"]:
            if cur:
                out[cur] = "\n".join(buf).strip()
                cur, buf = None, []
            key, val = m.group(1).strip().upper(), m.group(2).strip()
            out[key] = val
            # TYPE / LOCATION / COMP share one line
            for k2 in ("LOCATION", "COMP"):
                mm = re.search(k2 + r"\s*:\s*([^\n]*?)(?=\s{2,}[A-Z/ ]{3,}:|$)", ln)
                if mm and k2 not in out:
                    out[k2] = mm.group(1).strip()
            continue
        if cur:
            buf.append(ln)
    if cur:
        out[cur] = "\n".join(buf).strip()
    m = re.search(r"^###\s*(.+)$", text, re.M)
    if m:
        out["_HEADER"] = m.group(1).strip()
    return out


def bullets(block):
    """Comparable units from a quoted block: bullets, else sentences."""
    lines = [l for l in re.split(r"\n+", block or "") if l.strip()]
    items = [re.sub(r"(?m)^\s*>\s?", "", l).strip() for l in lines]
    items = [i for i in items if len(norm(i)) >= 25 and not i.rstrip().endswith(":")]
    if not items:
        t = norm(block)
        items = [s for s in re.split(r"(?<=\.)\s+", t) if len(s) >= 25]
    return items


def check(report_text, truth):
    rep = parse_report(report_text)
    jd = norm(truth.get("_jd_text", ""))
    res = []

    def add(name, ok, detail, critical=False):
        res.append({"check": name, "ok": bool(ok), "detail": detail, "critical": critical})

    # 1. template completeness
    missing = [f for f in REQUIRED_FIELDS if f.upper() not in rep]
    add("TEMPLATE", not missing, "all fields present" if not missing else f"missing: {', '.join(missing)}")

    # 2. status — catches UNVERIFIABLE-when-actually-LIVE
    t_status = (truth.get("status") or "").upper()
    s_status = (rep.get("STATUS") or "").upper()
    s_kind = next((k for k in ("LIVE", "CLOSED", "UNVERIFIABLE", "NEEDS-UI") if k in s_status), "?")
    if t_status in ("LIVE", "CLOSED"):
        ok = (s_kind == t_status)
        why = f"scout={s_kind} truth={t_status}"
        if s_kind == "UNVERIFIABLE" and t_status == "LIVE":
            why += "  <-- scout gave up on a req tier 0 fetched fine (lost coverage)"
        add("STATUS", ok, why, critical=True)
    else:
        add("STATUS", True, f"truth={t_status or 'n/a'}, not asserted")

    # 3. QUOTE FIDELITY — the invariant the cascade rests on
    q = rep.get("QUALIFICATIONS", "")
    if not truth.get("qual_found"):
        add("QUOTE_FIDELITY", True, "tier 0 found no qualifications block; cannot assert")
    elif not q.strip():
        add("QUOTE_FIDELITY", False, "scout returned no qualifications quote", critical=True)
    else:
        whole = norm(q) in jd
        items = bullets(q)
        hits = [b for b in items if norm(b) in jd]
        miss = [b for b in items if norm(b) not in jd]
        cov = (len(hits) / len(items)) if items else 0.0
        if whole:
            add("QUOTE_FIDELITY", True, f"exact substring of source ({len(items)} bullets)", critical=True)
        elif cov == 1.0:
            add("QUOTE_FIDELITY", True,
                f"all {len(items)} bullets verbatim, block not contiguous (benign reflow)", critical=True)
        else:
            kind = "PARAPHRASE/TRUNCATION"
            add("QUOTE_FIDELITY", False,
                f"{kind}: only {len(hits)}/{len(items)} bullets ({cov:.0%}) appear verbatim in source. "
                f"first miss: {(miss[0][:110] + '...') if miss else '-'}", critical=True)

    # 4. location
    t_loc, s_loc = truth.get("location"), rep.get("LOCATION")
    if not t_loc:
        add("LOCATION", True, "truth has no extractable location (expected on Google)")
    elif not s_loc:
        add("LOCATION", False, f"scout blank, truth={t_loc!r}")
    else:
        tt = set(re.findall(r"[a-z]{4,}", t_loc.lower()))
        ss = set(re.findall(r"[a-z]{4,}", s_loc.lower()))
        ok = bool(tt & ss) or "remote" in ss
        add("LOCATION", ok, f"scout={s_loc!r} truth={t_loc!r}" + ("" if ok else "  <-- no token overlap"))

    # 5. C/C++ placement — no-cpp-roles-rule tests the block, not the title
    t_cpp = (truth.get("cpp_gate") or "none").upper()
    s_line = (rep.get("LANGUAGES / STACK NAMED") or "").upper()
    s_cpp = next((k for k in ("HARD-GATE", "OR-LIST", "PREFERRED") if k in s_line), "NONE")
    if t_cpp == "NONE" and s_cpp == "NONE":
        add("CPP_CLASS", True, "no C/C++ in either")
    else:
        ok = (t_cpp == s_cpp)
        add("CPP_CLASS", ok, f"scout={s_cpp} truth={t_cpp}" +
            ("" if ok else "  <-- misclassifying this mis-scores the no-C/C++ rule"), critical=True)

    # 6. caps
    t_caps = truth.get("caps_quote") or []
    s_caps = (rep.get("CAPS / LIMITS") or "").strip().lower()
    said_none = (not s_caps) or s_caps.startswith("none")
    add("CAPS", not (t_caps and said_none),
        "agree" if not (t_caps and said_none)
        else f"scout said none, tier 0 saw: {t_caps[0][:100]}")
    return rep, res


def load_truth(path):
    t = json.load(open(path))
    jd = path.replace(".truth.json", ".jd.txt")
    t["_jd_text"] = open(jd).read() if os.path.exists(jd) else ""
    return t


def pair_by_index(report_dir, jsonl_path, truth_dir):
    """Deterministic pairing: report NN.md <-> the Nth record in ats_probe's JSONL.

    Preferred over name matching. Report files are named by their position in the req list, which
    is the same order ats_probe emitted, so nothing depends on title spelling. Records with no
    ground-truth file (e.g. Microsoft NEEDS-UI) are reported as ungradeable rather than skipped
    silently.
    """
    recs = [json.loads(l) for l in open(jsonl_path) if l.strip()]
    pairs, ungradeable = [], []
    for i, rec in enumerate(recs, 1):
        rpath = os.path.join(report_dir, f"{i:02d}.md")
        pre = rec.get("out_prefix")
        tpath = (pre + ".truth.json") if pre else None
        if not os.path.exists(rpath):
            ungradeable.append((f"{i:02d}", "no scout report written"))
            continue
        if not tpath or not os.path.exists(tpath):
            ungradeable.append((f"{i:02d}", f"no tier-0 ground truth ({rec.get('status')})"))
            continue
        pairs.append((rpath, tpath))
    for idx, why in ungradeable:
        print(f"  -  {idx}: ungradeable — {why}", file=sys.stderr)
    return pairs


def pair_up(report_dir, truth_dir):
    truths = {f[:-len(".truth.json")]: os.path.join(truth_dir, f)
              for f in os.listdir(truth_dir) if f.endswith(".truth.json")}
    pairs = []
    for f in sorted(os.listdir(report_dir)):
        if not f.endswith((".md", ".txt")):
            continue
        stem = os.path.splitext(f)[0]
        key = next((k for k in truths if k == stem or k in stem or stem in k), None)
        if key:
            pairs.append((os.path.join(report_dir, f), truths[key]))
        else:
            print(f"  ! no truth file matched report {f}", file=sys.stderr)
    return pairs


def run(pairs, label=""):
    tot = fails = crit = 0
    per_check = {}
    for rpath, tpath in pairs:
        truth = load_truth(tpath)
        _, res = check(open(rpath).read(), truth)
        name = (truth.get("title") or os.path.basename(rpath))[:52]
        bad = [r for r in res if not r["ok"]]
        print(f"\n  {'FAIL' if bad else 'PASS'}  {name}")
        for r in res:
            mark = "ok  " if r["ok"] else ("FAIL" if not r["critical"] else "FAIL*")
            print(f"        [{mark}] {r['check']:<16} {r['detail']}")
            d = per_check.setdefault(r["check"], [0, 0])
            d[1] += 1
            d[0] += 1 if r["ok"] else 0
        tot += 1
        fails += 1 if bad else 0
        crit += sum(1 for r in bad if r["critical"])
    print(f"\n  {label}summary: {tot - fails}/{tot} reqs clean, "
          f"{fails} with findings, {crit} critical")
    for k, (o, n) in per_check.items():
        print(f"      {k:<16} {o}/{n} passed")
    return fails, crit, per_check


def main():
    ap = argparse.ArgumentParser(description="Verify jd-scout reports against tier-0 ground truth")
    ap.add_argument("--report"); ap.add_argument("--truth")
    ap.add_argument("--report-dir"); ap.add_argument("--truth-dir")
    ap.add_argument("--ab", nargs=2, metavar=("DIR_A", "DIR_B"))
    ap.add_argument("--index-from", metavar="JSONL",
                    help="ats_probe JSONL; pairs report NN.md to the Nth record (deterministic)")
    a = ap.parse_args()

    def pairs_for(d):
        if a.index_from:
            return pair_by_index(d, a.index_from, a.truth_dir)
        return pair_up(d, a.truth_dir)

    if a.ab:
        if not a.truth_dir:
            ap.error("--ab requires --truth-dir")
        out = {}
        for d in a.ab:
            print(f"\n=== {os.path.basename(d.rstrip('/'))} ===")
            out[d] = run(pairs_for(d), label=f"{os.path.basename(d.rstrip('/'))} ")
        print("\n=== A/B verdict ===")
        (fa, ca, pa), (fb, cb, pb) = out[a.ab[0]], out[a.ab[1]]
        for k in sorted(set(pa) | set(pb)):
            x, y = pa.get(k, (0, 0)), pb.get(k, (0, 0))
            flag = ""
            if k in ("QUOTE_FIDELITY", "CPP_CLASS", "STATUS") and y[0] < x[0]:
                flag = "   <-- cheaper tier is worse on a load-bearing check"
            print(f"  {k:<16} A {x[0]}/{x[1]}   B {y[0]}/{y[1]}{flag}")
        print(f"\n  critical failures: A={ca}  B={cb}")
        print("  " + ("B is safe to adopt." if cb <= ca else
                      "Do NOT adopt B: it loses on a check the commander cannot catch."))
        sys.exit(1 if cb > ca else 0)

    if a.report_dir and a.truth_dir:
        f, c, _ = run(pairs_for(a.report_dir))
        sys.exit(1 if f else 0)
    if a.report and a.truth:
        f, c, _ = run([(a.report, a.truth)])
        sys.exit(1 if f else 0)
    ap.error("give --report/--truth, --report-dir/--truth-dir, or --ab with --truth-dir")


if __name__ == "__main__":
    main()
