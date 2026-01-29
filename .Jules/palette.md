## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2026-01-29 - Empty States & Clear Buttons
**Learning:** Empty states ("No results found") are dead ends if they don't offer a way out. Adding a "Clear Search" button directly in the empty state transforms a frustration point into a recovery flow. Also, clearing Streamlit inputs programmatically is tricky; dynamic keys (forcing re-render) are more reliable than session state modification for `text_input`.
**Action:** Always provide a "Reset" or "Add New" action in empty state components. Use dynamic keys for resetable inputs.
