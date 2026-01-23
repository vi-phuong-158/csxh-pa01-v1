## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2025-05-26 - Popover Confirmation Patterns
**Learning:** `st.popover` is excellent for inline destructive actions (delete buttons) to avoid cluttering the UI with modals. However, while widgets *inside* the popover (like the confirmation button) need unique `key`s in loops, the `st.popover` container itself **does not accept a `key` argument** and will raise a `TypeError` if one is provided.
**Action:** Use `with st.popover("Label", help="..."):` without a key, but ensure the inner `st.button("Confirm", key=f"conf_{id}")` has a unique key.
