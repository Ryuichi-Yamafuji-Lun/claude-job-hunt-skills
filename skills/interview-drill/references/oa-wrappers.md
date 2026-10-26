# OA wrappers — a twist bolted onto a primitive you already know

**The diagnosis.** Many OA mediums need no algorithm the candidate lacks. They're a familiar primitive (rotate a grid, count pairs) plus one or two wrappers ("keep the diagonals fixed", "do it k times", "report after every query"). Candidates who read each wrapper as a brand-new problem design from scratch and lose the clock. A named wrapper costs 30 seconds; an unnamed one costs 20 minutes.

**How to use this file, by mode:**
- **Mock / OA (measured): observe only, never prompt.** Note whether the user's first sentence after clarifying separates the primitive from the wrapper. Asking the question hands them the answer.
- **Guided / warmup / review: ask outright.** *"What's the primitive, and what's bolted onto it?"* One-sentence answer before any code.
- **Debrief, any mode:** walk the table below against the problem just done.

## The wrapper table

| The wrapper, as the statement phrases it | What it actually changes | The move |
|---|---|---|
| **"…k times"**, with k up to 1e9 | Only how many times | The operation permutes a fixed set of slots, so it's **periodic**. Find the period p, do `k % p` passes. Rotating a list: p = n. Rotating a grid 90°: p = 4. Reversing: p = 2. |
| **"these cells don't move"** / "anchored" | Possibly nothing | Substitute the fixed set into the transform. If fixed cells map to fixed cells, the set is closed and the wrapper is a `continue`. If not, work out what moves where before typing. |
| **"in place"** / "O(1) extra space" | You can't read from what you're writing into | Either walk each cycle with one temp, or use a copy if allowed. Decide **before** typing; mixing a pull formula with an in-place write silently clobbers. |
| **"after each query, report…"** | One batch computation becomes **incremental maintenance** | Keep the aggregate in a variable. Per update: subtract the terms the changed value participates in, apply the update, add them back. |
| **"remove all occurrences of x"** | The container, not the algorithm | Keep counts (a counter/map), not a list. "All occurrences" becomes one assignment. |
| **"return the result"** vs "modify the input" | Scoring, not logic | The grader reads the **return value**. A perfect in-place mutation with no `return` scores zero. |
| **constraints: n ≤ 1e5, values ≤ 1e9** | The complexity target | Read constraints **first**. 1e5 means O(n log n) at worst, so a nested loop is ruled out before you design. 1e9 on a count means you don't iterate it. |
| **"the grid isn't square"** | Which transforms still make sense | Transpose and ring rotation survive. A 90° rotation of n×m returns m×n, so in place is off the table. |

## The anchor test — 10 seconds that makes index formulas safe

**Never commit an index formula from memory.** Every transform has a plausible mirror image, and under a clock you can't tell which one you wrote.

1. Write the candidate formula.
2. Pick **one** cell whose destination you're certain of by eye on a 3×3.
3. Substitute. If it disagrees, you wrote the mirror image. Flip it.

Example: clockwise rotation must send the top-middle cell `(0,1)` to `(1,2)`. The formula `new[r][c] = old[c][n-1-r]` pulls `old[2][1]` into `(1,2)`, not `old[0][1]`, so it's the counter-clockwise pull. One substitution catches it; memorizing harder doesn't.
