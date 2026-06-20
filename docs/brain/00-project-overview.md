# 00 — Project Overview

## Mục tiêu

VCFE Database (VCFED v2.0 — *Vietnamese Citizens with Foreign Elements Database*) là phần mềm
nội bộ giúp PA01 Công an tỉnh Phú Thọ **lưu trữ, tra cứu và phân tích mạng lưới** hồ sơ người
Việt Nam có yếu tố nước ngoài. Toàn bộ dữ liệu nằm trong một file `.db` mã hóa AES-256
(SQLCipher), chạy 100% offline trên máy/LAN nội bộ — không phụ thuộc internet hay cloud.

## Người dùng chính

- **Cán bộ nghiệp vụ (role `user`)** — tra cứu hồ sơ, nhập/cập nhật dữ liệu được phân công
  (`nguoi_phu_trach_id`), tra cứu danh bạ SĐT/tài khoản, xuất báo cáo.
- **Quản trị viên (role `super_admin`)** — toàn quyền mọi hồ sơ, quản lý người dùng, xem
  audit log, quản lý nguồn dữ liệu, nhập Excel hàng loạt.

## Phạm vi

### Trong scope
- Hồ sơ đối tượng (`doi_tuong`) và các bảng vệ tinh: liên hệ, tài chính, phương tiện, nhân
  thân, hồ sơ đặc thù, tài liệu, quá trình hoạt động, quan hệ giữa các đối tượng.
- Tra cứu (chính xác + fuzzy/RapidFuzz), danh bạ toàn cục, rà soát trùng lặp.
- Phân tích mạng lưới (đồ thị quan hệ), dashboard thống kê (ECharts).
- Nhập liệu thủ công + nhập hàng loạt từ Excel; xuất Word/PDF.
- Phân quyền theo người phụ trách, audit log, quản lý user.

### Ngoài scope
- Mọi tính năng online/cloud, đồng bộ đa máy, API công khai.
- Bảo mật kiểu web public (HTTPS bắt buộc, rate-limit chống DDoS quy mô lớn) — đây là hệ
  thống local/LAN khép kín.

## Điểm khác biệt / giá trị cốt lõi

"Zero-Configuration Security": file DB mã hóa SQLCipher, mật khẩu nhập **một lần** rồi lưu vào
Windows Credential Manager (keyring); `SECRET_KEY` ký session sinh tự động từ mật khẩu DB
(PBKDF2) nên không cần lưu secret ra file văn bản. Đóng gói thành `.exe` (PyInstaller) — "mở là chạy".

## Trạng thái dự án (2026-06-20)

Đã hoàn thành refactor & đóng gói; đang ở giai đoạn **Bảo trì & Nâng cấp**. Phiên bản 2.0.0.
Việc đang làm gần đây xoay quanh **Nhập liệu từ Excel** (`backend/services/nhap_excel.py`,
`routes/nhap_excel.py`) và hoàn thiện UI (theme CAND, danh bạ, chuẩn hóa SĐT).

Hai vấn đề kỹ thuật đã biết (xem `README(VCFE).md`):
- **KI-01:** module `backend/utils/bulk_import/` là dead code (lồng thư mục sai, import kiểu
  Streamlit cũ); `nhap_excel.py` đang dùng implementation inline tối giản.
- **KI-02:** đổi mật khẩu DB → đổi `SECRET_KEY` → mọi session đang đăng nhập bị đăng xuất.
