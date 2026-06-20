# 04 — Current Tasks

> Cập nhật mỗi khi bắt đầu hoặc hoàn thành task. Agent đọc đây để biết được phép làm gì.

---

## Đang làm

- **Nhập liệu từ Excel (Bulk Import)** — đang hoàn thiện `backend/services/nhap_excel.py` (file
  mới, chưa commit) + `routes/nhap_excel.py` + template `nhap_excel/`. UI theme CAND
  (`cand-theme.css`) cũng đang chỉnh. _(theo git status tại 2026-06-20)_

---

## Chờ làm (backlog)

### Danh bạ tra cứu toàn cục
- **Mô tả:** Tra cứu SĐT & số tài khoản ngân hàng toàn hệ thống, dùng delay search HTMX.
- **Liên quan:** `routes/danh_ba.py`, `services/search.py`, index `ix_lien_he_gia_tri` / `ix_tai_chinh_so_tai_khoan`.
- **Ưu tiên:** TB.

### Báo cáo thống kê chuyên sâu (ECharts)
- **Mô tả:** Lọc biểu đồ theo thời gian thực, không reload trang.
- **Liên quan:** `routes/bao_cao.py`, `services/dashboard.py`, `frontend/static/js/app/bao_cao_charts.js`.
- **Ưu tiên:** Thấp.

### Xuất báo cáo Word/PDF từ kết quả tìm kiếm
- **Liên quan:** `services/docx_export.py`, fpdf2/python-docx.
- **Ưu tiên:** Thấp.

### (Nợ kỹ thuật) Xóa dead code `bulk_import`
- **Mô tả:** Tính năng nhập Excel đã được viết lại trong `services/nhap_excel.py` (đa sheet,
  chunked commit, dedup, và nay có cả quan hệ graph). Module `backend/utils/bulk_import/` giờ
  là dead code thực sự (không chạy được) → **xóa cả thư mục**.
- **Liên quan:** `backend/utils/bulk_import/`. Chi tiết: `Review.md`.
- **Ưu tiên:** Thấp — dọn dẹp.

### (TB) Sửa bug logic backend từ review 2026-06-20 (xem Review.md)
- Tìm SĐT ở `search_profiles` chưa `normalize_phone` → sót kết quả (đồng bộ với danh bạ).
- Cache dashboard không invalidate sau ghi (`services/dashboard.py`).
- Bỏ dấu chữ "Đ" lệch giữa `fuzzy_matching` (NFKD) và `text_utils` (NFD+Đ→D).
- Validate `page`/`page_size` ở `routes/tra_cuu.py`.
- `get_multi_bfs` dedup link thiếu `loai_quan_he` (`services/network.py`).
- **Ưu tiên:** TB (bug logic, chưa chặn vận hành).

### (Thấp) Hiệu năng khi dữ liệu tăng (xem Review.md)
- N+1 trong BFS graph (`services/network.py` — pattern fix có sẵn ở `quan_he.py`).
- Fuzzy/khử trùng load toàn bảng + O(n²) (`utils/deduplication.py`, `fuzzy_matching.py`, `routes/ra_soat.py`).
- `count_upcoming_events` dùng `func.count`; gỡ index `ngay_ket_thuc` khai trùng.
- **Ưu tiên:** Thấp — ổn ở ~400 hồ sơ.

---

## Không làm lúc này

- Không thêm tính năng online/cloud/đồng bộ đa máy — hệ thống offline khép kín.
- Không thay HTMX/Alpine bằng framework JS nặng — vi phạm [UI-1].
- Không tự refactor `bulk_import/` nếu task không yêu cầu — dễ vỡ thêm.

---

## Đã hoàn thành gần đây

- [2026] UI đợt 2: empty-state macro, a11y, responsive, chuẩn hóa SĐT (commit 83c29a2).
- [2026] Modal xác nhận Alpine thay `window.confirm`, fix fuzzy search (0aac051).
- [2026] perf+sec: thêm index tra cứu, fix N+1, whitelist role (4ebb6b3).
