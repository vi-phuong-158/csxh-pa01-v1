## 2024-05-22 - [Vectorized Search for Vietnamese Text]
**Learning:** SQLite's `LIKE` operator does not support case/accent-insensitive search for Vietnamese characters effectively. The previous solution loaded all data and used `iterrows` with Python logic, causing O(N) performance bottleneck with high constant factor (0.8s for 10k rows).
**Action:** Use Pandas vectorized string operations (`.str.contains` and boolean indexing) instead of `iterrows`. This reduced search time by ~7.5x while maintaining complex fuzzy matching logic (containment + subsequence). Centralize text normalization in `utils/text_utils.py` to support this.

## 2026-01-27 - [Push Filters to SQL (Predicate Pushdown)]
**Learning:** Loading full datasets into Pandas for filtering is a major bottleneck (O(N) data transfer). Even with vectorized operations, the memory overhead is unnecessary.
**Action:** Always push categorical filters (`WHERE column = value`) to the SQL query layer before loading data into Pandas for complex text processing.

## 2025-02-20 - [SQLite WAL Mode for Write Performance]
**Learning:** Default SQLite configuration uses `DELETE` journal mode which requires a full fsync on every transaction commit. In a system like `services.py` that commits after every insert (e.g., during bulk import or user entry), this causes massive latency (blocking I/O).
**Action:** Enable `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = NORMAL`. This reduced 1000 insert time from 2.63s to 0.12s (~20x speedup) by using a Write-Ahead Log and reducing fsync frequency while maintaining durability.
