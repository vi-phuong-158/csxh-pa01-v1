## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2026-01-26 - Surfacing Hidden Power with Tooltips
**Learning:** Streamlit's `text_input` and `selectbox` UI is often minimal, which can hide powerful logic like fuzzy/subsequence search or advanced filter defaults. Users don't know they can type "viphuong" to find "Vi Ngoc Phuong" unless explicitly told.
**Action:** Always use the `help` parameter and descriptive `placeholder` text to surface advanced capabilities directly in the UI context, rather than relying on external documentation.

## 2026-02-02 - Interactive Dataframes & Selection Loops
**Learning:** Enabling `on_select` in Streamlit dataframes is a huge UX win for "Master-Detail" views, but it introduces a state persistence trap. If a user navigates away and comes back, the selection persists, potentially causing infinite redirects or confusion.
**Action:** Always implement a "Counter/Key Reset" strategy. Increment a session state counter when navigating "Back" to the list view, and use it as part of the `st.dataframe` key (e.g., `key=f"table_{counter}"`) to force a fresh, unselected state.
