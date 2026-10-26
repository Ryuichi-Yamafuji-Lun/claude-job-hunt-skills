# jobsweep tier 0 + scout verification

Four scripts. None of them uses a model.

| script | job |
|---|---|
| `find_boards.py` | Company names → which public board each uses (`greenhouse:stripe`, `ashby:notion`, …). Picks the busiest board when a company has an old one left over. |
| `list_jobs.py` | Lists matching open roles across many boards in one go, newest first, filtered by level, role and location. Output specs feed straight into `ats_probe.py`. |
| `ats_probe.py` | Tier 0. Pulls liveness, title, location, posting date, full-slug URL and the qualifications block straight from public ATS APIs. Deterministic, free, cannot hallucinate. |
| `scout_verify.py` | Checks a `jd-scout` report against tier-0 ground truth. Mechanical. Catches the paraphrase/truncation the commander structurally cannot see. |

## Why tier 0 exists

The old flow was two tiers: scout (Sonnet) fetches and extracts, Opus scores from the scout's quote.
But most tracked reqs live on Greenhouse / Ashby / Lever / Amazon, which **return structured JSON**.
Liveness, title, location, posting date and the qualifications text are all mechanically extractable.
Paying a model to read a page dump for that is paying for judgment where there is none to apply.

Tier 0 also removes the page dump from the model's input entirely, which shrinks the scout's error
surface at the same time as its cost.

```
tier 0  ats_probe.py   liveness, title, location, dates, qualifications block   free, deterministic
tier 1  scout (model)  only the messy paths: no API, login-gated, JS-only        judgment
tier 2  Opus           fit score                                                judgment
```

## Usage

```bash
# single req
./ats_probe.py greenhouse:imc/4673650101
./ats_probe.py google:118616007559258822
./ats_probe.py amazon:"software development engineer 2026"     # 2026, not 2027

# a tracker batch, with a human summary and ground-truth dumps
./ats_probe.py -f reqs.txt --table --out-dir ./jd
```

Accepts `greenhouse:org/id`, `ashby:org[/title-substr]`, `lever:org[/id]`, `google:id`,
`amazon:query`, or any career URL (auto-detected). Emits JSONL on stdout.

`--out-dir` writes per req: `<title>.jd.txt` (full plain text), `.qual_min.txt`,
`.qual_pref.txt`, `.truth.json`. Those are what `scout_verify.py` diffs against.

Statuses: `LIVE` · `CLOSED` · `NEEDS-UI` (Microsoft) · `UNVERIFIABLE` (unknown ATS, hand to a scout).

It also emits, per req:

- `type_guess` (`Intern` / `New Grad` / `Full-time`) and **`is_internship`**, so the
  full-time-only filter is applied mechanically rather than by eye. Amazon's search *does* return
  intern reqs mixed in with early-career ones, so this matters. The `--table` view shows `INTERN!`.
- `cpp_gate` (`HARD-GATE` / `OR-LIST` / `PREFERRED` / `none`) plus `cpp_hits` with the surrounding
  context, computed from **where the token sits in the blocks**, not from the title.
- `freshness_field` naming the date field to trust for that ATS (`first_published` on Greenhouse).
- Line-bounded quotes for caps, sponsorship, graduation window and YOE.

**It returns no qualifications block rather than a guess.** Heading detection is heading-anchored and
tiered: specific heads (`minimum qualifications`, `your skills and experience`, `what we need to see`)
are trusted; generic ones (`requirements`, `qualifications`) are a fallback only, because they also
occur in prose and EEO boilerplate. A wrong block is worse than none, since Opus would score it.

## The Haiku A/B: is the cheap scout tier safe?

A shell script cannot spawn subagents, so this part is run by the commander (Opus). The scripts
supply ground truth and the grading.

1. **Pick 8 reqs** spanning the shapes that actually break things: 2 Greenhouse, 1 Ashby or Lever,
   1 Amazon, 2 Google, 1 Microsoft, 1 unknown ATS. Include at least one with C/C++ in the
   **minimum** block and one with it only in **preferred** — that pair is what tests the
   avoid-language (C/C++) classification.

2. **Build ground truth:** `./ats_probe.py -f reqs.txt --out-dir ./jd --table`

3. **Run both scout tiers on the same 8 reqs.** Spawn `jd-scout` twice, overriding `model` on the
   Agent call (`sonnet` / `haiku`). Tell each to write one report per req to `./rep_sonnet/NN.md`
   and `./rep_haiku/NN.md`, where `NN` is the req's **two-digit position in `reqs.txt`** — that is
   the same order `ats_probe.py` emits, so pairing needs no title matching.

   **Tell both scouts NOT to run `ats_probe.py`.** The A/B measures the model's own extraction; if
   a scout calls tier 0, both arms return identical output and the test proves nothing.

4. **Grade:** `./scout_verify.py --ab ./rep_sonnet ./rep_haiku --truth-dir ./jd --index-from ./truth.jsonl`

   `--index-from` takes the JSONL that step 2 wrote and pairs `NN.md` to the Nth record. Reqs with
   no tier-0 ground truth (Microsoft `NEEDS-UI`, unknown ATS) are listed as ungradeable rather than
   passed over in silence. Without `--index-from` it falls back to matching titles in filenames.

Exit code 0 means the cheaper tier had no more critical failures than the expensive one.

### The six checks

| check | critical | what it catches |
|---|---|---|
| `TEMPLATE` | | dropped or renamed fields |
| `STATUS` | ✓ | disagreement, **especially `UNVERIFIABLE` on a req tier 0 fetched fine** (silent lost coverage) |
| `QUOTE_FIDELITY` | ✓ | the quoted block is not a verbatim substring of source. Reports per-bullet coverage, so truncation and paraphrase are distinguishable |
| `LOCATION` | | blank or non-overlapping location |
| `CPP_CLASS` | ✓ | HARD-GATE vs OR-LIST vs PREFERRED mismatch, which mis-scores the avoid-language gate |
| `CAPS` | | scout said "none seen" where a real application cap exists |

`QUOTE_FIDELITY` is the one that matters most. The cascade's safety property is "the scout quotes
verbatim, Opus verifies against the quote" — but Opus never sees the source, so it can only catch a
scout disagreeing with *itself*. A scout that paraphrases produces a self-consistent, plausible,
wrong input and gets scored with confidence. This check is the only thing standing there.

### Reading the result

Cost is not the reason to do this. At ~20 reqs a sweep the Sonnet→Haiku swap saves roughly
20 cents, about $10/year. **The reason is coverage:** at the same spend the cheaper tier screens
about twice as many reqs, and more reqs screened means more chances at a 75+.

So the asymmetry to respect is: downside of a degraded scout is a missed req; upside is $10/year.
If `QUOTE_FIDELITY` or `CPP_CLASS` regresses at all, keep Sonnet on the scouts and spend the
savings on width instead.
