# Bolt's Journal

## 2024-05-22 - Search Performance with Pandas
**Learning:** For SQLite + Vietnamese diacritics, using Pandas vectorized operations (`.str.contains`, etc.) is significantly faster than `iterrows` or SQL `LIKE` with wildcards on the application side for complex filtering.
**Action:** Always prefer Pandas boolean masking for search logic in `views/tra_cuu.py`.
