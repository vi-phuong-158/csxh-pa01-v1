## 2024-05-22 - [Vectorized Search for Vietnamese Text]
**Learning:** SQLite's `LIKE` operator does not support case/accent-insensitive search for Vietnamese characters effectively. The previous solution loaded all data and used `iterrows` with Python logic, causing O(N) performance bottleneck with high constant factor (0.8s for 10k rows).
**Action:** Use Pandas vectorized string operations (`.str.contains` and boolean indexing) instead of `iterrows`. This reduced search time by ~7.5x while maintaining complex fuzzy matching logic (containment + subsequence). Centralize text normalization in `utils/text_utils.py` to support this.

## 2026-01-24 - [Hybrid SQL Filtering for Optimized Search]
**Learning:** While Python-based fuzzy matching is necessary for Vietnamese text, loading the entire dataset (`SELECT *`) for every search is inefficient. Pushing strict filters (Province, Gender, CCCD) to the SQL layer *before* loading data into Pandas drastically reduces the working set.
**Action:** Implemented a hybrid approach:
1. Exact/Prefix matches (like CCCD) are handled entirely in SQL (`LIKE %...%`), bypassing Python processing (~6x speedup).
2. Categorical filters (Province, Gender) are applied in SQL `WHERE` clauses, reducing data volume for the subsequent Python fuzzy search (~1.8x speedup).
