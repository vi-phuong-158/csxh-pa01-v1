## 2024-05-22 - [Vectorized Search for Vietnamese Text]
**Learning:** SQLite's `LIKE` operator does not support case/accent-insensitive search for Vietnamese characters effectively. The previous solution loaded all data and used `iterrows` with Python logic, causing O(N) performance bottleneck with high constant factor (0.8s for 10k rows).
**Action:** Use Pandas vectorized string operations (`.str.contains` and boolean indexing) instead of `iterrows`. This reduced search time by ~7.5x while maintaining complex fuzzy matching logic (containment + subsequence). Centralize text normalization in `utils/text_utils.py` to support this.

## 2024-05-22 - [SQL-Level Filtering for Search]
**Learning:** Loading all data into Pandas before filtering (`SELECT *`) is inefficient and can cause pagination bugs (filtering applied after pagination limits results incorrectly).
**Action:** Construct SQL `WHERE` clauses dynamically for categorical filters (Province, Gender) to filter data *before* loading. This reduces memory usage and ensures pagination counts are accurate. Use parameterized queries (`params` argument in `pd.read_sql_query`) to prevent SQL injection.
