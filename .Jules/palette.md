## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2025-05-27 - Safe Deletion Pattern
**Learning:** Streamlit's default `st.button` executes immediately, which is dangerous for destructive actions like deleting records. Accidental clicks can cause irreversible data loss.
**Action:** Use `st.popover` to wrap destructive buttons. This creates a natural "Confirmation Dialog" where the user clicks the icon first, sees a confirmation message (e.g., "Are you sure?"), and then clicks a "Confirm" button. This micro-interaction adds safety without cluttering the UI.
