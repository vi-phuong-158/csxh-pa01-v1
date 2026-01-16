import time
import os
from playwright.sync_api import sync_playwright, expect

def run():
    # Ensure verification dir exists
    os.makedirs("verification", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Login
            print("Navigating to app...")
            page.goto("http://localhost:8501")

            # Wait for Streamlit to load
            print("Waiting for login inputs...")
            page.wait_for_selector('input', timeout=20000)

            # Login
            print("Logging in...")
            page.get_by_placeholder("Nhập username").fill("admin")
            page.get_by_placeholder("Nhập mật khẩu").fill("admin123")
            page.get_by_role("button", name="🔓 Đăng nhập").click()

            time.sleep(3)

            # 2. Change Password (if required)
            if page.get_by_role("button", name="✅ Đổi mật khẩu").is_visible():
                print("Changing password...")
                page.get_by_placeholder("Ít nhất 6 ký tự").fill("password123")
                page.get_by_placeholder("Nhập lại mật khẩu").fill("password123")
                page.get_by_role("button", name="✅ Đổi mật khẩu").click()
                time.sleep(3) # Wait for reload
            else:
                print("No password change screen detected")

            # 3. Navigate to Nhập liệu
            print("Navigating to Nhập liệu...")
            page.wait_for_selector('text="Nhập liệu"', timeout=20000)
            page.get_by_text("Nhập liệu", exact=True).click()
            time.sleep(3)
            page.screenshot(path="verification/debug_4_nhap_lieu.png")

            # 4. Add Basic Info
            print("Adding Basic Info...")
            # Use get_by_role to avoid ambiguity with help buttons
            page.get_by_role("textbox", name="Số CCCD *").fill("001099000001")
            page.get_by_role("textbox", name="Họ và tên *").fill("Test User")

            # Save
            page.get_by_role("button", name="💾 Lưu thông tin").click()

            # Wait for success balloons/toast
            time.sleep(5)
            page.screenshot(path="verification/debug_5_saved_basic.png")

            # 5. Add Relative (Thân nhân)
            print("Adding Relative...")
            page.get_by_text("👨‍👩‍👧‍👦 Thân nhân").click()
            time.sleep(1)

            # Inputs for relative
            inputs = page.get_by_role("textbox", name="Họ và tên *").all()
            target_input = None
            for i in inputs:
                if i.is_visible():
                    if i.input_value() == "":
                        target_input = i
                        break

            if target_input:
                target_input.fill("Relative A")
            else:
                print("Could not find relative name input, using last one")
                inputs[-1].fill("Relative A")

            # Save Relative
            page.get_by_role("button", name="💾 Lưu thân nhân").click()
            time.sleep(3)
            page.screenshot(path="verification/debug_6_saved_relative.png")

            # 6. Delete
            print("Clicking Delete...")
            # Find the delete button. It's in a column.
            # Text is "🗑️".
            delete_btn = page.get_by_role("button", name="🗑️").first
            delete_btn.click()

            time.sleep(1)

            # 7. Verify Confirmation
            print("Verifying confirmation...")
            # Expect text "Xác nhận xóa?"
            expect(page.get_by_text("Xác nhận xóa?")).to_be_visible()

            # Take screenshot
            page.screenshot(path="verification/verification.png")
            print("Screenshot taken!")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
