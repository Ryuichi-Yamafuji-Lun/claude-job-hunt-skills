#!/usr/bin/env python3
"""
Tier 0 for /jobsweep: deterministic req probing. No model, no cost, cannot hallucinate.

Pulls liveness, title, location, posting date, full-slug URL and the qualifications block
straight from public ATS APIs, so the scout model never sees a raw page dump and Opus gets
ground truth it can verify a scout against.

Usage:
  ats_probe.py greenhouse:imc/4979079101
  ats_probe.py google:118616007559258822
  ats_probe.py -f reqs.txt                 # one spec or URL per line, '#' comments ok
  ats_probe.py --out-dir ./jd https://boards-api.greenhouse.io/v1/boards/imc/jobs/4979079101

Spec forms (or paste any career URL and it is auto-detected):
  greenhouse:<org>/<id>    ashby:<org>[/<title substr>]    lever:<org>[/<id>]
  google:<id>              amazon:<search terms>

Emits one JSON object per req to stdout (JSONL). With --out-dir, the extracted plain-text JD
and qualifications block are written there for scout-verify.py to diff against.
"""
import argparse, html, json, os, re, sys, urllib.error, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
TIMEOUT = 25

# Specific heads are trusted; generic ones ("requirements", "qualifications") are only used as a
# fallback, because they also occur in prose and EEO boilerplate. Both are matched HEADING-LIKE only.
MIN_HEADS_SPECIFIC = ["minimum qualifications", "basic qualifications", "required qualifications",
                      "what we need to see", "minimum requirements", "your skills and experience",
                      "skills and experience", "what you'll need", "what you will need",
                      "who you are", "what we're looking for", "what we are looking for",
                      "we're excited if you have", "we are excited if you have",
                      "education & experience", "education and experience",
                      "what you bring", "what you'll bring", "what you will bring",
                      "basic requirements", "required skills", "desired skills",
                      "you should have", "your background", "about you",
                      "qualifications & skills", "qualifications and skills",
                      "experience & qualifications", "requirements & qualifications"]
MIN_HEADS_SPECIFIC += ["skills you'll need to bring", "skills you will need to bring",
                       "your background looks something like"]
SOFT_HEADS = {"who you are", "about you", "your background", "you should have", "what you bring",
              "what you'll bring", "what you will bring", "your background looks something like"}
MIN_HEADS_GENERIC = ["requirements", "qualifications"]
PREF_HEADS = ["preferred qualifications", "nice to have", "nice-to-have", "bonus points",
              "desired qualifications", "what would be nice", "preferred"]
STOP_HEADS = PREF_HEADS + ["about the", "about us", "benefits", "compensation", "salary",
                           "equal opportunity", "eeo", "how to apply", "our team", "perks",
                           "the base salary", "base salary range", "what we offer"]

CAP_PAT = re.compile(
    r"[^.\n]*\b(?:"
    r"(?:only\s+)?(?:one|two|three|\d+)\s+applications?\b"          # "only one application"
    r"|appl\w+[^.\n]{0,45}\bper\s+(?:season|year|cycle|rolling|\d+\s*(?:days|months))"
    r"|re-?appl\w+"                                                    # "may re-apply after..."
    r"|no more than \d+\s*months?"                                    # experience-ceiling cap
    r"|limit(?:ed)?\s+to\s+\d+\s+(?:applications?|roles?|reqs?)"
    r")[^.\n]*[.\n]", re.I)
SPON_PAT = re.compile(r"[^.\n]*\b(sponsor|sponsorship|work authorization|visa|H-?1B|"
                      r"require.{0,20}authoriz)\b[^.\n]*[.\n]", re.I)
GRAD_PAT = re.compile(r"[^.\n]*\b(graduat\w*|start date|starting in|class of|"
                      r"expected to (?:graduate|complete)|degree (?:by|between))\b[^.\n]*[.\n]", re.I)
YOE_PAT = re.compile(r"[^.\n]*\b(\d+)\+?\s*(?:\(\d+\))?\s*years?\b[^.\n]{0,60}?"
                     r"(?:experience|industry)[^.\n]*[.\n]", re.I)


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        b = r.read()
    return b if raw else b.decode("utf-8", "replace")


def to_text(s):
    """HTML -> plain text, preserving block boundaries as newlines."""
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|ul|ol|h[1-6]|tr|section)>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "\n- ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace(" ", "\n")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n\s*", "\n\n", s)
    return "\n".join(ln.strip() for ln in s.split("\n")).strip()


def _low(text):
    """Lowercased with curly apostrophes folded, so heading literals match either form."""
    return text.lower().replace("\u2019", "'").replace("\u2018", "'")


_ALLOWED_PREFIX = re.compile(r"[\s\-*#>\u2022]*\Z")

# A heading-like line: short, and either ends with ':' or is a known head. Used to find where a
# block STOPS, so a block ends at the next section whatever that section happens to be called.
_HEADLINE = re.compile(r"(?m)^[\s\-*#>\u2022]{0,4}(?=[^\n]{1,112}$)([^\n]*:)\s*$")

# Words that mark a heading as being about the CANDIDATE (qualifications) ...
_QUAL_WORDS = re.compile(r"\b(qualification\w*|requirement\w*|required|skills?|experience|"
                         r"bring|background|looking\s+for|need\s+to\s+see|about\s+you|"
                         r"who\s+you\s+are|you\s+have|minimum|basic|ideal\s+candidate)\b", re.I)
# ... and words that mark it as being about the JOB (responsibilities) — these must not win.
_RESP_WORDS = re.compile(r"\b(you'?ll\s+do|you\s+will\s+do|will\s+build|you'?ll\s+build|"
                         r"responsibilit\w*|the\s+role|you'?ll\s+work|day\s+to\s+day|"
                         r"what\s+we\s+value|benefits?|perks?|about\s+us|the\s+team)\b", re.I)


def _heading_hits(low, heads, start=0):
    """Occurrences of `heads` that look like headings, not prose: line-initial and followed by
    ':' or end of line. This is what stops 'requirements' inside EEO boilerplate from winning."""
    hits = []
    for h in heads:
        i = low.find(h, start)
        while i != -1:
            ls = low.rfind("\n", 0, i) + 1
            if _ALLOWED_PREFIX.match(low[ls:i]):
                tail = low[i + len(h):i + len(h) + 30]
                if tail.lstrip(" ").startswith(":") or tail.strip() == "" or tail.startswith("\n"):
                    hits.append((i, h))
            i = low.find(h, i + 1)
    return sorted(hits)


def _first_heading(low, heads, start=0):
    hits = _heading_hits(low, heads, start)
    return hits[0] if hits else None


def _qual_headline(text, start=0):
    """Any heading-like line that is about the candidate rather than the job.

    Generic on purpose: startup boards invent their own wording ("Required skills and
    experience:", "What You'll Learn / Bring:") and a fixed literal list cannot keep up.
    """
    for m in _HEADLINE.finditer(text, start):
        line = m.group(1)
        if _RESP_WORDS.search(line):
            continue
        if _QUAL_WORDS.search(line):
            return m.start(1), line
    return None


def _next_headline(text, after):
    """Position of the next heading-like line, so a block ends at the following section."""
    m = _HEADLINE.search(text, after)
    return m.start(1) if m else None


def split_blocks(text):
    """Return (minimum_block, preferred_block), heading-driven and tiered.

    Tier 1 exact specific heads -> tier 2 generic candidate-facing headline -> tier 3 generic
    heads. Returns ("", "") rather than a guess when nothing qualifies: a wrong block is worse
    than no block, because the commander would score against it.
    """
    low = _low(text)
    # Explicit requirement heads beat soft persona heads ("who you are", "about you"), which often
    # come first and hold culture copy: Stripe puts "Who you are" above "Minimum requirements".
    mn = (_first_heading(low, [h for h in MIN_HEADS_SPECIFIC if h not in SOFT_HEADS])
          or _first_heading(low, MIN_HEADS_SPECIFIC))
    mstart = mhead = None
    if mn:
        mstart, mhead = mn[0], mn[1]
    else:
        g = _qual_headline(text)
        if g:
            mstart, mhead = g[0], g[1]
        else:
            mn = _first_heading(low, MIN_HEADS_GENERIC)
            if mn:
                mstart, mhead = mn[0], mn[1]
    if mstart is None:
        return "", ""

    after = mstart + len(mhead)
    stops = [p for p in (_next_headline(text, after),
                         (_first_heading(low, STOP_HEADS, after) or (None,))[0]) if p]
    minimum = text[mstart:(min(stops) if stops else len(text))].strip()

    preferred = ""
    pf = _first_heading(low, PREF_HEADS, after)
    if pf:
        pstart = pf[0]
        pafter = pstart + len(pf[1])
        pstops = [p for p in (_next_headline(text, pafter),
                              (_first_heading(low, [h for h in STOP_HEADS if h not in PREF_HEADS],
                                              pafter) or (None,))[0]) if p]
        preferred = text[pstart:(min(pstops) if pstops else len(text))].strip()
    return minimum, preferred


# C++ and C# are unambiguous. Bare "C" is not: "C.S. classes", "C.V.", "Plan C" all false-positive,
# so a bare C only counts when a language cue sits beside it.
CPP_TOKEN = re.compile(r"(?<![A-Za-z+#])(C\+\+|C#|\bC\b)(?![A-Za-z+#])")
_BARE_C_OK = re.compile(r"\b(C\+\+|Java|Python|Rust|Golang|Go|Scala|Kotlin|Swift|Objective-C|"
                        r"languages?|programming)\b", re.I)
# Phrasings that mean "any one of these is fine" — i.e. C/C++ is NOT a hard requirement.
ORLIST_CUES = re.compile(
    r"\b(one or more|at least one|at least \d|such as|e\.?g\.?|for example|for instance|"
    r"including|includes|or similar|or equivalent|or another|any of|one of|"
    r"a modern|modern programming|general purpose programming|"
    r"(?:[A-Za-z+#.]+\s*,\s*){1,}[A-Za-z+#.]+\s*(?:,\s*)?\bor\b|"
    r"[A-Za-z+#.]+\s*/\s*[A-Za-z+#.]+\s*/\s*[A-Za-z+#.]+)", re.I)


def classify_cpp(minimum, preferred):
    """Where does C/C++ actually sit? Tests the qualification block, not the title.

    HARD-GATE = named as a requirement on its own. OR-LIST = one acceptable option among several
    ("languages such as C, C++, Rust"), which is NOT a C/C++ role. PREFERRED = preferred block only.
    Mislabelling an OR-LIST as HARD-GATE wrongly kills a good req under an avoid-C/C++ rule.
    """
    hits = []
    for label, blk in (("HARD-GATE", minimum), ("PREFERRED", preferred)):
        if not blk:
            continue
        for m in CPP_TOKEN.finditer(blk):
            tok = m.group(1)
            # Scope to the ENCLOSING BULLET, not a character window. A wide window picks up an
            # unrelated "OR" from the neighbouring bullet (e.g. "...OR 2+ years in lieu of a
            # degree" next to "1+ years of experience with C/C++") and downgrades a real gate.
            ls = blk.rfind("\n", 0, m.start()) + 1
            le = blk.find("\n", m.end())
            win = blk[ls:(le if le != -1 else len(blk))]
            if tok == "C" and not _BARE_C_OK.search(win):
                continue          # "C.S. classes", "Plan C" — not the language
            tag = "OR-LIST" if ORLIST_CUES.search(win) else label
            hits.append({"token": tok, "placement": tag,
                         "context": re.sub(r"\s+", " ", win).strip()[:200]})
    if not hits:
        return "none", []
    order = {"HARD-GATE": 0, "OR-LIST": 1, "PREFERRED": 2}
    worst = min(hits, key=lambda h: order.get(h["placement"], 3))["placement"]
    return worst, hits


INTERN_PAT = re.compile(r"\b(intern|interns|internship|internships|co-?op|co-?ops)\b", re.I)
NEWGRAD_PAT = re.compile(r"\b(new\s+grad\w*|new\s+college\s+grad\w*|university\s+grad\w*|"
                         r"early\s+career|recent\s+graduate|campus\s+hire|class\s+of\s+20\d\d)\b", re.I)


def guess_type(title, text):
    """Intern / New Grad / Full-time. Title outranks body: body often mentions both programs."""
    t = title or ""
    if INTERN_PAT.search(t):
        return "Intern", True
    if NEWGRAD_PAT.search(t):
        return "New Grad", False
    head = text[:2500]
    if INTERN_PAT.search(head) and not NEWGRAD_PAT.search(head):
        return "Intern", True
    if NEWGRAD_PAT.search(head):
        return "New Grad", False
    return "Full-time", False


def firsts(pat, text, n=1):
    out = [re.sub(r"\s+", " ", m.group(0)).strip() for m in pat.finditer(text)]
    return out[:n]


def enrich(rec, text):
    minimum, preferred = split_blocks(text)
    gate, hits = classify_cpp(minimum, preferred)
    tguess, is_intern = guess_type(rec.get("title"), text)
    rec.update({
        "type_guess": tguess,
        "is_internship": is_intern,   # no-internships-rule: full-time only, ever
        "qual_min": minimum,
        "qual_preferred": preferred,
        "qual_found": bool(minimum),
        "cpp_gate": gate,
        "cpp_hits": hits,
        "caps_quote": firsts(CAP_PAT, text, 2),
        "sponsorship_quote": firsts(SPON_PAT, text, 2),
        "grad_window_quote": firsts(GRAD_PAT, text, 2),
        "yoe_quote": firsts(YOE_PAT, text, 2),
        "jd_chars": len(text),
        "_text": text,          # popped before printing; written to <prefix>.jd.txt with --out-dir
    })
    return rec


# ---------------- per-ATS probes ----------------

def probe_greenhouse(org, jid):
    url = f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{jid}?content=true"
    try:
        j = json.loads(get(url))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"status": "CLOSED", "note": f"greenhouse 404 for {org}/{jid}"}
        return {"status": "UNVERIFIABLE", "note": f"greenhouse HTTP {e.code}"}
    text = to_text(j.get("content", ""))
    rec = {"status": "LIVE", "title": (j.get("title") or "").strip() or None,
           "location": (j.get("location") or {}).get("name"),
           "url": j.get("absolute_url"),
           "first_published": j.get("first_published"),
           "updated_at": j.get("updated_at"),
           "application_deadline": j.get("application_deadline"),
           # IMC's updated_at was board-wide; first_published is per-req, use it for freshness.
           "freshness_field": "first_published",
           "note": ""}
    if org.lower() == "imc":
        rec["note"] = ("IMC: judge freshness by first_published, not updated_at "
                       "(updated_at has historically been board-wide).")
    return enrich(rec, text)


def probe_ashby(org, want=None):
    """`want` may be an Ashby job UUID (from the posting URL) or a title substring."""
    try:
        j = json.loads(get(f"https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true"))
    except urllib.error.HTTPError as e:
        return [{"status": "UNVERIFIABLE", "note": f"ashby HTTP {e.code} for {org}"}]
    jobs = j.get("jobs") or []
    if want:
        w = want.lower()
        is_uuid = bool(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", w))
        if is_uuid:
            jobs = [x for x in jobs if (x.get("id") or "").lower() == w]
        else:
            jobs = [x for x in jobs if w in (x.get("title") or "").lower()]
    if not jobs:
        # Board fetched fine but this posting is gone -> genuinely closed/unlisted.
        return [{"status": "CLOSED" if want else "UNVERIFIABLE",
                 "note": f"ashby {org}: posting not on the live board" + (f" ({want})" if want else " (board empty)")}]
    out = []
    for x in jobs:
        text = to_text(x.get("descriptionHtml") or "") or (x.get("descriptionPlain") or "")
        rec = {"status": "LIVE" if x.get("isListed", True) else "CLOSED",
               "title": x.get("title"), "location": x.get("location"),
               "url": x.get("jobUrl"), "first_published": x.get("publishedAt"),
               "updated_at": x.get("updatedAt"),
               "employment_type": x.get("employmentType"),
               "freshness_field": "publishedAt", "note": ""}
        out.append(enrich(rec, text))
    return out


def probe_lever(org, jid=None):
    try:
        arr = json.loads(get(f"https://api.lever.co/v0/postings/{org}?mode=json"))
    except urllib.error.HTTPError as e:
        return [{"status": "UNVERIFIABLE", "note": f"lever HTTP {e.code} for {org}"}]
    if isinstance(arr, dict):
        return [{"status": "UNVERIFIABLE", "note": f"lever: {arr.get('error', 'unexpected shape')}"}]
    if jid:
        arr = [x for x in arr if x.get("id") == jid]
        if not arr:
            return [{"status": "CLOSED", "note": f"lever {org}: id {jid} not on board"}]
    out = []
    for x in arr:
        text = to_text(x.get("descriptionHtml") or x.get("description") or "")
        for lst in (x.get("lists") or []):
            text += "\n\n" + (lst.get("text") or "") + "\n" + to_text(lst.get("content") or "")
        rec = {"status": "LIVE", "title": x.get("text"),
               "location": ((x.get("categories") or {}).get("location")),
               "url": x.get("hostedUrl"), "first_published": x.get("createdAt"),
               "updated_at": x.get("createdAt"), "freshness_field": "createdAt", "note": ""}
        out.append(enrich(rec, to_text(text)))
    return out


def probe_google(jid):
    """Live page contains its own title >=1x; a dead req silently returns the generic listing."""
    base = "https://www.google.com/about/careers/applications/jobs/results/"
    try:
        page = get(base + str(jid))
    except urllib.error.HTTPError as e:
        return {"status": "CLOSED" if e.code == 404 else "UNVERIFIABLE",
                "note": f"google HTTP {e.code}"}
    text = to_text(page)
    m = re.search(r'\["' + re.escape(str(jid)) + r'","([^"]{5,120})"', page)
    title = m.group(1) if m else None
    if not title:
        m2 = re.search(r"<title>([^<]+)</title>", page)
        title = (m2.group(1).split("—")[0].strip() if m2 else None)
    occ = text.lower().count(title.lower()) if title else 0
    live = bool(title) and occ >= 1 and ("minimum qualifications" in text.lower())
    rec = {"status": "LIVE" if live else "CLOSED",
           "title": title, "location": None,
           "url": base + str(jid), "first_published": None, "updated_at": None,
           "freshness_field": None, "title_occurrences": occ,
           "note": ("Google: location/salary are NOT reliably extractable (regex lands on the "
                    "embedded listing JSON) — read those on the page. Liveness = own title present "
                    "AND a qualifications heading present.")}
    return enrich(rec, text)


def probe_amazon(query):
    q = urllib.parse.urlencode({"base_query": query, "country": "USA",
                                "result_limit": 40, "sort": "recent"})
    try:
        j = json.loads(get("https://www.amazon.jobs/en/search.json?" + q))
    except urllib.error.HTTPError as e:
        return [{"status": "UNVERIFIABLE", "note": f"amazon HTTP {e.code}"}]
    out = []
    for x in (j.get("jobs") or []):
        text = "\n\n".join(filter(None, [
            to_text(x.get("description") or ""),
            "BASIC QUALIFICATIONS\n" + to_text(x.get("basic_qualifications") or ""),
            "PREFERRED QUALIFICATIONS\n" + to_text(x.get("preferred_qualifications") or "")]))
        rec = {"status": "LIVE", "title": x.get("title"),
               "location": x.get("normalized_location") or x.get("location"),
               "url": "https://www.amazon.jobs" + (x.get("job_path") or ""),
               "first_published": x.get("posted_date"), "updated_at": x.get("updated_time"),
               "freshness_field": "posted_date",
               "note": "Amazon: early-career reqs are often labelled with the current year, not the "
                       "graduation year. If a search returns nothing, try the other year."}
        out.append(enrich(rec, text))
    return out


MS_NOTE = ("Microsoft has no usable API ({'message':'Not authorized for PCSX'}) and "
           "jobs.careers.microsoft.com 301s to a landing page. Verify in the UI via "
           "apply.careers.microsoft.com/careers?query=<jobnumber>.")


def resolve(spec):
    """spec -> list of records. Accepts scheme:args or any career URL."""
    s = spec.strip()
    if not s or s.startswith("#"):
        return []
    low = s.lower()

    m = re.match(r"^(greenhouse|ashby|lever|google|amazon):(.+)$", s, re.I)
    if m:
        kind, arg = m.group(1).lower(), m.group(2)
        if kind == "greenhouse":
            org, _, jid = arg.partition("/")
            return [probe_greenhouse(org, jid)] if jid else [{"status": "UNVERIFIABLE",
                    "note": "greenhouse spec needs org/id"}]
        if kind == "ashby":
            org, _, want = arg.partition("/")
            return probe_ashby(org, want or None)
        if kind == "lever":
            org, _, jid = arg.partition("/")
            return probe_lever(org, jid or None)
        if kind == "google":
            return [probe_google(arg.split("-")[0])]
        if kind == "amazon":
            return probe_amazon(arg)

    if "greenhouse.io" in low:
        mm = re.search(r"/(?:boards/)?([A-Za-z0-9_-]+)/jobs/(\d+)", s)
        if mm:
            return [probe_greenhouse(mm.group(1), mm.group(2))]
    if "ashbyhq.com" in low:
        mm = re.search(r"ashbyhq\.com/(?:job-board/)?([A-Za-z0-9_.-]+)"
                       r"(?:/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                       r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}))?", s)
        if mm:
            return probe_ashby(mm.group(1), mm.group(2))
    if "lever.co" in low:
        mm = re.search(r"lever\.co/([A-Za-z0-9_-]+)(?:/([0-9a-f-]{8,}))?", s)
        if mm:
            return probe_lever(mm.group(1), mm.group(2))
    if "google.com/about/careers" in low:
        mm = re.search(r"/results/(\d{6,})", s)
        if mm:
            return [probe_google(mm.group(1))]
    if "amazon.jobs" in low:
        mm = re.search(r"/jobs/(\d+)", s)
        return probe_amazon(mm.group(1) if mm else s)
    # Company careers pages that embed Greenhouse: stripe.com/jobs/search?gh_jid=8212508.
    # The board slug is usually the company's domain name; a 404 means the guess was wrong,
    # not that the job closed, so never report CLOSED from a guess.
    mm = re.search(r"[?&]gh_jid=(\d+)", s)
    if mm:
        host = urllib.parse.urlparse(s if "://" in s else "https://" + s).hostname or ""
        labels = [p for p in host.split(".") if p not in ("www", "careers", "jobs", "boards")]
        if labels:
            rec = probe_greenhouse(labels[0], mm.group(1))
            if rec.get("status") != "CLOSED":
                return [rec]
        return [{"status": "UNVERIFIABLE", "url": s,
                 "note": f"Greenhouse job {mm.group(1)} embedded on a company site; board slug not "
                         f"guessed. Run find_boards.py <company>, then greenhouse:<slug>/{mm.group(1)}"}]
    if "careers.microsoft.com" in low:
        mm = re.search(r"(\d{6,})", s)
        return [{"status": "NEEDS-UI", "url": s, "title": None,
                 "note": MS_NOTE + (f" jobnumber={mm.group(1)}" if mm else "")}]
    return [{"status": "UNVERIFIABLE", "url": s,
             "note": "unrecognised ATS — needs WebFetch or the browser, hand to a scout"}]


def main():
    ap = argparse.ArgumentParser(description="Tier 0 deterministic req probe for /jobsweep")
    ap.add_argument("specs", nargs="*")
    ap.add_argument("-f", "--file", help="file of specs/URLs, one per line")
    ap.add_argument("--out-dir", help="write extracted JD + qualifications text here")
    ap.add_argument("--table", action="store_true", help="human summary to stderr")
    a = ap.parse_args()

    specs = list(a.specs)
    if a.file:
        with open(a.file) as fh:
            specs += [ln.strip() for ln in fh if ln.strip() and not ln.strip().startswith("#")]
    if not specs:
        ap.error("no specs given")
    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)

    rows = []
    for spec in specs:
        try:
            recs = resolve(spec)
        except Exception as e:
            recs = [{"status": "UNVERIFIABLE", "note": f"{type(e).__name__}: {e}"}]
        for rec in recs:
            rec.setdefault("spec", spec)
            rec.setdefault("title", None)
            if a.out_dir and rec.get("_text"):
                key = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{rec.get('title') or 'req'}").strip("_")[:70] or "req"
                for suffix, body in (("jd", rec.get("_text", "")),
                                     ("qual_min", rec.get("qual_min", "")),
                                     ("qual_pref", rec.get("qual_preferred", ""))):
                    with open(os.path.join(a.out_dir, f"{key}.{suffix}.txt"), "w") as fh:
                        fh.write(body)
                rec["out_prefix"] = os.path.join(a.out_dir, key)
                with open(os.path.join(a.out_dir, f"{key}.truth.json"), "w") as fh:
                    json.dump({k: v for k, v in rec.items() if k != "_text"}, fh,
                              ensure_ascii=False, indent=2)
            rec.pop("_text", None)
            print(json.dumps(rec, ensure_ascii=False))
            rows.append(rec)

    if a.table:
        w = sys.stderr
        w.write(f"\n{'STATUS':<13}{'TYPE':<11}{'CPP':<10}{'QUAL':<6}TITLE\n")
        for r in rows:
            t = r.get("type_guess") or "-"
            if r.get("is_internship"):
                t = "INTERN!"          # no-internships-rule: full-time only, ever
            w.write(f"{r.get('status',''):<13}{t:<11}{str(r.get('cpp_gate','-')):<10}"
                    f"{('yes' if r.get('qual_found') else 'NO'):<6}{(r.get('title') or r.get('spec'))[:52]}\n")
            if r.get("status") in ("UNVERIFIABLE", "NEEDS-UI") and r.get("note"):
                w.write(f"{'':<40}-> {r['note'][:100]}\n")
        w.write(f"\n{len(rows)} req(s). "
                f"interns dropped by rule={sum(1 for r in rows if r.get('is_internship'))}. "
                f"LIVE={sum(1 for r in rows if r.get('status')=='LIVE')} "
                f"CLOSED={sum(1 for r in rows if r.get('status')=='CLOSED')} "
                f"UNVERIFIABLE={sum(1 for r in rows if r.get('status')=='UNVERIFIABLE')} "
                f"NEEDS-UI={sum(1 for r in rows if r.get('status')=='NEEDS-UI')}\n")


if __name__ == "__main__":
    main()
