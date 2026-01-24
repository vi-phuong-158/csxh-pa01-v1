## 2025-05-26 - Toasts for Micro-Interactions
**Learning:** In Streamlit apps with complex forms, using `st.success` + `st.rerun` for every small addition (like adding a list item) creates a jarring experience. `st.toast` provides transient, non-blocking feedback that feels much more modern and less disruptive, especially when combined with immediate UI updates.
**Action:** Prefer `st.toast` for secondary actions (Add/Delete items from a list) and reserve `st.success` + `st.balloons` for primary success states (Create/Submit main entity).

## 2025-05-27 - Streamlit Popover Testing with Playwright
**Learning:** Streamlit popovers render their content in the DOM but hidden until opened. Playwright's strict mode fails if multiple popovers exist with similar content, even if closed. Additionally, sidebar buttons (e.g., "Đổi mật khẩu") can conflict with main content buttons if labels share substrings.
**Action:** Use unique data for test items to target specific popovers. Use `exact=True` for button locators to avoid partial matches with sidebar items. Ensure proper visibility checks (`.filter(visible=True)` or specific text matching) when asserting popover content.
