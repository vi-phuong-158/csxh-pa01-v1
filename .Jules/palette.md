## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2026-01-16 - Popover for Destructive Confirmations
**Learning:** Streamlit's `st.popover` is an excellent, lightweight alternative to full modals for simple confirmation dialogs (like delete actions). It keeps context (the button clicked) and doesn't require complex state management or page reloads just to show the question.
**Action:** Use `st.popover` containing a warning and a confirmation button for all inline destructive actions instead of immediate execution.
