## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2026-01-26 - Surfacing Hidden Power with Tooltips
**Learning:** Streamlit's `text_input` and `selectbox` UI is often minimal, which can hide powerful logic like fuzzy/subsequence search or advanced filter defaults. Users don't know they can type "viphuong" to find "Vi Ngoc Phuong" unless explicitly told.
**Action:** Always use the `help` parameter and descriptive `placeholder` text to surface advanced capabilities directly in the UI context, rather than relying on external documentation.

## 2026-02-14 - Streamlining Master-Detail Navigation
**Learning:** The "Selectbox + Button" pattern for selecting items from a list is a legacy Streamlit workaround that adds unnecessary friction. With modern `st.dataframe` selection support, allowing users to click directly on a row to navigate is far more intuitive and reduces clicks by 50%.
**Action:** Replace "Select ID from Dropdown" patterns with interactive `st.dataframe(selection_mode='single-row', on_select='rerun')` for master-detail views.

## 2026-02-15 - Ergonomic Pagination Controls
**Learning:** Default Streamlit `number_input` for pagination is functional but breaks flow; users have to target small spinner arrows or switch to keyboard to type. Large, distinct "Previous/Next" buttons reduce cognitive load and allow for "mindless browsing".
**Action:** Replace standalone number inputs with a "Prev | Page Input | Next" button group for paginated views.
