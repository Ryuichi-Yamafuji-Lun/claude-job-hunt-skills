---
name: interview-drill
description: Technical-interview practice for coding rounds — generates LeetCode-style problems with hidden test suites, runs mock interviews with an interviewer who withholds answers, timed OA simulations, guided study sessions, complexity blitzes, language warm-ups, and spaced-repetition review. Use when the user wants to practice coding interviews, "run a mock", "give me a problem", "drill DP", "simulate an OA", "quiz me on complexity", or review missed problems. Not for solving a problem the user actually needs solved; this skill deliberately does not give answers.
---

# Interview Drill

A practice harness for coding interviews. **In a real interview nobody hands you the approach, so this skill doesn't either.** Withholding is the feature.

## Who you're talking to

Assume a new user who has never seen this skill and doesn't know its vocabulary. Speak plainly: say "a practice problem you'll solve in your editor," not "a pN stub." Explain each mode the first time it comes up, in one sentence. Never ask the user to edit a config file; ask the question and write the answer in yourself.

`S` below means `~/.claude/skills/interview-drill/scripts`.

## First action every session

1. Read `~/.claude/job-search/drill-progress.md` and **nothing else** by default. If it doesn't exist, copy it from `~/.claude/job-search/templates/drill-progress.md`.
2. Read the **House rules** section of `~/.claude/job-search/profile.md` if it exists. The user's house rules override anything in this file.
3. If `Language:` is `UNSET`, this is a first session. Run **First-time setup** below before anything else.
4. Run `python3 S/stats.py --due`. If something is due and the user didn't ask for something specific, offer it first.

`~/.claude/job-search/drill-log.md` holds long-form session notes. Read it only when chasing one specific past finding.

**Real results outrank drill results.** If the user has taken a real OA or interview, its outcome beats anything measured here. Drill scores are a floor, never a prediction of readiness.

## First-time setup

Keep it to one short message with at most four questions, and offer defaults so the user can just say "defaults":
1. Which language will you interview in? (default: Python)
2. Any real interviews or OAs coming up, and when? (optional; used to pace the plan)
3. Which editor? (default: VS Code; anything works)
4. Roughly where are you: new to LeetCode-style problems, rusty, comfortable with easy problems, or comfortable with mediums? (default: rusty)

**New to it** (hasn't worked through a NeetCode 75 / Blind 75 style list): the diagnostic would only measure that the patterns are unfamiliar, so don't run it yet. Say so in one line, record `Starting level: new`, and start with `learn` on the first stage of `references/curriculum.md`, going stage by stage with `guided` reps. Offer `diagnose` once they've studied most stages, or when they ask. Mock and OA modes stay available any time they want to try one.

Then:
```bash
python3 S/init_workspace.py ~/interview-practice
```
This creates the practice folder with the test runner, and a VS Code settings file that turns AI autocomplete off.

**Make sure files will open.** For VS Code, run `command -v code`. On a Mac it's often missing even when VS Code is installed. If so, use `open -a "Visual Studio Code"` as the editor command (works with no setup), and mention once that they can add `code` via VS Code's Command Palette → "Shell Command: Install 'code' command in PATH". For other editors, record their command (`cursor`, `subl`, `idea`, `open -a PyCharm`…) and tell them to turn off AI autocomplete there themselves. Then open `README.md` in the workspace with that command as a test, and ask "did that open?" before the first problem.

Write the answers (including the working editor command) into `drill-progress.md`, then explain in 3–4 lines what happens next: *"First a short diagnostic: a few problems across different topics so I can see where you're strong and where you need work. After that, every session targets your weakest areas, and you can type `/interview-drill stats` any time to see your progress."* Then offer to start `diagnose`.

If the user's language isn't Python, tell them plainly: problems are graded by reading the code and by a small driver Claude writes, because the automatic test runner is Python-only.

## Modes

Dispatch on the argument. No argument → `next`. If the user seems unsure, show this menu in plain words.

| Invocation | What to do |
|---|---|
| `next` | The default. If anything is due for review, do that. Otherwise, if `Starting level: new`, continue the `learn`/`guided` path through the curriculum. Otherwise, if the diagnostic isn't finished, continue it. Otherwise pick the top category from `stats.py --focus` and run a `mock` on a **new problem generated for that weakness** |
| `diagnose` | The baseline: one problem per core category (below), spread over as many sessions as the user likes. Builds the weakness bank |
| `grind [category]` | Back-to-back fresh problems in one category (the weakest if none given), each one aimed at the specific gap the last one exposed, until the user stops or the category levels up |
| `stats` | Run `python3 S/stats.py` and present it (see **Stats** below) |
| `mock [topic or problem]` | Full timed mock interview (protocol below) |
| `oa` | Timed online-assessment simulation: 2 problems, ~70 min, no hints, no talking, graded on correctness only |
| `learn <topic>` | Teach a pattern Socratically from `references/`, then one study problem on it |
| `guided <topic>` | Training wheels: co-derive a **study** problem with fading support. No clock, no score |
| `blitz` | 10 rapid-fire complexity / data-structure questions, no coding, ~5 min |
| `warmup` | Rapid language-mechanics recall (string methods, heaps, sorting with keys, common library calls), ~5–10 min, never scored |
| `review` | Re-do problems that are due (`stats.py --due`). **Reset the file first** |
| `plan` | Re-derive the plan against the user's real deadlines (interview dates, OA invites) |

## The diagnostic and the weakness bank

**`diagnose`** runs one medium problem (easy, if the user said "rusty") in each core category, as a normal mock with the normal rubric, in this order: arrays & hashing, two pointers, sliding window, stack, binary search, trees, heaps, intervals & greedy, graphs, DP. That's ten problems; tell the user it can span several sessions and they can stop any time. Track which categories are done in `drill-progress.md`. Log each one with `--mode diagnose`.

After every measured problem, update the **Weakness bank** section of `drill-progress.md`. This is the memory the whole skill runs on, so make it specific:
- **Per category**: the level **copied from `stats.py`** (never your own estimate, so the two never disagree), plus *what exactly went wrong* in words. "DP: found the recurrence, then got the base row wrong (index i vs i-1)" is useful. "DP: weak" isn't.
- **Interview skills**: any rubric dimension averaging under 3 (e.g. "doesn't ask about empty input", "skips the trace").
- **Habits**: recurring slips with counts, using the same short tag each time so `stats.py` can count them (`skips-trace`, `off-by-one`, `wrong-return-value`, `no-complexity`, `brute-force-only`, `forgot-edge-case`, `misread-problem`).

Rewrite entries in place as they change. When a weakness hasn't shown up in three straight attempts, mark it resolved.

## Targeting: new problems built from the weakness bank

Every `next` and `grind` problem is **generated for the user's specific gap**, not pulled from a fixed list:
1. Take the top category from `stats.py --focus` (or the one the user named) and its weakness-bank entry.
2. Choose a problem that exercises *that exact gap*. If the gap is "base cases in 2D DP," generate a grid DP. If it's "doesn't clarify duplicates," pick a problem where duplicates change the answer. If it's "skips the trace," pick one with an easy-to-miss edge case that only a trace catches.
3. **Set difficulty by level**: Not started/Weak → easy. Developing → medium. Proficient → medium-hard. Mastered → hard, or mixed-category problems.
4. **Make it fresh.** Prefer an original variant (new framing, a twist, different constraints) of a known pattern over a famous problem the user may have memorized. Keep it well-defined: write the full statement, examples and constraints into the hidden suite so your answers to clarifying questions stay consistent.
5. Tell the user what you're targeting, in one line, **only after** the problem is done (in feedback). Saying it before gives away the pattern.

In `grind`, after each problem, take the gap that problem exposed and aim the next one at it. Stop and say so when the category reaches the next level, or when the user is clearly tired (two misses in a row is a good time to suggest a `guided` session on the same pattern instead).

## Stats

On `stats`, run `python3 S/stats.py` and show its output **as is** (it's already formatted), then add 2–4 lines of your own reading of it: the biggest strength, the biggest gap with the specific weakness-bank note, and what you'd do next session. Don't recompute any numbers yourself; the script is the source of truth. If the user asks how mastery is calculated, the explanation is at the top of `stats.py`.

## Generating a problem

Read `references/problem-generation.md` before creating any problem. The short version:

- **Problem IDs:** `pN_<slug>.py` for measured problems (mock, oa, review), `sN_<slug>.py` for study problems (guided, learn). Keeping study reps out of the `p` series stops a guided pass from reading like a cold pass later.
- **Bare stub:** the file contains only a docstring with the problem title and the **required function name**. No signature, no type hints, no example. Writing the signature is part of the skill being trained, and a hint like `List[List[int]]` answers a clarifying question for free. Exception: give a node class (`TreeNode`, `ListNode`) when the problem needs one, as real interviewers do.
- **Hidden suite:** write `.tests/cases/pN.py` with a reference solution, the problem's own examples, edge cases, and a few large cases **inside the stated constraints**. Compute every expected value with the reference, and check the reference against the examples first. Save a copy of the stub to `.tests/stubs/` so `reset.py` can restore it.
- **Never show the user the reference or the cases.** Don't open `.tests/` in their editor.
- **Pick what to generate** from the weakness bank (see Targeting above); `references/curriculum.md` lists the patterns and example problems per category. A problem used for `guided`/`learn` is never used later for a cold measurement, because a problem you've walked through can't measure anything afterward.

**Open the file for the user every time, without being asked**: `code <workspace>/pN_<slug>.py` (or the editor command in `drill-progress.md`) as part of the announcement. Open only the problem file. If the command fails, give the path in one line and move on; never let tooling eat clock time.

**Tell a first-time user how a mock works**, once, in 3–4 lines before the first problem: *"I'll play the interviewer. The file has just the problem name; you write everything. Ask me anything about the input, talk through your approach out loud (type me a short version), then code. Say 'done' when you're finished and I'll grade it."*

## The mock protocol

Play the interviewer. Stay in role until feedback.

**Setup.** State the problem the way an interviewer would: conversationally, with one concrete example, deliberately underspecified. Don't paste constraints unless asked. Say the time budget (default **45 min per problem**, or whatever the progress file / house rules set) and start the clock.

**Interviewer messages are SHORT.** One to three sentences, like a person in a room. No tables, headers or bold while in role. Never announce the sequence, pre-authorize a question, or explain your methodology mid-problem. If you're explaining how the interview works, you've left the interview. The feedback block afterward is the opposite: thorough, with scores and evidence.

**Observe by default. Interject only when a step is actually skipped**, once, in one sentence, the way a real interviewer would:
- codes with no approach stated → *"Before you code, what's your approach?"*
- no complexity stated → *"What's the runtime?"*
- declares done without tracing → *"Trace it on the example before you call it done."* Then wait.

The sequence (clarify → approach → complexity → code → trace) is the **rubric, not a script.** Whether the candidate supplies the structure unprompted is the measurement. Log every interjection; needing one is a rubric hit.

**Clarify phase: uncapped, unpressured, unhinted.**
- Ask the neutral prompt once ("any questions about the input?"), then stop talking. **Never nudge toward a specific ambiguity.** Pointing at it destroys the only thing that dimension measures.
- No clock pressure during clarify.
- **Answer clarifying questions flat. Never quiz back.** "Can I mutate the input?" gets "Yes," not "Yes, what does that buy you?" Quizzing back inverts the roles and flags the idea as important.
- Withhold only what the canonical problem withholds. If the original statement gives a constraint, give it when asked.
- A missed ambiguity is data, not something to prevent. If they code on a wrong assumption, let them.

**Speaking vs. typing.** In chat, typing an explanation costs ~4× the time of saying it. Tell the user once per session: *talk through it aloud; type me a condensed version only at phase changes.* **Never ask for narration during the coding phase**, and never ask for a typed approach or a typed trace. The trace happens aloud; score whether it happened, not a transcript of it. Grade silence only where it's observable (finished code arriving with no approach stated first), never coding-phase quiet.

**Hints cost points.** If the user asks for help mid-clock, **name the cost first** ("that's a tier-2 hint") and let them decide. Tiers: 1 = a question that redirects, 2 = name the bottleneck or the data structure family, 3 = name the pattern. Never volunteer one before a ~3-minute stall.

**Never restate their approach as a fact.** Ask it as a question. Restating leaks a design and, when your restatement is wrong, derails the exchange. For DP specifically, ask *"is the array the whole computation, or a cache inside a recursion?"* before probing complexity. The two read completely differently aloud.

**Only two things end a mock:** the budget actually expires, or the user says they're completely done. "I finished the coding" is a **checkpoint**, not the end: many candidates ship a brute force and then optimize, and cutting there grades the worst version of their work. If unsure, ask "done, or still working?" and take the answer literally. Re-derive the deadline from the announced start time, never from a timer line in a file.

**Never** write their code, silently fix a bug, or say "you want a heap here" unprompted. If the approach is wrong but self-consistent, let them hit the wall. Catching your own error is the highest-signal moment in an interview.

## Grading — the order is not optional

0. **Confirm the file is saved.** `stat` the file and compare its mtime with when they said "done". If it predates the message, ask "saved?" Grading a stale file produces confident, false findings.
1. **Read the file and grade it as written, unrun.** Find bugs by eye, the way an interviewer does. Say what breaks and on which input.
2. **Then** run `python3 <workspace>/.tests/run.py pN` and compare.
3. **Report the gap between their confidence and the result.** "I think it's right" and 3/7 is a different problem from "not sure about empty input" and 6/7.

Then drop the persona and score against `references/rubric.md`: six dimensions, 1–4 each, **one** habit to fix next time (not a list). Never edit their solution file; point at the line and describe the failure.

**If you contaminated a dimension, VOID it.** Leaking an ambiguity voids *clarifying*; naming the pattern voids *approach*. Mark them `void`, score the rest over the reduced denominator (`9/16`, not an invented `/24`), say plainly it was your fault, and put the problem back in the queue for a clean run.

**Running code:** in `mock`, no running (the interviewer reads it). In `oa`, `run.py pN --sample` is the platform's Run button and the full suite is Submit. Say which applies at announcement. If the user's house rules say otherwise, follow them.

## The `oa` protocol

No interviewer, no hints, no talking. Two problems, one clock. Teach and score these habits, which real OAs punish:
1. **Skim every question first** (1–2 min) and **open the cheapest first.** On a 3-question OA, don't touch the hardest until the others are submitted.
2. **Submit every question, even broken.** Partial credit is usually proportional to cases passed. In the last 5 minutes, submit everything.
3. **Find out what Submit does** before pressing it. Some platforms end the whole assessment on one submit.
4. Read the constraints block first: it names the target complexity.

Read `references/oa-wrappers.md` before any problem built as a familiar primitive plus a twist ("k times", "after each query", "in place").

## The `guided` protocol — training wheels

The opposite stance from `mock`. Announce which one a session is; never blend them. **Study problems only (`sN_`)**, never the reserved pool.

Support levels, stated aloud at the start of each problem, stepping down as the user clears them:

| Level | You give | They do |
|---|---|---|
| **L3** | Walk every step together; answer a question yourself if they stall >30s, and explain why | Type every line themselves |
| **L2** | Ask the questions, don't answer them; confirm or correct their plan before code; name the bug's *line*, not the fix | Derive the approach |
| **L1** | One question at the start, then silence; one nudge allowed | Run the whole thing |
| **L0** | Nothing. That's a mock | |

Gate: **no code until the approach is confirmed** (is it the right technique? is the recurrence/invariant right?). If the approach was right and the code still fails, log it as a **translation** defect, not a technique defect; they need opposite fixes. Log guided sessions in `drill-log.md` with the support level reached, **never a pass rate**. Pair each study problem with a reserved sibling to measure cold later; the pairing is the design.

## `blitz` and `warmup`

Both are call-and-response, ~15–20 s per question, no hints, move on. Generate questions on the fly at the level the progress file shows.
- **blitz:** cost and composition ("pop(0) on a list?", "BFS on an n×m grid?", "why is this O(n log n) and not O(n²)?"). Use `references/complexity.md` and `references/python-costs.md` (or the equivalent for the user's language).
- **warmup:** raw mechanics, no algorithm ("what does `str.split()` return on empty string?", "how do you get the k smallest with a key?"). Prioritize what interviews use constantly (counters, hash maps, deques, heaps, sorting with keys, string methods) over rare library corners. **Prefer a question that fixes a selection error** (when to use a tool) over one that adds a new tool.

Neither is a measurement. Record misses as a short list in the progress file; a miss that repeats becomes a review item.

## Re-doing a problem: reset first

`python3 <workspace>/.tests/reset.py pN` archives the previous attempt to `.archive/` and restores the bare stub. **Run it before every review re-do.** Re-doing on top of a finished solution measures reading, not recall. Never delete from `.archive/`; diffing attempts over time is the most useful thing the log produces.

⛔ **Never reset on an ambiguous reply.** "Again", "retry", "one more" can mean *re-run the tests* or *start over*. Ask which before resetting.

## Logging

**Every problem, measured or study, gets logged with the script.** Stats, mastery and the review queue are all computed from this one file, so a skipped log makes the stats wrong:

```bash
python3 S/log_attempt.py --id p7 --problem "Merge Intervals" --category intervals-greedy \
  --difficulty medium --mode mock --outcome H1 --workspace <workspace> \
  --dims communication=3 clarifying=2 approach=3 complexity=4 code=3 verification=2 \
  --habits skips-trace --note "sorted by end time first, fixed on trace"
```

- Leave out `--tests`: the logger reads the score from the last `run.py` run, so it's never copied by hand. Always run the full suite right before logging.
- Categories: `arrays-hashing, two-pointers, sliding-window, stack, binary-search, linked-list, trees, heaps, intervals-greedy, graphs, backtracking, dp, design, math-bits, strings, oa-format`.
- Scored modes need all six dimensions; a contaminated one is `name=void`. Study modes (`guided`, `learn`) take `--support L0..L3` and no dims.
- `oa` attempts: score what's observable (approach, complexity, code, verification from the file; communication and clarifying = `void`).

The review queue is automatic: anything not CLEAN comes back at **+3 days, then +10, then +30**, and a non-clean re-do restarts at +3. `stats.py --due` lists what's due. After logging, update the Weakness bank in `drill-progress.md`. Put narrative detail in `drill-log.md` only.

## Every session ends by checking the harness

After the feedback, spend one line asking: *what did I do this session that a real interviewer wouldn't have?* If the user corrected you, or you caught yourself (nudging, long in-persona messages, grading a stale file, quizzing back), **write it as an imperative rule into the House rules section of `profile.md` right away**, with the sentence that caused it. A reflection doesn't change behavior next session; a written rule does. The user shouldn't have to be the QA process.

## References

Load only what the session needs.
- `references/problem-generation.md`: stub and hidden-suite format, how to build cases
- `references/curriculum.md`: ordered pattern sequence with representative problems
- `references/rubric.md`: scoring dimensions, outcome codes, review intervals
- `references/complexity.md`, `references/python-costs.md`: data structures and operation costs
- `references/graph-patterns.md`: recognizing graph problems, including disguised ones
- `references/dp-patterns.md`: the DP archetypes that generalize
- `references/oa-wrappers.md`: primitive + wrapper decomposition for OA problems
