## 2024-05-22 - [Vectorized Search for Vietnamese Text]
**Learning:** SQLite's `LIKE` operator does not support case/accent-insensitive search for Vietnamese characters effectively. The previous solution loaded all data and used `iterrows` with Python logic, causing O(N) performance bottleneck with high constant factor (0.8s for 10k rows).
**Action:** Use Pandas vectorized string operations (`.str.contains` and boolean indexing) instead of `iterrows`. This reduced search time by ~7.5x while maintaining complex fuzzy matching logic (containment + subsequence). Centralize text normalization in `utils/text_utils.py` to support this.

## 2024-05-23 - [Hybrid Search: SQL Filtering + Pandas Fuzzy Matching]
**Learning:** Loading the entire dataset into Pandas for fuzzy search (Vectorized) becomes a bottleneck as data grows (O(N) memory).
**Action:** Push exact match filters (e.g., Province, Gender) to the SQL layer *before* loading data into Pandas. This significantly reduces the dataset size for the expensive fuzzy matching step (~47% faster when filtering by Gender).
