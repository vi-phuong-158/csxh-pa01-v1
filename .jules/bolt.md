## 2024-05-23 - [Search Performance Optimization]
**Learning:** SQLite's `LIKE` operator is limited for Vietnamese text search (diacritics, case sensitivity). The application loaded all data into Python to filter using a slow `iterrows()` loop.
**Action:** Replaced `iterrows()` with Pandas Vectorized Operations (`.str.contains`, `.apply`).
**Result:** ~8x speedup for text search, ~36x for exact match on 2000 records.
