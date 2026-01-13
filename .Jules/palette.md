## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2025-05-27 - Contextual Popovers for Destructive Actions
**Learning:** Using `st.popover` for destructive confirmations (like deletion) creates a better UX than conditional rendering of global dialogs. It keeps the context local to the item being acted upon and reduces state management complexity (no need for `delete_item_id` in session state).
**Action:** Replace custom "Are you sure?" dialog components with `st.popover` containing a confirmation button for row-level destructive actions.
