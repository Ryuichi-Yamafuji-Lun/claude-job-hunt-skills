# Scoring rubric

Six dimensions, 1–4 each. Report the per-dimension scores, the total /24, and **one** habit to fix.
Don't soften the numbers; an inflated log destroys the value of the whole system.

**1 = would fail the loop · 2 = below bar · 3 = hire bar · 4 = strong**

### 1. Communication under load
- 4 — continuous narration; the interviewer always knows what's being considered and why
- 3 — narrates at each phase change; brief silences, then a recap
- 2 — narrates the plan, then goes quiet while coding
- 1 — long silences; code appears with no explanation

*The single most common new-grad rejection reason.* In a chat harness, coding-phase silence is a tool limitation, not a habit: score phase changes only, and cap at 3.

### 2. Clarifying questions
- 4 — surfaces a genuine ambiguity that changes the solution
- 3 — asks about size, ranges, duplicates, empties before starting
- 2 — asks one token question
- 1 — starts solving immediately

### 3. Approach and problem-solving
- 4 — states a brute force with complexity, then reasons to the optimal by naming the bottleneck
- 3 — reaches optimal or near-optimal with ≤1 tier-2 hint
- 2 — needs a tier-3 hint, or lands on a working but suboptimal approach
- 1 — no viable approach without being told

### 4. Complexity analysis
- 4 — time *and* space, unprompted, before coding, correct on amortized/recursion-stack subtleties
- 3 — both, correct, when asked
- 2 — time only, or needs correction
- 1 — wrong or absent

### 5. Code quality
- 4 — compiles-in-head clean, meaningful names, no dead paths, sensible decomposition
- 3 — correct with a small slip caught on the dry run
- 2 — correct after debugging with help
- 1 — doesn't work

### 6. Verification
- 4 — traces a real example by hand, finds and fixes a bug before being told
- 3 — traces an example, names the edge cases
- 2 — says "let me check the edges" and lists them without tracing
- 1 — declares done (a skipped trace is a 1, however the trace is delivered)

---

## Outcome codes

- **CLEAN** — solved, no hints, optimal, on time
- **H1 / H2 / H3** — solved; deepest hint tier reached
- **SLOW** — solved but over the time budget
- **PARTIAL** — approach right, code incomplete
- **MISS** — didn't get there

**`→FIXED`** — solved off-clock after time was called. Write `PARTIAL (2/6 timed → 6/6 fixed)`. The timed number is the grade, because an interview ends at the buzzer, but the fixed number separates *"can't solve this"* from *"solved it but couldn't land it in time,"* which need opposite remedies. Never let it upgrade the outcome code.

**`(contaminated)`** — the interviewer leaked something. Tag the row, name the voided dimensions, score over the reduced denominator, and keep the problem in the queue for a clean run. This grades the harness, not the user.

---

## Spaced repetition

Anything but CLEAN goes into the review queue: re-do at **+3 days**, then **+10**, then **+30**. A re-do that isn't CLEAN resets the interval to +3. `→FIXED` counts as not CLEAN.
