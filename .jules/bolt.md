## 2026-01-18 - [Vectorized Search Optimization]
**Learning:** `iterrows` in Pandas is extremely slow for filtering large datasets (~90ms for 1k records). Vectorized operations (`str.contains`) combined with `apply` for normalization reduced search time to ~12ms (7x speedup). Even complex fuzzy matching can be partially vectorized by pre-computing normalized columns.
**Action:** Always prefer vectorized Pandas operations over loops. If a custom function is needed, apply it to the Series to create a mask, rather than iterating rows manually.
