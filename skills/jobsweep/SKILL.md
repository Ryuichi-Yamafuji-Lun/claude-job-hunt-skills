---
name: jobsweep
description: Run a job sweep — verify tracked roles are still live, discover new ones, fit-score them against the real job description, and write anything that clears your threshold into your tracker. Use when the user says "run the job sweep", "check for new jobs", "any new roles", or asks what to apply to this week.
---

# Job Sweep

Runs a job search end to end: verify → discover → score → record. **Run it locally.** See "Why this is a skill and not a cloud routine" at the bottom.

## Who you're talking to

Assume a new user who doesn't know this skill's vocabulary (ATS, req, lane, tier 0). Explain things in plain words, and never ask them to edit a config file; ask the question and write the answer in yourself.

## Step 0 — Load context first, always

Read `~/.claude/job-search/profile.md` before anything else. It holds the user's lanes, eligibility facts, caps, closed companies, tracker location, and live state. Don't re-derive decisions the profile records.

**First run** (no profile, or `Job search setup done: no`): create the profile from `~/.claude/job-search/templates/profile.md` if it's missing, then ask **one message** with only what a sweep needs, offering examples. Skip any question the profile already answers (for example, if `/tailor-apply` ran first):
1. What kind of roles, full-time only or internships too? (e.g. "new-grad software engineer, backend or ML infra, full-time")
2. What are you strongest at? Two to four areas. (These become the "lanes" used for fit scoring.)
3. When can you start, and how much professional experience do you have? (internships count)
4. Do you need visa sponsorship?
5. Which locations, or remote?
6. Any companies you've already applied to, or want to skip?
7. Any companies you'd love to work at? Optional. I'll also suggest some that hire for what you do.
8. Are there job sites you're logged into that I may read for you, like Handshake (school jobs) or Wellfound? Default: none. I'll only use public company job boards, which need no login.

Then, before sweeping:
- Write the answers into the profile. Record question 8 under **What Claude may access**, exactly as allowed and nothing broader (an unmentioned site stays `not asked yet`).
- **Build the starting company list.** Take the user's companies, add 15–25 well-known companies that hire for their lanes, level and regions, and show the combined list for a quick yes or edits. Then map each to its public board:
  ```bash
  python3 ~/.claude/skills/jobsweep/scripts/find_boards.py "Company A" "Company B" ...
  ```
  Save the `greenhouse:…` / `ashby:…` / `lever:…` specs under **Public boards to check**. List "not found" companies there too, marked "check by hand", and tell the user those use their own career sites.
- The tracker defaults to Markdown (`~/.claude/job-search/tracker.md`), which needs no setup. Mention once that Notion or Google Sheets also work if they have that connector.
- Set `Job search setup done: yes`, say in 2–3 lines what the sweep is about to do, and run it.

**Do NOT read `~/.claude/job-search/sweep-log.md`** unless you need the provenance of one specific past call. It grows every sweep and costs tokens on every turn once opened.

**The profile's House rules override this file.** Settings in the profile (score weights, threshold, caps) override the defaults below.

🔴 **Read the record before any verdict.** When sources disagree, precedence is: **the tracker and the user's real inboxes/calendar** (what they actually did) > **this skill's logs** (what was measured) > **profile notes** (what was planned). Before saying a role is open, unapplied, or missing, check the tracker. Before saying a file or result doesn't exist, search for it broadly (`find ~ -iname "*<token>*"`) at least once; re-running the same check in the same wrong place doesn't validate it.

## Commander / scouts — how the work is split

The main session is the commander: it decides what to check, scores, writes the tracker, and talks to the user. **All fetching and JD extraction fans out to the `jd-scout` agent** (a cheaper model): Steps 1 and 3 run in parallel batches of 5–10 reqs per agent, so raw page dumps never enter the commander's context. The scout returns the qualification block **quoted verbatim**; the commander scores from the quote and double-checks the scout's STATUS/TYPE/START calls against it. If a scout's quote and its own summary disagree, trust the quote and re-check.

## Step 1 — Verify tracked roles: tier 0 first, then scouts

**Nothing tracked yet (first sweep)?** Skip to Step 2.

Write the tracked roles' links to a scratch `reqs.txt`, one per line, then **run tier 0 before spawning any scout.** `scripts/ats_probe.py` is deterministic, free, and cannot hallucinate. It covers Greenhouse, Ashby, Lever, Amazon and Google:

```bash
~/.claude/skills/jobsweep/scripts/ats_probe.py -f reqs.txt --table --out-dir ./jd
```

It returns status, title, location, `first_published`, full-slug URL and the qualifications block as JSON. Score straight from that for every req it marks LIVE or CLOSED. **Only `UNVERIFIABLE` (unknown ATS) and `NEEDS-UI` (Microsoft) rows need a scout**; hand those out 5–10 per agent. See `scripts/README.md`.

Tier 0 also writes ground truth to `--out-dir`, so `scripts/scout_verify.py` can check a scout's quote mechanically instead of trusting it. Run it on any sweep where a scout's numbers look surprising, and before changing the scout's model.

```bash
# Greenhouse
curl -s "https://boards-api.greenhouse.io/v1/boards/{org}/jobs"                     # full board
curl -s "https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{id}?content=true"   # full JD

# Ashby
curl -s "https://api.ashbyhq.com/posting-api/job-board/{org}"

# Amazon: returns basic_qualifications + preferred_qualifications inline
curl -s "https://www.amazon.jobs/en/search.json?base_query=<terms>&country=USA&result_limit=40&sort=recent"
```

**Traps that have produced wrong answers before:**

- **Greenhouse `updated_at` can be board-wide.** Some boards (IMC, Stripe) have reported one timestamp across every req. Use **`first_published`**, which is per-req and is what `ats_probe.py` reports as `freshness_field`. Board presence is the liveness signal.
- **Amazon early-career searches use the current year, not the grad year.** Searching "software development engineer <grad year>" can return 0 hits while "<current year>" returns the real early-career reqs. Try both.
- **Never declare a role closed from a truncated ATS URL.** Some Workday/Phenom sites return "no longer available" for a URL without the title slug while the full-slug URL is live. Use the complete URL before calling anything dead.
- **Microsoft migrated hosts.** `jobs.careers.microsoft.com/...` 301s to a generic landing page, so live reqs look dead. Use `apply.careers.microsoft.com/careers?query=<jobnumber>`. Its API is not public; use the UI.
- **"New College Grad" titles are unreliable** (NVIDIA especially). Read the requirements block on every req; some NCG-labelled reqs demand 2+ years. "Applications accepted at least until [date]" is a legal minimum posting period, not a deadline.
- **Location must come from the req's own page.** Google's early-career search is global unless the URL includes `&location=<country>`, and a page-wide "City, ST" regex grabs locations from the embedded listing of *other* jobs. Read the location block that belongs to this req, and name the location + req id so the user can verify in one click. Same trap for the qualifications block: take the first one on the req's own page.
- **Google Careers pages ARE curl-able.** `curl -A "<desktop UA>" https://www.google.com/about/careers/applications/jobs/results/<id>-<slug>` returns the JD server-side; grep `Minimum qualifications:` / `Preferred qualifications:`. A CLOSED req silently returns the generic listing: a live page contains its own title at least once, a dead one zero times. WebFetch returns only the SPA shell; use curl.

## Step 2 — Discover new roles

🔒 **Logged-in sites are opt-in, per site.** Read **What Claude may access** in the profile. Public company boards and their APIs need no permission. **Any site that uses the user's login** (Handshake, LinkedIn, Wellfound, Indeed, a school portal) is used **only if the user listed it there.** If a sweep would benefit from an unlisted site, ask once in one line (*"Handshake often has school-only postings. May I read it using your logged-in browser? I'll only read job listings."*). Then record the answer either way and don't ask again. When allowed:
- **Read only.** Never apply, message, connect, follow, save jobs, or change anything on the account.
- **Never log in for the user** or type a password. If the session is logged out, ask the user to log in and say when.
- Keep it light: a few searches per sweep, not page after page.
- **LinkedIn specifically:** its terms forbid automated access, and accounts do get restricted. Before the first use, tell the user that and suggest the safer route: they search LinkedIn themselves and paste links, which `ats_probe.py` and the scouts then verify on the company's own board. Use the browser on LinkedIn only if they still say yes after hearing that.
- Scouts (`jd-scout`) never touch logged-in sites. They only fetch public pages.

**Discovery sources, in order:** (1) allowed logged-in boards; (2) every board under **Public boards to check**, in one command:
```bash
python3 ~/.claude/skills/jobsweep/scripts/list_jobs.py <all the greenhouse:/ashby:/lever: specs> \
    --location "<the profile's regions as a regex, e.g. san francisco|new york|remote>"
```
It keeps entry-level engineering titles and drops internships and senior roles by default. Widen it for other fields with `--role` (e.g. `--role "data|analyst"`), and pass `--days 7` on routine sweeps to see only new postings. Each line starts with a spec that `ats_probe.py` takes, so verify the promising ones next. (3) For companies not on a public board yet, run `find_boards.py` first. When a user mentions a company mid-session, add it to the profile.

**Check allowed private/school boards FIRST.** They carry school-targeted postings that never appear on public career sites. Handshake specifics, when allowed:

```
app.joinhandshake.com/job-search?query=<terms>&page=1&per_page=25&sort=posted_date_desc
```

Read `a[href*="/job-search/1"]`, then take `a.parentElement.innerText` (the anchor itself has no text). Handshake **AND**s all terms, so keep queries to 2–3 words. Its search is fuzzy relevance, not exact match: it is for *discovery* only and cannot verify whether a specific known role is still open. Verify on the company board.

Then run **two streams**: cohort / new-grad programs *and* rolling entry-level titles (`Software Engineer I`, `Associate Software Engineer`, `Junior Software Engineer`, `Backend Engineer I`, `Platform Engineer I`, or whatever the profile's target titles are). The rolling stream hires year-round with 4–8 week starts.

**If the profile says full-time only, filter internships at discovery**, not at scoring. `ats_probe.py` emits `is_internship`; Ashby's API has `employmentType`; Handshake tags internships and shows hourly pay; on Greenhouse, grep the JD for intern / co-op / duration / hourly. Full-time tells: equity band, 401k, parental leave. **A summer start date is not an internship**: many new-grad roles start in summer. Titles like "Early Careers", "Emerging Talent", "University Grad" and "Associate" are usually full-time; verify.

**Freshness is a ranking axis, not a filter.** Early applicants get read by a human, so a req posted in the last 24 hours goes to the top of the list regardless of fit. It never retires backlog: older reqs are triaged by fit × deadline.

## Step 3 — Fit-score against the real JD: scouts fetch, commander scores

Never score from a title. Have `jd-scout` pull the full JD and quote the qualification block; score from the quote. Score /100 using the profile's weights if it sets them, otherwise roughly:

- **~40 pts — domain match** against the profile's lanes. Reqs centred on a listed weak area cap out near 68 no matter how the resume is written.
- **~25 pts — eligibility.** Degree/YOE gates, graduation-window language, sponsorship, the avoid-language gate. Read sponsorship lines against the user's work authorization: "sponsorship is not offered" is a **plus** for someone who doesn't need it (it thins the pool) and a hard stop for someone who does.
- **~20 pts — start date.** Can it start by the profile's latest acceptable start date?
- **~15 pts — comp and seniority sanity.**

🔴 **Score YOE gates against the profile's professional months only.** Unpaid or student research roles are not employment and must never be counted as professional YOE. A 2+ year gate is a genuine risk; a 3+ year gate usually fails a recruiter's title scan.

Scores are judgment calls, ±5. **Surface a 70 with the score attached** rather than silently filtering it. That's the user's call, not yours.

## Step 4 — Write to the tracker

Use the tracker the profile names: **Markdown** (default, no connector needed): add or update rows in the table in `~/.claude/job-search/tracker.md`, keeping its column order; **Notion** needs the Notion MCP connector; **Sheets** needs a Google Sheets connector. If the profile names a connector that isn't available this session, say so in one line, write the rows to the Markdown tracker instead, and tell the user where they went. Write a row only when the score clears the profile's threshold (default 75), plus two standing carve-outs: **early-start roles** (a 72 that starts on time beats a 90 that leaves a six-month gap) and an optional **practice tier** (low priority, deliberately low fit, purpose is OA reps).

Record at least: company, title, URL, fit score, source, verified-on date, start window, next action. **A blank fit score means NOT YET AUDITED. Never assume a score.**

Use only the status/priority values the tracker accepts (they're listed in the profile). If the tracker has no Closed option, demote dead rows via priority + notes rather than inventing a status.

## Step 5 — Respect the caps before recommending anything

Check every recommendation against the profile's per-company caps and closed pipelines. When a capped company has more good reqs than slots, **force a pick** and say which one and why. Default allocation for capped companies: most slots on new-grad reqs, about one on a regular req as a hedge. Do not argue the user out of a cap decision they've already recorded.

## Step 6 — Record findings (two-tier)

**Append** a dated section to `~/.claude/job-search/sweep-log.md` (write-only, do not read it first): what was verified live, what was newly found with its score, what could not be verified and why, any new trap. Then **rewrite in place** the affected lines of `profile.md` (the live state, caps, open items), keeping it under ~6 KB. Never append session notes to the profile.

Then hand off, sorted by freshness first and fit second:
- **Tailor** (`/tailor-apply <company>`): fit at or above the profile's tailor threshold (default 78), any name-brand company where the resume screen is the whole gate, any well-funded early-stage startup where one new-grad seat is visible to the founders, or any req with a required essay.
- **Quick apply** (`/tailor-apply quick`): everything else worth sending, with the generic resume.

Say which side each role falls on and why. **Never quietly drop a strong role into the quick tier to save time**: tailoring typically moves a fit score 8–12 points, and at one-application-per-season companies a weak first shot is unrecoverable.

Last, one line: *did the user have to correct anything this sweep?* If so, write it into the profile's House rules as an imperative rule now, with the words that caused it.

## Why this is a skill and not a cloud routine

A scheduled cloud routine generally **cannot do this job**: cloud sandboxes are often egress-blocked from career domains, they may have no connectors attached to write the tracker, and login-gated boards are reachable only from a local browser session. A routine can remind the user to run this skill; it can't replace it. If the user believes a routine is auto-populating the tracker, check the creation time on the newest rows before agreeing.
