# Python operation costs

**Organized by "how many items does this touch?", not alphabetically**, because an alphabetical
fact table doesn't transfer under interview pressure; a single question does.

> **The one question:** does this operation touch **one slot**, **every item**, or does it **halve**?
> Everything below is just that question, pre-answered.

---

## Bucket 1 — touches ONE slot → **O(1)**

| Operation | Note |
|---|---|
| `lst[i]` read or write | index math, no scan |
| `lst.append(x)` | **amortized** — say the word; a doubling resize is O(n) but rare |
| `lst.pop()` — from the **end** | |
| `d[k]`, `d[k] = v`, `k in d`, `d.get(k)`, `del d[k]` | average case; **see the k-caveat below** |
| `s.add(x)`, `x in s`, `s.remove(x)` (set) | average case |
| `dq.append` / `appendleft` / `pop` / `popleft` (deque) | this is the whole reason deque exists |
| `heap[0]` (peek) | |
| `len(anything)` | stored, never counted |

⚠️ **The k-caveat, and it is the most-missed item.** Dict and set are O(1) *in the number of keys*.
Hashing the key itself costs O(size of the key). A **string key of length k costs O(k)** to hash and
O(k) to store. `d[some_int]` is O(1). `d[some_string]` is O(k).

## Bucket 2 — touches EVERY item → **O(n)**

| Operation | Cost |
|---|---|
| `lst.pop(0)` / `lst.pop(i)` / `lst.insert(i,x)` / `del lst[i]` | O(n) — everything after shifts |
| `x in lst` (list), `lst.index(x)`, `lst.count(x)`, `lst.remove(x)` | O(n) |
| `min(lst)`, `max(lst)`, `sum(lst)` | O(n) |
| `lst.reverse()`, `lst.copy()`, `list(other)`, `set(lst)` | O(n) |
| `lst[a:b]` slice | **O(b−a)** — a slice is a copy |
| `lst1 + lst2` | O(n+m) |
| `s.split()`, `s.replace()`, `s.strip()`, `s.lower()`, `s.find()` | O(n) |
| `"".join(parts)` | O(total length) — and it is the **fix** for the row below |
| `Counter(iterable)` | O(n) |
| iterating a dict/set | O(n) |
| `dq[i]` — indexing a deque in the **middle** | O(n) — deque is O(1) only at the ends |

## Bucket 3 — HALVES → **O(log n)**

| Operation | Cost |
|---|---|
| `heapq.heappush` / `heappop` | O(log n) |
| `bisect.bisect_left` / `bisect_right` | O(log n) |
| binary search you write yourself | O(log n) |

⚠️ **`bisect.insort` is O(n), not O(log n).** The *search* halves; the *insert* still shifts the
whole list. Classic trap, and it is the same shape as `lst.insert`.

## Bucket 4 — sorts → **O(n log n)**

| Operation | Time | Space |
|---|---|---|
| `lst.sort()` | O(n log n) | **O(n) auxiliary** (Timsort) — not O(1) |
| `sorted(anything)` | O(n log n) | O(n), builds a new list |
| `sorted(word)` for a word of length k | **O(k log k)** | O(k) |
| `sorted(d.items())` | O(n log n) | O(n) |

⚠️ **`heapq.heapify(lst)` is O(n), NOT O(n log n).** Building a heap from an existing list is linear.
Getting this right unprompted reads as depth.
⚠️ `heapq.nlargest(k, iterable)` is O(n log k) — better than sorting when k is small.

---

## The two multipliers that actually cost points

### 1. Strings are containers, not values

`str` is **immutable**, so every "modification" is a copy of the whole thing.

| Written | Real cost | In a loop over n |
|---|---|---|
| `s = s + t` | O(len(s)+len(t)) | **O(n²)** — and O(n²k) if each `t` has length k |
| `s[a:b]` | O(b−a) | **O(n²)** if the slice grows |
| `d[s] = v` where `s` is length k | O(k) | O(n·k) |
| `sorted(s)` | O(k log k) | O(n·k log k) |
| `"".join(parts)` at the end | O(total) | **O(n) — this is the fix** |

### 2. If the thing it touches GROWS, the cost is not one number

Write the cost **at iteration i**, then sum. **1+2+…+n = n²/2 = O(n²).**
Covers: growing string, growing slice, growing list you re-scan, growing set you copy.

---

## Substring search — the one people get wrong

`t in s` where `s` has length n and `t` has length m is **O(n·m)** worst case in CPython, not O(n).
Same for `s.find(t)`, `s.count(t)`, `s.replace(old, new)`. Fine to use; know the bound.

## Space conventions

- Report **auxiliary** space — "not counting the input." Say the convention out loud.
- **The recursion stack counts.** DFS on an all-land R×C grid is O(R·C) *stack*, even when the data
  is O(1) because you marked in place.
- Output space is conventionally excluded when the output *is* the answer — but say that you are
  excluding it.
- `lst.sort()` is O(n) auxiliary. Mutating in place is O(1) auxiliary. A dict of n string keys of
  length k is O(n·k).
