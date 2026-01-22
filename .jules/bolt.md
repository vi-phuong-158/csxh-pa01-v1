# Bolt's Journal

## 2024-05-23 - Streamlit Loop Optimization
**Learning:** Streamlit re-runs the entire script on every interaction. Iterating through large datasets (like 1000+ records) and creating widgets inside the loop causes significant lag because it generates thousands of HTML elements on every re-run.
**Action:** Use pagination or `st.dataframe`/`st.data_editor` for large datasets instead of custom row-by-row widget rendering. If custom rendering is needed, implement server-side pagination to limit the number of items rendered at once.

## 2024-05-23 - SQLite String Matching Performance
**Learning:** Python's `rapidfuzz` or `thefuzz` for fuzzy matching 1000+ records in a loop is extremely slow (O(n)).
**Action:** Use vectorization with Pandas or full-text search features if available. For SQLite, since FTS might be overkill for simple needs, pre-normalizing strings and using exact/subsequence matching via vectorized Pandas operations (`.str.contains`) is orders of magnitude faster than iterating row-by-row.
