## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2026-01-20 - Confirmation Dialogs with Popover
**Learning:** Replacing direct delete buttons with `st.popover` provides a clean confirmation flow without complex session state management. However, `st.popover` widgets inside loops MUST have unique `key` arguments (e.g., `key=f"pop_{id}"`), otherwise Streamlit crashes with a DuplicateWidgetID error.
**Action:** Always assign a unique key to `st.popover` when generating them dynamically in a list.
