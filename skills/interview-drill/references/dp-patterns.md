# Dynamic programming — four archetypes that generalize

The instinct that "learning ~4 problems covers almost everything" is correct. Here they are. Learn
each one until you can rebuild it from nothing, then learn to *map* new problems onto them.

## The universal procedure

Every DP problem, no exceptions:

1. **What is the state?** The smallest set of variables that fully describes a subproblem.
   Getting this wrong is the only real way to fail a DP problem — everything else is bookkeeping.
2. **What is the recurrence?** How a state's answer composes from smaller states.
3. **What is the base case?**
4. **What order do states get filled?** (Or: memoize and let recursion decide.)
5. **Where does the answer live?** Last cell, or a max over all cells — not always the same.

Write the recurrence in words before writing it in code. "The best I can do through index i is
either skip i and keep dp[i-1], or take i and add dp[i-2]" is worth more in an interview than a
correct line of code that appeared without explanation.

**Say this out loud whenever it applies:** "This has optimal substructure and overlapping
subproblems, so it's DP rather than greedy or divide-and-conquer." Naming why it isn't greedy is
high-signal.

---

## Archetype 1 — Linear / take-or-skip (1D)

**State**: `dp[i]` = best answer considering the first `i` items.
**Shape**: `dp[i] = f(dp[i-1], dp[i-2], ...)`

**Canonical**: House Robber.
`dp[i] = max(dp[i-1], dp[i-2] + nums[i])` — skip this house, or rob it and take the best from two
back. O(n) time, O(1) space after you notice only two values are ever live.

**Same skeleton**: Climbing Stairs · Min Cost Climbing Stairs · Decode Ways · Word Break
(`dp[i]` true if some `j < i` has `dp[j]` true and `s[j:i]` in dict) · Maximum Subarray ·
House Robber II (run it twice: exclude first, exclude last).

**Cousin worth its own slot — Longest Increasing Subsequence.** `dp[i]` = LIS *ending at* i, which
is O(n²), and the answer is `max(dp)` not `dp[n-1]`. The O(n log n) patience-sorting version with
binary search is a genuinely separate trick — know that it exists and that the "tails" array does
not hold a real subsequence.

**Tell**: linear input, each element take-or-leave, a local constraint like "not adjacent".

---

## Archetype 2 — Knapsack / subset choice with a budget (2D collapsible)

**State**: `dp[i][c]` = best using the first `i` items with capacity/target `c`.
**Shape**: `dp[i][c] = max(dp[i-1][c], value[i] + dp[i-1][c - weight[i]])`

**Canonical**: 0/1 Knapsack. O(n·C) time. Collapses to a 1D array — and the direction of the inner
loop *is* the distinction between the two variants:

- **0/1** (each item once): iterate capacity **descending**.
- **Unbounded** (unlimited copies): iterate capacity **ascending**.

Being able to explain *why* — descending keeps you reading the previous row, ascending lets you
reuse the current row, i.e. the same item again — is a strong moment. Most candidates memorize the
direction without the reason.

**Same skeleton**: Partition Equal Subset Sum (target = sum/2, boolean) · Target Sum ·
Coin Change (unbounded, minimize count) · Coin Change II (unbounded, count ways — note the loop
order: coins outer, amount inner, or you count permutations instead of combinations) ·
Last Stone Weight II · Ones and Zeroes (two budgets, so 3D).

**Tell**: choose a subset, subject to a numeric budget, optimizing count/value/feasibility.
Pseudo-polynomial — `O(n·C)` is *not* polynomial in input size. Say that; it's a real distinction.

---

## Archetype 3 — Two sequences / grid (true 2D)

**State**: `dp[i][j]` = answer for the first `i` of A and first `j` of B (or cell `(i,j)` of a grid).
**Shape**: compare `A[i]` and `B[j]`; match → diagonal + 1; mismatch → best of the neighbors.

**Canonical**: Edit Distance.
```
if A[i] == B[j]:  dp[i][j] = dp[i-1][j-1]
else:             dp[i][j] = 1 + min(dp[i-1][j],    # delete
                                     dp[i][j-1],    # insert
                                     dp[i-1][j-1])  # replace
```
O(mn) time, O(min(m,n)) space rolling.

**Same skeleton**: Longest Common Subsequence · Longest Common Substring (reset to 0 on mismatch —
and the answer is the max over all cells, not the corner) · Unique Paths · Minimum Path Sum ·
Maximal Square · Distinct Subsequences · Interleaving String · Regular Expression Matching
(same grid, gnarlier transition on `*`).

**Tell**: two strings/arrays being aligned, or literal 2D movement. Base row and base column are
where the off-by-ones live — fill them explicitly and say what they mean.

---

## Archetype 4 — Interval / partition DP

**State**: `dp[i][j]` = answer for the subarray `i..j`.
**Shape**: pick a split point or a "last thing resolved" `k` inside the interval, and combine.
**Order**: by increasing interval **length**, not by index.

**Canonical**: Burst Balloons. The inversion is the whole lesson — instead of asking which balloon
pops *first*, ask which pops **last** in `i..j`, because then the two sides are independent:
```
dp[i][j] = max over k in (i,j) of  dp[i][k] + nums[i]*nums[k]*nums[j] + dp[k][j]
```
O(n³) time, O(n²) space.

**Same skeleton**: Matrix Chain Multiplication · Palindrome Partitioning II ·
Longest Palindromic Subsequence · Stone Game / Predict the Winner (two-player, `dp[i][j]` = best
score *difference* — encoding both players in one number is the trick) · Minimum Cost to Cut a Stick.

**Tell**: "combine adjacent things", "remove one at a time and the neighbors change", "split into
groups optimally". Usually O(n³). The reflex to build: *when the first choice entangles the two
halves, reason about the last choice instead.*

---

## Two more to recognize (don't need mastery for a new-grad loop)

**State-machine DP** — you're in one of a few named states, and each state's next value depends on
the others. Best Time to Buy and Sell Stock with Cooldown: `hold`, `sold`, `rest`. With **k**
transactions it becomes `dp[k][hold?]`. Appears often enough at big tech to be worth an evening.
Recognize it by: "you may hold at most one X at a time" / "with a cooldown" / "at most k times".

**Bitmask DP** — state includes a subset of ≤ ~20 items encoded as an integer. Travelling Salesman,
assignment problems. `O(2ⁿ · n)`. Rare for new grad; recognizing the `n ≤ 20` constraint as the tell
is the whole win.

---

## Constraint sizes as hints (works for every topic, not just DP)

| n up to | Intended complexity |
|---|---|
| 10–12 | O(n!) — permutations, backtracking |
| ~20 | O(2ⁿ) — subsets, bitmask |
| ~100–500 | O(n³) — interval DP, Floyd-Warshall |
| ~5,000 | O(n²) — 2D DP, LIS naive |
| ~10⁵–10⁶ | O(n log n) or O(n) — sort, heap, two pointers, sliding window |
| ~10⁹ | O(log n) or O(1) — binary search, math |

Reading constraints backward into a target complexity is a legitimate, expected interview move.
Do it out loud: *"n is 10⁵, so I need n log n or better — that rules out the O(n²) DP."*

---

## Drill order

Do these five first; they are one per archetype plus the state-machine.

1. House Robber → then Word Break (archetype 1)
2. Coin Change → then Partition Equal Subset Sum (archetype 2)
3. Longest Common Subsequence → then Edit Distance (archetype 3)
4. Longest Palindromic Subsequence → then Burst Balloons (archetype 4)
5. Best Time to Buy and Sell Stock with Cooldown (state machine)

**Do each one twice**: top-down memoized first (easier to derive — write the recursion, add a
cache), then bottom-up tabulated (what interviewers like to see, and where space optimization
lives). Deriving top-down and then *converting* it out loud is the strongest way to present DP
under pressure, because it shows the state was discovered rather than recalled.
