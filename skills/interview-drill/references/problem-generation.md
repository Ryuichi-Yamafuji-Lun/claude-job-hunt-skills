# Generating a problem

Every problem is three files in the workspace:

```
pN_<slug>.py                 the user's file (bare stub)
.tests/stubs/pN_<slug>.py    identical copy, so reset.py can restore it
.tests/cases/pN.py           the hidden suite
```

Pick the next free number by listing the workspace (`pN_*` and `sN_*` are separate series).

## 1. The stub

Only a docstring. The function name is the one thing the user can't choose, because the runner looks it up by name.

```python
"""
Merge Intervals

Write a function named `merge`.
"""
```

The interviewer states the problem aloud (in chat), not in the file. In `oa` mode, real platforms show the full statement, so put the full statement, examples and constraints in the docstring, still with no signature.

If the problem needs a node type, include the class, the way LeetCode and real interviewers do:

```python
"""
Binary Tree Level Order Traversal

Write a function named `level_order`. It receives the root TreeNode (or None).
"""
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right
```

## 2. The hidden suite

```python
# .tests/cases/p7.py
FUNC = "merge"
SAMPLES = 2          # the first N cases are what `--sample` runs (the OA "Run" button)
TIMEOUT = 2          # seconds per case; set so the brute force fails the large cases if it should

def ref(intervals):
    intervals = sorted(intervals)
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out

_EXAMPLES = [
    (([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]),
    (([[1, 4], [4, 5]],),                    [[1, 5]]),
]
for args, want in _EXAMPLES:                 # the reference must agree with the statement's examples
    assert ref(*args) == want, (args, ref(*args), want)

import random
_rng = random.Random(7)                      # fixed seed: the suite is identical every run
_extra = [
    ([[1, 4]],),                             # single interval
    ([[1, 4], [0, 4]],),                     # unsorted input
    ([[1, 4], [2, 3]],),                     # containment
    ([[_rng.randint(0, 10**4)] * 2 for _ in range(10**4)],),   # large, inside the constraints
]
CASES = _EXAMPLES + [(a, ref(*a)) for a in _extra]
```

Rules:
- **Expected values come from the reference**, and the reference is checked against the problem's own examples first. Never hand-type an expected value for a large case.
- **Every case stays inside the stated constraints.** A case outside them never counts against the user unless they asked about it during clarify.
- Cover: the examples, empty / single-element input (if the constraints allow), duplicates, negative numbers, already-sorted and reverse-sorted input, and at least one large case near the max size.
- **More than one correct answer?** (any valid topological order, any of several pairs) Define `check(args, got) -> bool` instead of comparing to one answer. Pinning one valid answer grades an implementation detail.
- **Order-insensitive output?** Define `normalize(x)`, e.g. `return sorted(map(sorted, x))`.
- **Trees, linked lists, class-design problems (LRU cache, MedianFinder)?** Define `drive(target, args)` that builds the input from a list or replays an operation sequence, and returns a plain value to compare. `target` is whatever `FUNC` names in the user's file (a function or a class). Example for a class:

```python
FUNC = "LRUCache"
def drive(cls, args):
    capacity, ops = args
    obj, out = cls(capacity), []
    for op, *a in ops:
        out.append(getattr(obj, op)(*a))
    return out
```

## 3. Sanity check before announcing

Write the reference into a temporary file outside the workspace, point the runner at it, and confirm it passes 100%. **Then do the same with a second, top-down (recursive, memoized) solution** whenever the problem has a natural recursive answer. Python's recursion limit crashes a correct recursive solution around depth 1,000–3,000, and raising it with `sys.setrecursionlimit` doesn't reliably help. **Keep the recursion depth a correct solution needs under ~1,000** (cap n accordingly) unless the point of the problem is forcing bottom-up, and if it is, say so in the statement's constraints. A suite that fails a correct answer on a language quirk teaches the wrong lesson.

Also confirm the **brute force fails** the large cases if the problem exists to teach the efficient version; otherwise the large cases aren't testing anything. A broken suite wastes a measurement and burns a problem from the pool. Delete the temporary file afterward.

## Other languages

The runner is Python-only. For another language, write the stub in that language and grade by eye plus a short driver you run yourself. Note in `drill-progress.md` that automated suites aren't available.
