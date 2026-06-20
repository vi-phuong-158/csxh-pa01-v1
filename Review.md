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

**[P3] Các cải thiện còn lại — Đã xử lý**

| Vấn đề | Cách xử lý |
|--------|-----------|
| Zip-bomb upload `.xlsx` | `_check_xlsx_bomb` chặn theo tổng kích thước bung (đọc metadata ZIP, ngưỡng 200MB) trước khi pandas parse |
| Rò rỉ chi tiết exception ra client | Thay bằng thông báo chung; chi tiết chỉ vào log (`routes/nhap_excel.py`, `routes/bao_cao.py`) |
| `change_password` không hỏi mật khẩu cũ | Thêm `current_password` + verify trước khi đổi (`services/auth.py`, `routes/auth.py`, template) |
| Dead code `bulk_import` | Đã xóa cả thư mục `backend/utils/bulk_import/` |
| Nhập Excel partial-commit | Ghi rõ trong docstring `import_workbook` |

### ⏳ Tồn đọng

Không còn mục P1/P2/P3 nào từ bản review này. Xem "Khoảng Trống Chưa Review" bên dưới.

---

## Đã Xác Nhận An Toàn

SQL injection (ORM bind tham số), SQLCipher/PRAGMA key (escape + verify fail-fast + `cipher_compatibility=4`), path traversal khi serve file (`files.py` whitelist + `relative_to`), upload avatar/doc (magic bytes + cap 5MB + tên server-side UUID), CSRF toàn cục, open redirect (`safe_next_url`), phân quyền role + `require_profile_access`, redact secret khi log, `.gitignore` (đã bỏ `.env`/`*.db`/`dist/`), frontend dùng modal Alpine thay `confirm()`, không có `|safe` gây XSS.

## Review Chuyên Sâu Logic Backend (2026-06-20)

Đã soát search/fuzzy, network graph, dashboard/thống kê, deduplication, events. **Không có lỗ
hổng bảo mật mới.** Phần lớn vấn đề là **hiệu năng O(n)/O(n²)** — hiện chấp nhận được ở quy mô
~400 hồ sơ nhưng sẽ xấu đi khi dữ liệu tăng. Đã xác nhận tốt: GROUP BY SQL ở dashboard,
`joinedload` chống N+1 khi export, Union-Find khử trùng, chống chu trình graph (`visited`),
giới hạn depth/node graph, chuẩn hóa cạnh đối xứng nhất quán giữa nhập thủ công và nhập Excel.

### Đáng sửa (bug logic / độ chính xác)
| Mức | Vấn đề | File |
|-----|--------|------|
| TB | **Tìm SĐT ở tra cứu không chuẩn hóa** → lệch với cách ghi DB và với danh bạ, gõ `+84`/có dấu cách là sót kết quả | `services/search.py` (search_profiles) |
| TB | **Cache dashboard không invalidate** sau ghi (TTL 300s) → sau nhập Excel/CRUD số liệu cũ tới 5 phút | `services/dashboard.py` |
| TB | **Bỏ dấu chữ "Đ" lệch nhau** giữa query-side (NFKD, không đổi Đ) và SQL `unaccent_lower` (NFD + Đ→D) → sót tên bắt đầu bằng Đ | `utils/fuzzy_matching.py` vs `utils/text_utils.py` |
| TB | `page`/`page_size` không chặn → offset âm / trả cả bảng | `routes/tra_cuu.py`, `services/search.py` |
| TB | `get_multi_bfs` dedup link bỏ `loai_quan_he` → nuốt cạnh khi 2 người có nhiều loại quan hệ | `services/network.py` |

### Hiệu năng (ổn ở 400 hồ sơ, lưu ý khi scale)
| Vấn đề | File |
|--------|------|
| **N+1 trong BFS graph** (`db.get` từng node; `get_multi_bfs` BFS lại từ đầu mỗi gốc) — pattern fix đã có sẵn ở `quan_he.py` | `services/network.py` |
| Tìm theo tên & fuzzy load toàn bảng vào RAM (không dùng index) | `services/search.py`, `routes/ra_soat.py` |
| Khử trùng O(n²): block `unknown`/năm phổ biến quá lớn; `find_potential_duplicates` không blocking | `utils/deduplication.py`, `utils/fuzzy_matching.py` |
| `count_upcoming_events` đếm bằng `len()` thay vì `func.count` | `services/events.py` |

### Nhỏ
- `dashboard.get_statistics` nuốt mọi exception → trả "0 hồ sơ" giả khi DB lỗi (nên báo lỗi rõ).
- `ra_soat` echo `str(e)` ra UI (rò rỉ chi tiết — giống lỗi đã sửa ở `nhap_excel`).
- Index `ngay_ket_thuc` khai 2 lần (model `index=True` + `_PENDING_INDEXES`).
- `do_tin_cay` quan hệ luôn = 50 (không có đường nhập) — trường "chết" nếu không dùng.

> Các mục này **chỉ mới review, chưa sửa** (theo yêu cầu). Đã đưa vào backlog
> `docs/brain/04-current-tasks.md`. Không mục nào chặn vận hành ở quy mô hiện tại.

---

## Kết Luận

So với 05-18, dự án tiến bộ rõ: tính năng nhập Excel — điểm yếu lớn nhất — đã được viết lại đạt chuẩn CLAUDE.md, có quan hệ graph và phản hồi UI theo từng sheet. Toàn bộ P1/P2/P3 đã xử lý. Review chuyên sâu backend không phát hiện lỗ hổng bảo mật mới; các vấn đề còn lại chủ yếu là hiệu năng chưa cấp thiết ở quy mô ~400 hồ sơ + vài bug logic nhỏ (đã ghi backlog).
