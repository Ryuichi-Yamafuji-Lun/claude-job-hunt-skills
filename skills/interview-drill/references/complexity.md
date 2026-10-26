# Data structures — costs and the "when"

Complexities are the *typical interview answer*. Where the worst case differs from what you should
say out loud, both are listed — knowing the gap is itself a signal.

## Linear structures

| Structure | Access | Search | Insert | Delete | Space | The "when" |
|---|---|---|---|---|---|---|
| Array (fixed) | O(1) | O(n) | — | — | O(n) | Known size, index math |
| Dynamic array | O(1) | O(n) | O(1)* amortized append | O(n) middle | O(n) | Default container |
| Singly linked list | O(n) | O(n) | O(1) at known node | O(1) at known node | O(n) | O(1) splice; LRU chains |
| Doubly linked list | O(n) | O(n) | O(1) | O(1) | O(n) | LRU cache, order + O(1) removal |
| Stack | — | — | O(1) | O(1) | O(n) | Nesting, undo, DFS-without-recursion |
| Queue | — | — | O(1) | O(1) | O(n) | BFS, level order |
| Deque | O(1) ends | — | O(1) ends | O(1) ends | O(n) | Sliding-window max, monotonic queue |

*Amortized: a doubling resize is O(n) but happens rarely enough that the average append is O(1).
Say "amortized" out loud — interviewers listen for it.

## Associative structures

| Structure | Search | Insert | Delete | Space | The "when" |
|---|---|---|---|---|---|
| Hash map / set | O(1) avg, O(n) worst | O(1) avg | O(1) avg | O(n) | Membership, counting, index-by-key. Default reflex. |
| Balanced BST (TreeMap, `std::map`) | O(log n) | O(log n) | O(log n) | O(n) | You need **order**: floor/ceil, range queries, sorted iteration |
| Binary heap | O(1) peek | O(log n) | O(log n) pop | O(n) | Top-k, streaming median (two heaps), Dijkstra |
| Trie | O(L) | O(L) | O(L) | O(alphabet · nodes) | Prefix queries, autocomplete, word-search-on-grid pruning |
| Union-Find (path compression + union by rank) | O(α(n)) ≈ O(1) | O(α(n)) | — | O(n) | Dynamic connectivity, Kruskal, "are these merged" |

Hash map worst case is O(n) under adversarial collisions. Almost never the answer they want, but
naming it unprompted reads as depth.

Heap **build** from an existing array is O(n), not O(n log n). Common gotcha — get it right.

## Range structures

| Structure | Build | Query | Update | The "when" |
|---|---|---|---|---|
| Prefix sum array | O(n) | O(1) range sum | O(n) | Static array, many range-sum queries |
| Fenwick / BIT | O(n log n) | O(log n) | O(log n) | Prefix sums with point updates |
| Segment tree | O(n) | O(log n) | O(log n) | Range min/max/sum with updates; range assign w/ lazy |

For a new-grad loop, prefix sums are expected, BIT/segment tree are bonus. Recognizing that a
problem *wants* one earns most of the credit even without a full implementation.

## Sorting and searching

| Algorithm | Time | Space | Stable | Note |
|---|---|---|---|---|
| Quicksort | O(n log n) avg, O(n²) worst | O(log n) | No | What most stdlib sorts use (introsort) |
| Mergesort | O(n log n) | O(n) | Yes | Linked lists, external sort, stability required |
| Heapsort | O(n log n) | O(1) | No | In-place guarantee |
| Counting / radix | O(n + k) | O(k) | Yes | Small bounded integer range only |
| Binary search | O(log n) | O(1) | — | Sorted input **or** a monotonic predicate |

**Binary search on the answer** is the underused one. If the question is "minimum X such that a
check passes" and the check is monotonic (true stays true as X grows), binary-search the answer
space, not the array. Ship-capacity, Koko-eating-bananas, split-array-largest-sum all reduce to this.

## Amortized vs average vs worst — say the right word

- **Worst case**: any single operation. What you default to.
- **Average**: over a random input distribution. Hash map O(1) is this.
- **Amortized**: over a *sequence*, guaranteed. Dynamic array append is this. Monotonic stack is
  this — each element is pushed and popped at most once, so an inner `while` loop that looks O(n)
  is O(1) amortized and the whole scan is O(n). This is the single most common place candidates
  over-report complexity.

## Space complexity — the part people skip

Count: output (often excluded — say so), auxiliary structures, **and the recursion stack**. DFS on a
skewed tree is O(n) space. Sorting in-place is O(log n) not O(1) because of the recursion. State
whether you're counting the output; being explicit beats being right silently.

---

# Python specifics (default interview language)

Python hides costs behind clean syntax. These are the places where the code looks O(1) and isn't —
which is exactly where an interviewer catches an over-reported complexity.

## Operation costs that surprise people

| Operation | Cost | Note |
|---|---|---|
| `list.append(x)` | O(1) amortized | |
| `list.pop()` | O(1) | from the end |
| `list.pop(0)` / `list.insert(0, x)` | **O(n)** | shifts everything — use `deque` |
| `list.pop(i)` **anywhere but the end** | **O(n−i)** | same shift. ⚠️ **Classic slip**: `pop(idx+1)` inside a loop, priced at O(1), turning an O(n log n) design into O(n²) |
| `x in list` | **O(n)** | vs `x in set` / `x in dict` at O(1) avg |
| `list[a:b]` slicing | **O(b-a)** | a slice inside a loop silently adds a factor of n |
| `s1 + s2` on strings | **O(n+m)** | strings are immutable; building in a loop is O(n²) |
| `"".join(parts)` | O(total) | the correct way to build a string |
| `deque.appendleft/popleft` | O(1) | `from collections import deque` |
| `heapq.heappush/heappop` | O(log n) | |
| `heapq.heapify(arr)` | **O(n)** | not O(n log n) — in place |
| `sorted()` / `list.sort()` | O(n log n) | Timsort, **stable**. `sorted()` O(n) space for the new list; **`list.sort()` is NOT O(1) space** — Timsort needs a merge buffer, O(n) worst case |
| `min`/`max`/`sum` | O(n) | |
| `set` union/intersection | O(len) | |
| `dict` insertion order | preserved | guaranteed since 3.7 — usable, and worth saying |

## Interview reflexes

- `collections.defaultdict(list)` and `Counter` — say the name; both read as fluency.
  `Counter(s).most_common(k)` is O(n log k).
- `heapq` is a **min-heap only**. For a max-heap, negate the values. For top-k largest, a min-heap
  of size k is O(n log k) — better than sorting. Say which you chose and why.
- Tuples in a heap break ties by the next element; if the second element isn't comparable
  (a custom object), it raises. Push `(priority, counter, item)`.
- `float('inf')` / `float('-inf')` for DP and Dijkstra initialization.
- 2D grid init: `[[0] * n for _ in range(m)]`. **Never** `[[0] * n] * m` — that aliases the same row
  m times. Classic bug; an interviewer watching you type it will say nothing and wait.
- Default recursion limit is 1000. Deep DFS on a 10⁵-node graph will hit it. Mention that you'd go
  iterative in production; `sys.setrecursionlimit` is acceptable to name in an OA.
- `@functools.lru_cache(None)` or `@cache` turns a recursion into top-down DP in one line — perfect
  for deriving the state, but be ready to convert it to a table when asked about space.
- Integers are arbitrary precision — no overflow. Worth stating when a problem hinges on it, since
  the Java/C++ answer would differ.
- `for i, x in enumerate(arr)`, `zip(a, b)`, `range(len(arr) - 1, -1, -1)` — write these without
  thinking. Fumbling reverse-range syntax under pressure costs real minutes.

## Space complexity in Python

The recursion stack still counts, and Python frames are heavy. A memoized DP is O(states) space for
the cache *plus* O(depth) for the stack — report both. Slicing in a recursive function copies, so
`solve(arr[1:])` is O(n²) space overall; pass indices instead.
