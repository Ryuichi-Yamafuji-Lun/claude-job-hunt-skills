# Claude Code job-hunt kit

Three [Claude Code](https://claude.com/claude-code) skills for a software job search: **find roles that actually fit you, tailor your resume and apply, and practice for the coding interview.**

| Skill | What it does |
|---|---|
| **`/jobsweep`** | Finds open roles at the companies you care about, scores each one against the **real** job description (not the title), and keeps a tracker of what's worth applying to. |
| **`/tailor-apply`** | Tailors your resume to one job: a recruiter-style audit (match score, 5 missing keywords, 3 red flags), a rewrite using Google's XYZ formula, and a final check. Then it hands you the application and confirms it really went through. A `quick` mode batches lower-priority roles with your generic resume. |
| **`/interview-drill`** | Runs a short diagnostic, remembers exactly what you struggle with, and generates new LeetCode-style problems aimed at those weak spots. Mock interviews, timed OA simulations, guided study, and `stats` to see your mastery per topic. |

No setup files to edit: the first time you run each skill, it asks you a few questions and remembers the answers.

---

## Contents

- [Install](#install)
- [Quick start](#quick-start)
- [How each skill works](#how-each-skill-works)
- [You control what Claude can access](#you-control-what-claude-can-access)
- [Make it yours](#make-it-yours)
- [Troubleshooting](#troubleshooting)
- [Design choices](#design-choices)
- [What's in this repo](#whats-in-this-repo)

---

## Install

**You need:** [Claude Code](https://claude.com/claude-code), Python 3.8 or newer (macOS and most Linux distributions already have it), and macOS or Linux. On Windows, use WSL.

**Option A: git**

```bash
git clone https://github.com/Ryuichi-Yamafuji-Lun/claude-job-hunt-skills.git
cd claude-job-hunt-skills
bash install.sh
```

**Option B: download a ZIP.** Click **Code → Download ZIP** at the top of this page and unzip it. Open a terminal in the unzipped folder and run:

```bash
bash install.sh
```

Then **restart Claude Code** (or open a new session) so it picks up the new skills.

The installer copies the skills into `~/.claude/skills/` and creates your personal files in `~/.claude/job-search/`. After that you can delete the downloaded folder.

| | |
|---|---|
| **Update** | Download the new version and run `bash install.sh` again. Your profile, tracker and practice history are never touched. |
| **Uninstall** | `bash install.sh --uninstall`. Your files in `~/.claude/job-search/` stay until you delete that folder. |
| **Already have a skill with the same name?** | The installer moves yours to `~/.claude/job-hunt-kit-backup-<date>/` instead of overwriting it, and tells you. |

---

## Quick start

| I want to… | Type in Claude Code |
|---|---|
| find jobs that fit me | `/jobsweep` |
| tailor my resume to a job and apply | `/tailor-apply` and paste the job link |
| practice coding interviews | `/interview-drill` |
| see my practice progress | `/interview-drill stats` |

**What to have ready:**
- For `/jobsweep`: what kind of roles you want, your strongest areas, when you can start, and (optionally) companies you like.
- For `/tailor-apply`: your resume as a file (PDF, Word, Markdown or text), a Google Docs link, or pasted text.
- For `/interview-drill`: nothing. It asks which language you use.

Your job tracker is a simple Markdown table at `~/.claude/job-search/tracker.md`, so no Notion or Google Sheets is required. You can switch to either later.

---

## How each skill works

### `/jobsweep`: find and score roles

**First run** asks about 8 short questions (roles you want, your strengths, start date, sponsorship, locations, dream companies, and which logged-in sites it may use). It then suggests 15–25 companies that hire for what you do. Once you approve the list, it finds each company's public job board.

**Every sweep:**
1. **Checks** that roles in your tracker are still open.
2. **Finds** new entry-level roles across all your companies' boards, newest first, filtered to your locations.
3. **Scores** each one out of 100 against the actual job description: how well it matches your strengths, whether you meet the requirements (degree date, years of experience, sponsorship), whether the start date works, and pay and level.
4. **Records** anything scoring 75+ in your tracker, and tells you which roles to tailor for and which to batch-apply.

Titles mislead. In testing, a role titled "Software Engineer, Early Career" turned out to require a degree completed before the candidate's graduation date, and another said "This is NOT a new grad role." The sweep reads the job description so you don't waste an application.

### `/tailor-apply`: tailor, apply, confirm

```
/tailor-apply Stripe            then paste the job link or description
> resume review                 Stage 1: recruiter audit (score, 5 missing keywords, 3 red flags)
                                Stage 2: XYZ rewrite of your experience section
> final review                  Stage 3: verification (new score, keyword and bullet checks)
/tailor-apply quick             batch ~10 lower-priority roles with your generic resume
```

- It checks hard requirements **before** tailoring, so you don't polish a resume for a role you can't get.
- It never invents numbers. If a bullet needs a metric, it asks you for one.
- It keeps 3–4 bullets per role, one line per bullet where possible, one page.
- **You press Submit, always.** Afterward it confirms the "thank you for applying" email arrived (or asks you for its subject line) before marking the role Applied.

### `/interview-drill`: practice that targets your weak spots

1. **Setup:** your language, editor, how rusty you are, and any upcoming interviews.
2. **Diagnostic:** one problem in each core topic (arrays, two pointers, sliding window, stack, binary search, trees, heaps, intervals, graphs, dynamic programming), each run as a mock interview. Spread it over as many sessions as you like.
3. **Weakness bank:** after every problem it records specifically what went wrong, like *"found the DP recurrence, then the base row was off by one"* or *"never asks about empty input."*
4. **Targeted practice:** every new problem is generated for your weakest spot, at a difficulty that matches your level.
5. **Stats** at any time:

```
Category                       Done  Scored  Clean  Mastery         Level       Last
------------------------------------------------------------------------------------------
Arrays & hashing                  3       3      2  ████████░░  81  Proficient  2026-10-20
Sliding window                    2       2      0  ████░░░░░░  44  Developing  2026-10-22
Dynamic programming               1       1      0  ████░░░░░░  41  Developing  2026-10-24

Interview skills (average of last 8 scored attempts, out of 4; 3 = hire bar)
  clarifying      2.67  ← below hire bar
  verification    2.33  ← below hire bar

Focus next: Dynamic programming (developing, 41/100), Sliding window (developing, 44/100), Graphs (not tested yet)
Due for review now: p3 Cheapest Climb
```

| Command | What happens |
|---|---|
| `/interview-drill` | The next right thing: a due review, the next diagnostic problem, or a new problem on your weakest topic |
| `/interview-drill diagnose` | Continue the baseline diagnostic |
| `/interview-drill grind dp` | Back-to-back problems on one topic, each aimed at the gap the last one exposed |
| `/interview-drill mock graphs` | A timed mock interview on a topic |
| `/interview-drill oa` | Online-assessment simulation: 2 problems, 70 minutes, no hints |
| `/interview-drill guided dp` | Study session: Claude walks through it with you, with less help each problem |
| `/interview-drill blitz` | 5-minute time/space complexity quiz |
| `/interview-drill warmup` | Quick language-syntax warm-up |
| `/interview-drill review` | Re-do problems that are due (after 3, then 10, then 30 days) |
| `/interview-drill stats` | The progress report above |

**Where problems go:** `~/interview-practice/`. Each problem is a bare file like `p3_merge_intervals.py` with just the problem name and the function name. You write everything else, as in a real interview. Claude keeps a hidden test suite in `.tests/` (no peeking), reads your code first the way an interviewer would, then runs the tests:

```bash
python3 .tests/run.py p3            # full test suite
python3 .tests/run.py p3 --sample   # sample cases only, like an OA's "Run" button
python3 .tests/reset.py p3          # archive your attempt and start the problem fresh
```

Each mock is scored on six things (communication, clarifying questions, approach, complexity, code, verification), 1–4 each, with one habit to fix next time. Mastery is computed by a script, not estimated: it combines your scores, whether you solved the problem cleanly, and its difficulty, with recent attempts weighted most. The formula is at the top of `skills/interview-drill/scripts/stats.py`.

---

## You control what Claude can access

Out of the box the kit uses only **public company job boards** (Greenhouse, Ashby, Lever, Amazon and Google careers), which need no login. Anything that acts through **your** accounts starts off, and Claude asks the first time it would help:

| Permission | Used for | Until you allow it |
|---|---|---|
| Logged-in job sites (Handshake, Wellfound, LinkedIn…), per site | Postings that aren't on public boards | Public boards only |
| Reading your email | Confirming an application went through | You tell Claude the email's subject line |
| Filling application forms | Quick-apply mode | Claude gives you the list; you fill the forms |
| Editing your Google Doc resume | Tailoring in place | You get text to paste |

Claude **never** types your passwords, presses Submit, or messages anyone. Your choices are saved under **What Claude may access** in `~/.claude/job-search/profile.md`; change them any time.

**About LinkedIn:** its terms prohibit automated access, and accounts do get restricted. The kit recommends searching LinkedIn yourself and pasting links. It then checks each one on the company's own job board, which is more reliable anyway.

---

## Make it yours

You never need to edit the skill files. Everything personal lives in `~/.claude/job-search/`:

| File | What's in it |
|---|---|
| `profile.md` | Your background, target roles, strengths, companies, permissions, **Settings** and **House rules** |
| `tracker.md` | Your job tracker (one row per role) |
| `drill-progress.md` | Practice settings and your weakness bank |
| `drill-attempts.jsonl` | Every practice attempt (what `stats` reads) |

- **Settings** change the numbers: fit-score weights, the tailoring threshold, bullets per role. Mock length is in `drill-progress.md`.
- **House rules** override anything a skill says. Write them as plain instructions:
  ```
  - interview-drill: mocks are 30 minutes and I can run my code. Why: that's my target company's format.
  - jobsweep: skip anything in Seattle. Why: not relocating.
  ```
- **The skills learn from corrections.** Tell Claude "don't hint during my clarifying questions" or "that's deliberate, not a red flag," and it writes a House rule so it sticks next session.

Want to change how a skill works? Each one is plain Markdown in `skills/<name>/SKILL.md`. Edit it and run `bash install.sh` again.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `/jobsweep` etc. don't show up | Restart Claude Code after installing. Check that `~/.claude/skills/jobsweep/SKILL.md` exists |
| Installer says Python 3 is missing | macOS: run `xcode-select --install`. Linux: install `python3` with your package manager |
| Installer says it can't find `skills/` | Run it from inside the downloaded folder (`cd claude-job-hunt-skills` first) |
| Practice problems don't open in VS Code | In VS Code, open the Command Palette and run **Shell Command: Install 'code' command in PATH**. Until then the skill falls back to `open -a "Visual Studio Code"` |
| A company shows "not found" when finding job boards | It uses Workday or its own careers site. Claude checks those by hand or skips them |
| Want to start over | Delete `~/.claude/job-search/` and run `bash install.sh` again |

---

## Design choices

- **Scripts do the mechanical work, not the model.** `find_boards.py` finds each company's public job board, `list_jobs.py` lists matching roles across all of them, and `ats_probe.py` pulls status, location, posting date and qualifications straight from the boards' public APIs. They're free, fast, and don't hallucinate. A cheaper-model scout agent only handles postings the scripts can't read, and `scout_verify.py` checks that the scout quoted the posting word for word.
- **Score from the job description, never the title.**
- **Claude never presses Submit.** You make the legal statements on an application, so you submit it. A role is marked Applied only after the confirmation is seen.
- **No made-up numbers** on your resume.
- **The interviewer behaves like a real one:** short messages, straight answers to your clarifying questions, hints only if you ask (and they cost points), and the clock stops only when time runs out or you say you're done.
- **Practice numbers are computed, not guessed.** Test results are read from the runner, and the logger refuses inconsistent records (like calling a 6/10 run a clean solve).
- **Real results beat practice results.** A real OA or interview outcome outranks anything measured in practice.

---

## What's in this repo

```
install.sh                    installer (also --uninstall)
skills/
  jobsweep/                   /jobsweep
    SKILL.md
    scripts/                  find_boards.py · list_jobs.py · ats_probe.py · scout_verify.py
  tailor-apply/               /tailor-apply
    SKILL.md
    references/               resume formatting standards · Google Docs editing notes
  interview-drill/            /interview-drill
    SKILL.md
    scripts/                  run.py · reset.py · init_workspace.py · log_attempt.py · stats.py
    references/               rubric · curriculum · problem generation · DP/graph/complexity notes
agents/jd-scout.md            the scout agent /jobsweep uses to read postings
templates/                    starting profile, tracker and practice files
```

**Optional extras:** Claude in Chrome (for logged-in sites or Google Docs, if you allow them), a Notion or Google Sheets connector (if you'd rather keep the tracker there), a Gmail connector (to find confirmation emails), and `pdfinfo` from poppler (to check your resume PDF is one page).

---

## Disclaimer

This is an independent project, not affiliated with or endorsed by Anthropic or any company mentioned. You're responsible for your applications and for following each job site's terms of use. Fit scores and mastery levels are estimates to help you prioritize, not guarantees.

## License

[MIT](LICENSE)
