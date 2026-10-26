# Curriculum

An ordered pattern sequence. Each stage lists study problems (for `learn` / `guided`) and a reserved pool (for cold `mock` / `review`). Representative problems are well-known LeetCode titles; generate them or close variants. **Never use a reserved problem for study.**

Re-derive the order with `/interview-drill plan` against the user's real dates. If an OA or loop is close, front-load the patterns that company is known to test, and keep at least one `oa` simulation per week in the final two weeks.

| # | Pattern | Study (sN) | Reserved, measured cold (pN) |
|---|---|---|---|
| 0 | **Reactivation**: binary search, BFS on a grid, hash-map counting from scratch | Binary Search · Flood Fill | Two Sum · Valid Anagram |
| 1 | **Arrays + hashing** | Contains Duplicate · Group Anagrams | Top K Frequent Elements · Longest Consecutive Sequence · Product of Array Except Self |
| 2 | **Two pointers** | Valid Palindrome · Two Sum II | 3Sum · Container With Most Water |
| 3 | **Sliding window** | Best Time to Buy and Sell Stock · Max Average Subarray | Longest Substring Without Repeating Characters · Minimum Window Substring · Permutation in String |
| 4 | **Stack / monotonic stack** | Valid Parentheses · Min Stack | Daily Temperatures · Evaluate Reverse Polish Notation · Largest Rectangle in Histogram |
| 5 | **Binary search on the answer** | Search Insert Position | Koko Eating Bananas · Search in Rotated Sorted Array · Find First and Last Position |
| 6 | **Linked lists** | Reverse Linked List · Merge Two Sorted Lists | Linked List Cycle · Remove Nth From End · Reorder List |
| 7 | **Trees (DFS/BFS)** | Max Depth · Invert Tree | Level Order Traversal · Validate BST · Lowest Common Ancestor · Diameter of Binary Tree |
| 8 | **Heaps** | Kth Largest in a Stream · Last Stone Weight | K Closest Points · Task Scheduler · Find Median from Data Stream |
| 9 | **Intervals + greedy** | Meeting Rooms · Jump Game | Merge Intervals · Insert Interval · Non-overlapping Intervals |
| 10 | **Graphs** (see `graph-patterns.md`) | Number of Islands · Clone Graph | Course Schedule · Rotting Oranges · Pacific Atlantic · Word Ladder |
| 11 | **Backtracking** | Subsets · Permutations | Combination Sum · Word Search · Letter Combinations |
| 12 | **Dynamic programming** (see `dp-patterns.md`) | Climbing Stairs · House Robber | Coin Change · Longest Increasing Subsequence · Word Break · Unique Paths · Longest Common Subsequence |
| 13 | **Design** | Design HashMap | LRU Cache · Time-Based Key-Value Store · Insert Delete GetRandom O(1) |
| 14 | **OA format** (see `oa-wrappers.md`) | Rotate Image | Spiral Matrix · Game of Life · Range Sum Query (mutable) |

## Pacing

- One measured problem per session unless the user asks for more. Depth over volume.
- A stage is done when the user has one CLEAN cold solve on a reserved problem in it. Move on even if review items remain; the queue handles those.
- A 5-minute `blitz` fits on busy days. A short session is better than a skipped one.
- `diagnose` before stage 1 for anyone who isn't starting cold, so you don't teach what they already have.
