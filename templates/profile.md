# Job search profile

<!--
You don't have to fill this in by hand. The first time you run /jobsweep or /tailor-apply,
Claude asks you the few questions it needs and fills in this file for you.
You can edit it any time; the skills read it at the start of every run.
Leave anything blank that doesn't apply. Keep it short (under ~6 KB), since it's loaded every run.
-->

## Who I am
- Name:
- Graduation / availability date:            # e.g. "B.S. CS, Month Year; can start Month Year"
- Latest acceptable start date:              # roles starting later than this lose start-date points
- Professional experience (months, full-time equivalent):   # internships count; school lab roles usually don't
- Work authorization:                        # e.g. "US citizen", "Permanent Resident", "Needs H-1B sponsorship"
- Application email:                         # the address every ATS account uses
- Resume contact email (if different):       # recruiters reply here, so check both inboxes

## Setup
- Job search setup done: no                  # /jobsweep sets this to yes after its first-run questions
- Resume setup done: no                      # /tailor-apply sets this to yes once it knows your resume and basics

## What Claude may access
<!--
You decide. Everything here is OFF until you turn it on, and you can turn it off any time.
Public company job boards (Greenhouse, Ashby, Lever, Amazon, Google careers) need no login and are always used.
Claude never types your passwords, never applies or messages anyone, and never changes your profiles on these sites.
If a skill wants something that isn't allowed here, it asks you first.
-->
<!-- "not asked yet" means off. Claude asks the first time it would help, then writes yes or no here. -->
- Logged-in job sites Claude may read for you: not asked yet   # e.g. "Handshake, Wellfound". You stay logged in yourself
- Read my email to confirm applications: not asked yet         # yes = search your inbox for "thank you for applying" (Gmail connector)
- Fill application forms in quick-apply mode: not asked yet    # you always press Submit yourself
- Edit my resume in Google Docs through the browser: not asked yet

## What I'm looking for
- Role type: full-time only | internships OK
- Target titles:                             # e.g. "Software Engineer I, New Grad SWE, Backend Engineer I"
- Regions:                                   # e.g. "SF Bay Area, Seattle, NYC, LA, Remote-US"
- Minimum comp (optional):

## My lanes (domain match, ~40 pts of the score)
<!-- List 2-4 lanes you are strong in. Each lane gets its own base resume (see "Resumes" below). -->
- Lane A:                                    # e.g. "backend / data pipelines"
- Lane B:                                    # e.g. "AI agent infrastructure / developer tooling"
- Weak areas (cap fit near ~68 regardless of resume):   # e.g. "GPU kernels, CUDA, distributed training"

## Hard rules
- Avoid-language gate (optional):            # e.g. "no roles where C/C++ is a HARD-GATE requirement"
- Companies I will not apply to:
- Closed pipelines (rejected; wait until):   # e.g. "Acme: rejected Month Year, retry after Month Year"

## Per-company application caps
<!-- Some companies limit applications. Record them so the sweep never burns a slot by accident. -->
- # e.g. "Google: 3 per rolling 30 days, 90-day wait to re-apply to the same req"

## Tracker
- Type: markdown                             # markdown (no setup) | notion | sheet
- Location: ~/.claude/job-search/tracker.md  # or your Notion database / Google Sheet link
- Write threshold: 75                        # only write rows scoring >= this
- Status values:                             # only needed for Notion/Sheets: the exact options your tracker accepts

## Resumes
- Where they live:                           # e.g. "~/Documents/resumes/" or a Google Drive folder link
- Generic resume (for untailored apps):      # a file path (PDF, .docx, .md) or a Google Docs link
- Lane A base:
- Lane B base:
- Naming convention:                         # e.g. "First_Last_Software_Engineer_<Company>"
- Retired lines (never reintroduce):         # wording you've corrected and don't want to ship again

## Discovery sources
- School / private boards (check first):     # e.g. "Handshake". Also add it to "Logged-in job sites" above
- Companies I'm interested in:               # plain names, e.g. "Stripe, Notion, Datadog"
- Public boards to check:                    # filled in by /jobsweep, e.g. "greenhouse:stripe, ashby:notion"
- Known-good search queries:

## Settings (change any of these; the skills use the defaults if left blank)
- Fit score weights:                         # default: domain 40 / eligibility 25 / start date 20 / comp 15
- Tailor threshold:                          # default 78: at or above this, always tailor
- Max bullets per role:                      # default 4
- Deliberate resume choices (don't flag):    # e.g. "no GPA listed on purpose", "no summary section"

## House rules
<!--
Your own rules. They OVERRIDE anything in the skill files, so you never have to edit a SKILL.md
(and updating the package never overwrites them). The skills also add rules here when you correct them.
Write each rule as an instruction, with the reason:
- jobsweep: never recommend roles in <city>. Why: not relocating.
- tailor-apply: always fill forms for me in quick mode, I'll click submit. Why: saves time.
- interview-drill: mocks are 30 minutes, and I'm allowed to run the code. Why: matching my target company's format.
-->

## Live state (rewrite in place each sweep)
- Last sweep:
- Open items:
