## 2024-05-22 - [Pandas Iterrows Anti-pattern in Search]
**Learning:** The application was loading the entire `doi_tuong` table and iterating row-by-row with `iterrows()` to perform fuzzy search. This O(N) Python-loop approach is 8x slower than using Pandas vectorized string operations (`.str.contains`, `.apply`).
**Action:** Always prefer Pandas vectorized operations or boolean indexing over `iterrows()`. For complex fuzzy matching that requires Python logic, use `.apply()` on the specific column rather than iterating the whole DataFrame, or pre-calculate normalized columns.
