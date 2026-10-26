---
name: tailor-apply
description: Tailor a resume to one specific job and get the application submitted — recruiter-style audit (match score, missing keywords, red flags), an XYZ-formula rewrite of the experience section, a final verification pass, then a clean hand-off to apply and a confirmed tracker update. Also has a quick-apply mode for batching lower-priority roles with a generic resume. Use when the user says "resume review", "tailor my resume for X", "final review", "let's apply to X", "quick apply", "batch apply", or picks a role from /jobsweep.
---

# Tailor + Apply

Two modes:
- **Tailored** (default): one job, one tailored resume, one confirmed application. Three review stages, then apply.
- **Quick apply** (`/tailor-apply quick`): ~10 lower-priority roles in about an hour with the generic resume, no tailoring. See the bottom of this file.

## Who you're talking to

Assume a new user who doesn't know this skill's vocabulary. Explain each stage in one plain sentence the first time ("First I'll read your resume the way a recruiter at Stripe would and tell you what they'd notice"). Never ask the user to edit a config file; ask and write the answer in yourself.

## Permissions

Check **What Claude may access** in the profile before any of these. `not asked yet` means off: ask once, in one line, at the moment it would help ("Want me to check your Gmail for the confirmation email? I'd only search for it, nothing else."), and write `yes` or `no` into the profile either way. `no` means don't ask again:
- **Reading email** (Step 5). If not allowed, or there's no email connector, ask the user to check their inbox and tell you the subject line of the email they got.
- **Filling forms** (quick-apply mode). If not allowed, hand over the queue and let the user fill the forms.
- **Editing a Google Doc through the browser.** If not allowed, give the tailored text and let the user paste it.
- **Opening a logged-in site** (an ATS account, LinkedIn Easy Apply). Opening a tab the user asked for is fine. Never type passwords, and never press Submit.

## Step 0 — Load context

1. Read `~/.claude/job-search/profile.md`: lanes, resumes, application email, retired lines, tracker, and **House rules** (they override this file). If the file doesn't exist, create it from `~/.claude/job-search/templates/profile.md`.
2. **First run** (`Resume setup done: no`): ask in **one message**: the resume (*"a file path, a Google Docs link, or paste the text"*), plus anything the profile is missing out of graduation/start date, years of professional experience, whether they need visa sponsorship, and the email they apply with. Skip anything `/jobsweep` already recorded. Save the answers and the resume's location to the profile, then set `Resume setup done: yes`.
   **Using the resume:** if the profile lists one, use it. A local file (PDF, .docx, .md, .txt) can be read directly. A Google Docs link needs the browser (Claude in Chrome); if that isn't available, ask the user to export it as PDF or paste the text. If the user has resumes aimed at different kinds of roles, ask which is which and record them as lane bases.
3. **You need the company name and the full JD.** If either is missing, ask. Don't tailor against a title. Get the JD in this order:
   - The role came from `/jobsweep`: reuse the verbatim qualification block from that sweep.
   - The user pasted the JD text: use it as given.
   - The user gave a link: for Greenhouse, Ashby, Lever, Amazon or Google links, run `python3 ~/.claude/skills/jobsweep/scripts/ats_probe.py "<link>"`, which returns the requirements and whether the posting is still live. For other public pages, fetch the page. For LinkedIn, Handshake, Indeed or anything behind a login, don't fetch it: ask the user to paste the JD text, or read it in their browser only if "What Claude may access" allows that site.
   - A link that's dead or shows no requirements: say so and ask for the text. Never tailor against a guessed JD.
4. **Check hard requirements before tailoring.** Compare the JD's minimum requirements with the profile: graduation date, start date, years of experience, degree, sponsorship, location. If one is a clear fail (e.g. "degree by summer 2026" for a May 2027 grad), say so plainly before Stage 1 and let the user decide whether to continue. Tailoring can't fix a hard gate.
5. **Check the tracker first.** Make sure the user hasn't already applied, the company has no cap that's been used up, and the pipeline isn't closed. The tracker records what happened; the profile only records what was planned.
6. **Start from the right resume.** Use the most recent lane base, or the nearest already-corrected cut from the same lane. Never use an older copy that predates a correction. File modification time is download time, not authoring time, so check the content. Work on a **copy** named per the profile's naming convention (default `First_Last_Resume_<Company>`); never edit the base.

**Where the tailored resume goes:** for a Google Doc, a copy of the doc in the same folder. For a local .docx/.md, a new file next to the original. For a PDF-only resume, write the tailored text to a `.md` file and tell the user to paste it into their own template. Don't try to edit a PDF in place. Always tell the user the path of what you created.

The persona for Stages 1 and 3 is **a senior recruiter at that exact company**, not a generic reviewer.

## Stage 1 — Recruiter audit (on "resume review")

Run this prompt, filled in:

> Act as a senior recruiter for this exact [company name]. Analyze my resume against this job description and give me a match score out of 100, the top 5 missing keywords, and the 3 red flags a hiring manager would spot in under 10 seconds.

Output **exactly three sections** and nothing else:
1. **Match score** /100
2. **Top 5 missing keywords** (from the JD, absent or buried in the resume)
3. **3 red flags** (what a hiring manager notices in 10 seconds: YOE mismatch, a missing required skill, vague bullets with no numbers, title/lane mismatch, formatting that breaks ATS parsing, gaps)

Don't flag things the profile lists as deliberate choices. Then offer Stage 2.

## Stage 2 — XYZ rewrite

> Rewrite my experience section to naturally include those keywords and remove the red flags. Use the Google XYZ formula: Accomplish X as measured by Y by doing Z.

Rules:
- **Experience section only.** Keywords that don't fit a bullet naturally go on the skills line.
- **No keyword stuffing.** Every keyword must read as something the user actually did.
- **Every bullet is XYZ with a real metric for Y.** Never invent numbers. If a bullet has no real metric, ask the user for one or drop the Y rather than make one up.
- **Never introduce a claim the user hasn't confirmed** (technologies, scope, titles, employment status). Never reintroduce the profile's retired lines.

**Bullet rules (sources in `references/formatting-standards.md`):**
- 🔴 **3–4 bullets per role is a hard cap.** New content *replaces* a bullet; it's never appended. Count before sending; overruns creep back in exactly this way.
- **One bullet = one rendered line** (~110–115 chars, 16–18 words) where possible without losing quality. Quality wins ties: keep a second line for a real metric, mechanism, or Z. Recruiters read roughly the first 8 words, so front-load the verb and the number and cut trailing qualifiers.
- 🔴 **Re-verify XYZ after every length pass.** Shortening silently drops the Z.
- Never end a bullet on a dangling fragment; shorten somewhere else.
- No pronouns ("I", "my"). Start with an action verb, never a date.
- **One page.** Budget in wrapped *lines*, not bullets (a full page is ~64–65 lines at 11pt). Adding a skill to a full skills line means removing one. Recount after every change.

## Stage 3 — Final verification (on "final review")

> Act as a senior recruiter for this exact [company name]. Review the rewritten resume against the job description: give me an updated match score out of 100, confirm each of the top 5 keywords now appears naturally, verify every experience bullet follows the Google XYZ formula (Accomplish X as measured by Y by doing Z), and confirm the 3 red flags are gone — flag any that remain or any new ones introduced.

This is **verification, not a rewrite.** Report: new score, a keyword checklist, a per-bullet XYZ check, a red-flag checklist, and any newly introduced problems. Also check: ≤ 4 bullets per role, one page, no retired lines, contact info correct.

Then get it to a PDF and **check the page count mechanically** (`pdfinfo file.pdf | grep Pages`), not by eye:
- **Google Doc**: export via `.../export?format=pdf`.
- **Word (.docx)**: `soffice --headless --convert-to pdf file.docx` if LibreOffice is installed; otherwise ask the user to Save as PDF.
- **Markdown / plain text / PDF-only**: the user pastes the tailored text into their own resume template and exports. Tell them exactly which bullets changed so the paste takes a minute.
If `pdfinfo` isn't available, ask the user to confirm it's one page.

## Step 4 — Apply

**Default split: the user fills the form; you don't.** On a tailored application the user knows the answers, and going back and forth field by field costs more than it saves. Hand off in one line: "PDF is at <path>, form is open in tab <n>". Then stop. Add at most one more line for **honesty traps** on the form (e.g. "can you start within 2 months?" when the true answer is no) and which email to use (the profile's application email, so confirmations land where you can find them). Don't ask about pronouns, preferred name, or consent boxes.

Rules for every application:
- **Log in to the ATS first** and navigate from inside the account. Never use a public/guest form, even from a referrer's link; guest submissions can vanish with no record.
- 🔴 **Never navigate a tab the user may be using.** Do lookups mid-application in a NEW tab. Navigating away from a half-filled form loses it.
- 🔴 **You never press Submit. The user does.** These are legal employment applications carrying the user's identity and work-authorization answers. The user attests to them; an agent can't. The tracker records what the user has *done*, and an unconfirmed "Applied" row is how false positives happen.
- Recruiter email questionnaires count as forms. Give the user a wrapper email, flag any trap questions, and let them answer.

## Step 5 — Confirm, then log

After the user says "submitted":

1. **Find the confirmation email** (if email access is allowed; otherwise ask the user for the subject line). Search **both** the application email and the resume contact email; the ATS often uses the address on the resume. Never conclude "nothing arrived" from one inbox.
2. 🔴 **Read the subject; a company email isn't a confirmation.** "Received" / "Thank you for applying" = ✅. "Incomplete" / "Action required" / "Finish your application" = ❌, so tell the user to finish it.
3. Only then update the tracker row, **creating it first if the role isn't in the tracker** (e.g. the user brought the job directly instead of from `/jobsweep`): status → Applied, date applied, the exact email used, follow-up date (+14 days is a reasonable default). **Record what you saw, not what you assume.**
4. If there's no confirmation, the evidence order is: the platform's own record (its "My applications" page) > confirmation email > memory. Duplicate ATS accounts are the usual reason an application seems to have disappeared.

Never mark a role Applied because you prepared it. "I did the first six" means six.

Last, one line: *did the user correct anything this session?* If so, write it into the profile's House rules as an imperative rule now, with the wording that caused it.

## Quick-apply mode

For volume on lower-priority roles: ~10 in about an hour, generic resume, no tailoring.

**Tier rule (customizable in House rules):**

| Tier | What qualifies | How |
|---|---|---|
| **Tailor** | Fit ≥ 78, any name-brand company, a well-funded early-stage startup with a small eng team, or a required essay | **Never in a batch.** Tailored mode above |
| **Batch** | Fit < 78, unscored, or practice tier | Generic resume, ~5 min each |

When a batch candidate turns out to be big-name or 78+, **pull it out and say so.** Nine is fine.

**Step 1: build the queue.** Pull the batch tier from the tracker, verify each is still live (`/jobsweep`'s `ats_probe.py`), and order them shortest form first: Ashby and Greenhouse first, Workday last. Hand the user a numbered list of direct apply URLs. Nothing else.

**Step 2: fill (only if "Fill application forms" is allowed in the profile, or the user asks now).** You may fill fields and attach the generic resume. The user still presses Submit. Know these quirks:
- **Autofill is hostile.** It has re-split a US phone number into a foreign format under a +1 code and filled in the wrong city. **Check phone and city on every form.** Resume-parse autofill (Ashby, for example) can overwrite name and email with the resume header; re-set them after upload. A correct stored ATS profile (e.g. MyGreenhouse) fixes this once instead of per form, but verify it.
- **Leave sensitive uploads to the user** (transcripts, IDs).
- **Greenhouse forms embedded in an iframe** on a company's own site may be invisible to page-reading tools. Hand those to the user.
- Some ATS buttons only respond to a coordinate click, not an element-ref click.
- **If the permission system blocks form filling, say so once and move on.** Hand the user the queue. Don't re-test per company, and never edit your own permission settings; the user can change them with `/permissions` if they want.
- Anything with a required free-text essay doesn't belong in a batch. Move it to tailored.

**Step 3: the two checks to give the user, and nothing more.** A long checklist defeats the purpose of the mode:
- Phone and city, every time. It's the known silent defect.
- Screenshot or keep the confirmation. No confirmation screen may mean no application.

**Step 4: log.** Same as Step 5 above, for exactly the rows the user confirms.

## Editing in Google Docs (optional)

If the resume's system of record is Google Docs and you edit it through the browser, read `references/google-docs-editing.md` first. The Docs editor is a canvas, and blind typing has replaced whole documents.
