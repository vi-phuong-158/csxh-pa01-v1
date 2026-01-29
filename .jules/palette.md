## 2026-01-25 - [Destructive Action Safety]
**Learning:** Immediate deletion buttons in lists are error-prone and stressful for users.
**Action:** Use `st.popover` with a confirmation message and a primary "Confirm" button for all delete actions. Use `st.toast` for non-blocking success feedback to avoid layout shifts.
