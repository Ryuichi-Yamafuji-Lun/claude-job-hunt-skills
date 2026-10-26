# Graphs — recognition first, algorithm second

The complaint "I'm not creative with graphs" is almost never about Dijkstra. It's about not
*noticing* that a problem is a graph. That's a recognition skill, and it's trainable.

## The recognition test

Ask two questions about any problem:

1. **What is a node?** — Often not a "vertex". A node is a **state**: a board configuration, a
   4-digit lock combination, a word, a (row, col) cell, a (city, flights_used) pair.
2. **What is an edge?** — A **legal transition** between states, costing 1 (or a weight).

If both have answers, it's a graph, and you are looking for reachability, shortest path, ordering,
or connectivity over states. Nothing else changes.

Worked examples of the disguise:

| Problem | Node | Edge |
|---|---|---|
| Word Ladder | a word | one-letter mutation, cost 1 |
| Open the Lock | 4-digit combo | turn one wheel, cost 1 |
| Number of Islands | grid cell | 4-directional adjacency |
| Course Schedule | course | prerequisite |
| Evaluate Division | variable | division ratio, weighted |
| Cheapest Flights ≤ K stops | (city, stops used) | flight, weighted |
| Sliding Puzzle | board arrangement | one legal slide |
| Alien Dictionary | letter | "comes before", from adjacent word pairs |

Note the fourth column of that idea: **when a constraint like "at most K stops" won't fit, push it
into the node.** State = (position, resource-remaining). This one move solves a large class of
problems that look impossible as plain graphs.

## The decision tree

```
Is it a graph? (nodes = states, edges = transitions)
│
├── Just need to visit everything / count components / flood fill
│      → DFS or BFS.  O(V+E) time, O(V) space
│
├── Shortest path, all edges cost the same
│      → BFS.  O(V+E)
│      → spreading from many origins at once? multi-source BFS: seed the queue with all of them
│      → also searching backward? bidirectional BFS
│
├── Shortest path, weighted, no negative edges
│      → Dijkstra (binary heap).  O((V+E) log V)
│
├── Shortest path, negative edges allowed
│      → Bellman-Ford.  O(V·E)   (also detects negative cycles)
│      → hop-limited (≤ K edges)? Bellman-Ford relaxing exactly K times
│
├── Shortest path between ALL pairs, small V (≲ 400)
│      → Floyd-Warshall.  O(V³), 3 nested loops, k outermost
│
├── Ordering under prerequisites / dependency resolution
│      → Topological sort.  Kahn's BFS on in-degree, or DFS postorder reversed.  O(V+E)
│      → a cycle means no valid order — that IS the answer to "can you finish all courses"
│
├── Dynamic connectivity, "are these two in the same group", merging
│      → Union-Find.  ~O(1) amortized per op
│
├── Cheapest set of edges connecting everything
│      → MST: Kruskal (sort edges + DSU, O(E log E)) or Prim (heap, O(E log V))
│
├── Two-colorable / no odd cycle / split into two teams
│      → BFS 2-coloring.  O(V+E)
│
└── Enumerate all paths / all configurations
       → Backtracking DFS with an explicit visited set you un-mark on the way out
```

## Cycle detection — the two cases are different

- **Undirected**: DFS, and a visited neighbor that isn't your parent means a cycle. Or Union-Find:
  an edge whose endpoints already share a root closes a cycle.
- **Directed**: three colors — white (unseen), gray (on the current stack), black (finished).
  Hitting a **gray** node is a back edge, i.e. a cycle. Hitting black is fine. Confusing these two
  is one of the most common interview errors; a plain `visited` set does not work for directed.

## Implementation defaults worth memorizing cold

- **Grid directions**: `dirs = [(0,1),(0,-1),(1,0),(-1,0)]`, iterate, bounds-check, then visited-check.
- **Mark visited on push, not on pop.** Marking on pop lets duplicates into the queue and quietly
  degrades BFS.
- **BFS level tracking**: snapshot `len(queue)` at the top of each level and pop exactly that many.
- **Dijkstra with a lazy heap**: push `(dist, node)`; on pop, if the popped dist exceeds the recorded
  best, `continue`. No decrease-key needed. Say "lazy deletion" out loud.
- **Dijkstra is invalid with negative edges** — say why if asked: the greedy finalization assumes
  distances can only grow along a path.

## Complexity in terms of V and E

State both. On a dense graph E ≈ V², on a grid E ≈ 4V. `O(V+E)` on an `m × n` grid is `O(mn)` —
convert to the problem's own variables rather than leaving it abstract; interviewers notice.

## Drill set, in order

Recognition → traversal → ordering → weighted → state-in-the-node.

1. Number of Islands (grid as graph)
2. Rotting Oranges (multi-source BFS)
3. Clone Graph (traversal + hash map bookkeeping)
4. Course Schedule I & II (topological sort, both flavors)
5. Word Ladder (the disguise, hard version of BFS)
6. Number of Connected Components / Redundant Connection (Union-Find)
7. Is Graph Bipartite (2-coloring)
8. Network Delay Time (plain Dijkstra)
9. Cheapest Flights Within K Stops (state = node + resource)
10. Alien Dictionary (build the graph yourself, then toposort)
