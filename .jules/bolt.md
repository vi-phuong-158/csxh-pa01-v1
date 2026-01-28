## 2024-05-22 - [Vectorized Search for Vietnamese Text]
**Learning:** SQLite's `LIKE` operator does not support case/accent-insensitive search for Vietnamese characters effectively. The previous solution loaded all data and used `iterrows` with Python logic, causing O(N) performance bottleneck with high constant factor (0.8s for 10k rows).
**Action:** Use Pandas vectorized string operations (`.str.contains` and boolean indexing) instead of `iterrows`. This reduced search time by ~7.5x while maintaining complex fuzzy matching logic (containment + subsequence). Centralize text normalization in `utils/text_utils.py` to support this.

## 2026-01-27 - [Push Filters to SQL (Predicate Pushdown)]
**Learning:** Loading full datasets into Pandas for filtering is a major bottleneck (O(N) data transfer). Even with vectorized operations, the memory overhead is unnecessary.
**Action:** Always push categorical filters (`WHERE column = value`) to the SQL query layer before loading data into Pandas for complex text processing.
