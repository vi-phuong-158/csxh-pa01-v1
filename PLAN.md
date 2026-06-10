# KẾ HOẠCH KHẮC PHỤC SAU REVIEW — VCFE DATABASE

> Sinh ra từ đợt review toàn diện ngày 10/06/2026 (bảo mật, hiệu năng, giao diện).
> Quy ước trạng thái: `[ ]` chưa làm · `[x]` đã xong · `[~]` đang làm.
> Cập nhật tiến độ trực tiếp vào file này sau mỗi task hoàn thành.

---

## Nhóm A — Hoàn thiện tính năng Nhập Excel (Ưu tiên 0 — mục tiêu roadmap hiện tại)

File chính: `backend/routes/nhap_excel.py`, `frontend/templates/nhap_excel/index.html`

- [x] **A1. Giới hạn dung lượng file upload** theo `settings.MAX_UPLOAD_MB` (đọc tối đa
      `max_bytes + 1`, vượt ngưỡng → báo lỗi 413 thân thiện). *(Fix bảo mật mức CAO)*
- [x] **A2. Validate format CCCD từng dòng** (đúng 9 hoặc 12 chữ số) — dòng sai bị từ chối
      kèm thông báo rõ ràng, không chèn dữ liệu rác vào DB. *(Fix bảo mật mức TB)*
- [x] **A3. Check trùng CCCD theo batch**: 1 query `IN (...)` cho toàn bộ file thay vì
      `db.get()` từng dòng (N+1); đồng thời phát hiện CCCD lặp ngay trong file Excel.
- [x] **A4. Commit theo chunk 100 dòng** — đúng yêu cầu Database Safety trong CLAUDE.md,
      tránh transaction khổng lồ gây "database is locked".
- [x] **A5. Ghi audit log `BULK_IMPORT`** sau khi import (ai import, bao nhiêu dòng
      thành công/lỗi, tên file). *(Fix bảo mật mức TB)*
- [x] **A6. Bỏ block event loop**: chuyển route upload từ `async def` sang `def` thường
      để FastAPI tự chạy pandas + DB trong threadpool.
- [x] **A7. Frontend: spinner khi upload** (`hx-indicator` + disable nút submit qua
      `hx-disabled-elt`, htmx 1.9.12 hỗ trợ) để cán bộ biết hệ thống đang xử lý file.

## Nhóm B — Hiệu năng (Ưu tiên 1)

- [x] **B1. Thêm index cho cột tra cứu chính**: `lien_he.gia_tri` (SĐT) và
      `tai_chinh.so_tai_khoan` — bổ sung `index=True` trong `backend/models/models.py`
      + lệnh `CREATE INDEX IF NOT EXISTS` vào `_PENDING_INDEXES` (`backend/db/session.py`)
      để DB cũ được migrate tự động. *(Bắt buộc trước khi làm Danh bạ tra cứu toàn cục)*
- [x] **B2. Fix N+1 trong `fuzzy_search`** (`backend/services/search.py`): batch load
      hồ sơ khớp bằng 1 query `IN (...)` thay vì `db.get()` từng kết quả.
- [x] **B3. Fix N+1 trong `get_quan_he_full`** (`backend/services/quan_he.py`): batch load
      toàn bộ đối tác quan hệ bằng 1 query `IN (...)` thay vì `db.get()` từng cạnh.

## Nhóm C — Bảo mật (Ưu tiên 1)

- [x] **C1. Whitelist role trong `create_user`** (`backend/services/auth.py`): chỉ chấp nhận
      `super_admin` / `user`, từ chối mọi giá trị role lạ gửi qua form.

## Nhóm D — Giao diện / Tuân thủ quy tắc [UI-1] (Ưu tiên 1)

- [x] **D1. Modal xác nhận Alpine toàn cục thay `window.confirm()`**: chặn sự kiện
      `htmx:confirm` trong `base.html`, hiển thị modal theo theme CAND (tái dùng pattern
      modal của `nhap_lieu/form.html`). Giữ nguyên các thuộc tính `hx-confirm` hiện có
      (10 chỗ) làm nguồn nội dung câu hỏi — không phải sửa từng template.
- [x] **D2. Xóa `components/header.html` (dead code)**: file không được include ở đâu —
      `base.html` đã dùng `banner.html` chứa logic chuông thông báo phiên bản mới.

## Nhóm E — Phát hiện thêm trong quá trình test (ngoài review ban đầu)

- [x] **E1. Fix fuzzy search hỏng hoàn toàn** (`backend/utils/fuzzy_matching.py`):
      rapidfuzz không tự lowercase như thefuzz — từ khi họ tên bị chuẩn hóa về CHỮ HOA
      (commit `47114b1`), `find_similar_names` luôn trả rỗng vì so query chữ thường với
      candidates chữ hoa. Thêm `processor=normalize_vietnamese` vào `process.extract`.
      Ảnh hưởng cả tính năng Rà soát (`batch_screen`). Đã test: khớp có dấu/không dấu/sai
      1 ký tự đều trả kết quả đúng.

---

## Ghi chú phạm vi

- **Không làm** trong đợt này (đã review, để đợt sau): lỗi validation inline dưới từng
  trường form, chuẩn hóa empty-state partial, breakpoint `md:` cho tablet, ghép
  `label for=`/`id=` (accessibility), chuẩn hóa số điện thoại khi ghi DB.
- Phát hiện "echarts load trên mọi trang" trong review ban đầu là **không chính xác** —
  vendor JS đã được load theo từng trang qua `{% block %}`, không cần sửa.
- Sau khi sửa xong nhóm B1, lần khởi động đầu tiên DB sẽ tự tạo index mới qua
  `_auto_migrate()` — không cần thao tác tay.

## Tiến độ

| Nhóm | Hoàn thành |
|------|-----------|
| A — Nhập Excel | 7/7 ✅ |
| B — Hiệu năng | 3/3 ✅ |
| C — Bảo mật | 1/1 ✅ |
| D — Giao diện | 2/2 ✅ |
| E — Phát hiện thêm | 1/1 ✅ |

**Trạng thái: HOÀN THÀNH TOÀN BỘ (14/14 task) — đã test end-to-end.**

### Kết quả kiểm thử (TestClient + DB SQLCipher thật)

- Upload Excel 6 dòng: 3 nhập thành công, 3 bị từ chối đúng lý do (CCCD sai format,
  CCCD lặp trong file, thiếu họ tên).
- Upload lại cùng file: toàn bộ bị báo "đã tồn tại" (batch check IN hoạt động).
- File 11MB bị chặn với thông báo vượt ngưỡng 10MB.
- Audit log `BULK_IMPORT` ghi đủ: người import, tên file, số dòng thành công/lỗi.
- 2 index mới (`ix_lien_he_gia_tri`, `ix_tai_chinh_so_tai_khoan`) được auto-migrate tạo.
- `get_quan_he_full` sau fix N+1 trả đúng quan hệ; `fuzzy_search` sau fix E1 khớp
  có dấu/không dấu/sai 1 ký tự.
