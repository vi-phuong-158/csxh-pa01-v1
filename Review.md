# Review Dự Án: VCFE Database v2.0

> Ngày review: **2026-06-20** (cập nhật) — bản trước: 2026-05-18
> Reviewer: Claude Code (Opus 4.8) + fan-out agents
> Nhánh: `fix/idor-formula-injection`

---

## Tổng Quan

**VCFE Database** — hệ thống quản lý hồ sơ người Việt có yếu tố nước ngoài, chạy offline/LAN cho PA01 Công an tỉnh Phú Thọ. SQLCipher AES-256 + FastAPI + Jinja2/HTMX/Alpine.js.

```
run_server.py (Launcher: keyring, GUI password)
   └─> FastAPI (backend/) + Jinja2/HTMX/Alpine.js (frontend/)
          └─> SQLCipher AES-256 (security_profile.db)
```

## Đánh Giá Tổng Thể

| Hạng mục | 05-18 | 06-20 | Nhận xét |
|----------|-------|-------|----------|
| Bảo mật | 9/10 | 8.5→9/10 | Phát hiện thêm IDOR + formula injection — **đã vá**. |
| Kiến trúc | 8/10 | 8/10 | Phân tách routes/services/models rõ ràng. |
| Chất lượng code | 8/10 | 8/10 | Nhất quán; nhập Excel viết lại sạch. |
| UX/Giao diện | 8/10 | 8/10 | Tuân thủ modal Alpine; còn vài chỗ `fetch()` thuần. |
| Bảo trì | 6/10 | 7/10 | `bulk_import` cũ vẫn là dead code (nên xóa). |

---

## Trạng Thái Các Vấn Đề Từ Bản Review 2026-05-18

- **VẤN ĐỀ 1 (bulk_import dead code + nhập Excel tối giản):** ✅ **Đã giải quyết.** Tính năng nhập Excel được viết lại hoàn chỉnh trong `backend/services/nhap_excel.py` (đa sheet, **chunked commit 100 dòng**, dedup, batch query chống N+1, báo lỗi từng dòng, trả partial HTMX). Module `backend/utils/bulk_import/` giờ là dead code thực sự (không nơi nào import; bản thân nó còn `from database import ...` kiểu Streamlit → không chạy được). **Khuyến nghị: xóa cả thư mục.**
- **VẤN ĐỀ 2 (đổi mật khẩu DB kick session):** ⏳ Vẫn còn (KI-02) — đã document trong `docs/brain/03-decisions.md`. Nên thêm cảnh báo ở GUI đổi mật khẩu.
- **VẤN ĐỀ 3 (`schemas/` trống):** ⏳ Vẫn vậy — chấp nhận được khi chưa có API JSON public.

---

## Phát Hiện Mới & Trạng Thái Xử Lý

### ✅ Đã vá trong đợt review này

**[P1] IDOR — xóa item con của hồ sơ khác** (`services/profile.py`, `routes/profile.py`)
6 hàm `delete_*` xóa theo `item_id` thuần, không ràng buộc `cccd`. User phụ trách hồ sơ X có thể `DELETE /profile/<cccd_X>/lien-he/<id_của_Y>` để xóa dữ liệu hồ sơ Y.
→ **Đã sửa:** thêm tham số `cccd`, chỉ xóa khi `item.cccd == cccd`. _(commit `f82e0fb`)_

**[P1] Formula/CSV Injection — xuất báo cáo Excel** (`routes/bao_cao.py` `_build_xlsx`)
Dữ liệu người dùng (họ tên, ghi chú…) ghi thẳng vào ô Excel; ô bắt đầu bằng `= + - @` có thể thành công thức thực thi khi mở. `sanitize_for_csv()` đã có sẵn nhưng không được gọi.
→ **Đã sửa:** bọc `sanitize_for_csv()` tại chokepoint `_c()`. _(commit `f82e0fb`)_

**[P1] Mất quan hệ graph khi nhập Excel** (`services/nhap_excel.py` `_import_nhan_than`)
Sheet "Nhân thân" chỉ insert bảng vệ tinh `NhanThan`, không tạo cạnh `QuanHeDoiTuong` dù có cột CCCD nhân thân (thụt lùi so với module cũ).
→ **Đã sửa:** khi nhân thân có CCCD hợp lệ, tạo hồ sơ nháp (`is_draft=True`) nếu chưa có (ràng buộc FK) rồi thêm cạnh `QuanHeDoiTuong`; có ánh xạ từ vựng "Bố/Mẹ/Con/Vợ…" → key graph "Cha-Con/Mẹ-Con/Vợ chồng…", chuẩn hóa hướng + dedup (preload chống trùng, không N+1). Có test 9/9 case ánh xạ.

**[P2] Dedup không nhất quán khi nhập Excel** (`services/nhap_excel.py`)
`nhan_than`/`qua_trinh`/`dac_thu` không chống trùng khi upload lại file (khác lien_he/tai_chinh/phuong_tien).
→ **Đã sửa:** thêm khóa dedup qua `_load_satellite_keys` + check trong vòng lặp: nhân thân
`(cccd, loại quan hệ, họ tên)`, quá trình `(cccd, nội dung, ngày bắt đầu)`, đặc thù
`(cccd, loại hình, nội dung)`. Dòng trùng báo lỗi rõ thay vì nhân đôi.

**[P2] `fetch()` thuần cho ECharts/đồ thị** (`network/index.html`, `profile/_tab_mang_luoi.html`, `bao_cao_charts.js`)
→ **Đã xử lý (document):** chấp nhận ngoại lệ có chủ ý — HTMX swap HTML, không feed JSON cho
thư viện vẽ JS. Ghi rõ trong `docs/brain/03-decisions.md`. Mọi CRUD/điều hướng khác vẫn dùng HTMX.

**[P2] Hệ quả đổi mật khẩu DB (KI-02)**
→ **Đã xử lý (document):** đổi mật khẩu DB diễn ra ngoài app (keyring/`run_server.py`), không có
form trong app. Đã ghi ở `README(VCFE).md` và `docs/brain/03-decisions.md`.

### ⏳ Tồn đọng (chưa xử lý)

| Ưu tiên | Vấn đề | File |
|---------|--------|------|
| P3 | Zip-bomb: `MAX_UPLOAD_MB=10` chặn theo file nén, `.xlsx` bung lớn vào RAM | `config.py`, `routes/nhap_excel.py` |
| P3 | Rò rỉ chi tiết exception ra client | `routes/nhap_excel.py`, `routes/bao_cao.py` |
| P3 | `change_password` không yêu cầu mật khẩu cũ | `routes/auth.py` |
| P3 | Xóa dead code `backend/utils/bulk_import/` | toàn thư mục |
| P3 | Nhập Excel là partial-commit (không nguyên tử) — ghi rõ trong docstring | `services/nhap_excel.py` |

---

## Đã Xác Nhận An Toàn

SQL injection (ORM bind tham số), SQLCipher/PRAGMA key (escape + verify fail-fast + `cipher_compatibility=4`), path traversal khi serve file (`files.py` whitelist + `relative_to`), upload avatar/doc (magic bytes + cap 5MB + tên server-side UUID), CSRF toàn cục, open redirect (`safe_next_url`), phân quyền role + `require_profile_access`, redact secret khi log, `.gitignore` (đã bỏ `.env`/`*.db`/`dist/`), frontend dùng modal Alpine thay `confirm()`, không có `|safe` gây XSS.

## Khoảng Trống Chưa Review

Nhánh review logic backend chuyên sâu (search/fuzzy, network graph, dashboard, deduplication) bị gián đoạn do giới hạn phiên — chưa đánh giá N+1/transaction cho các service đó (ngoài `profile` và `nhap_excel` đã kiểm).

---

## Kết Luận

So với 05-18, dự án tiến bộ rõ: tính năng nhập Excel — điểm yếu lớn nhất — đã được viết lại đạt chuẩn CLAUDE.md và nay có cả quan hệ graph. Ba lỗi P1 (2 bảo mật + 1 thụt lùi tính năng) đã được vá. Việc còn lại chủ yếu là dọn dẹp (xóa `bulk_import` cũ), thống nhất dedup, và vài cải thiện P2/P3 không khẩn cấp.
