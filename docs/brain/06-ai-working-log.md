# 06 — AI Working Log

> Nhật ký các lần AI (Claude Code / Codex) sửa code. Mỗi agent PHẢI thêm entry sau mỗi lần
> chạm vào code. Đọc ngược từ trên xuống để biết gần đây ai đã làm gì và vì sao.

---

## Format entry

```
## [YYYY-MM-DD] [Tên task ngắn gọn]
- **Agent:** Claude Code | Codex
- **Thay đổi:** <mô tả ngắn những gì đã làm>
- **File đã sửa:** <danh sách file>
- **Lý do:** <vì sao cần thay đổi>
- **Kiểm tra:** <cách xác minh hoạt động đúng>
```

---

## [2026-06-20] Sửa P1 bảo mật: IDOR (xoá item con) + Formula Injection (xuất Excel)

- **Agent:** Claude Code
- **Thay đổi:**
  - **IDOR:** 6 hàm `delete_*` trong `services/profile.py` giờ nhận thêm `cccd` và chỉ xoá khi
    `item.cccd == cccd` (chống xoá item con của hồ sơ khác qua `item_id`). Cập nhật 6 call site
    trong `routes/profile.py` truyền `cccd`.
  - **Formula injection:** Bọc `sanitize_for_csv()` trong helper `_c()` của `_build_xlsx`
    (`routes/bao_cao.py`) — mọi ô dữ liệu người dùng được prefix `'` nếu bắt đầu bằng `= + - @`.
- **File đã sửa:** `backend/services/profile.py`, `backend/routes/profile.py`,
  `backend/routes/bao_cao.py`.
- **Lý do:** Hai lỗ hổng xác định cao từ bản review 2026-06-20 (IDOR đã xác minh trực tiếp;
  formula injection do 2 agent độc lập cùng phát hiện, hàm `sanitize_for_csv` đã có sẵn nhưng
  path export chính chưa gọi).
- **Kiểm tra:** `python -m py_compile` 3 file → sạch; grep xác nhận không còn call site dùng
  chữ ký cũ; chỗ ghi ô trực tiếp duy nhất còn lại (`_cccd_link`) chỉ ghi CCCD (chuỗi số, an toàn).
- **Phạm vi:** KHÔNG đụng phần graph quan hệ nhập Excel (P1 #3) — ngoài yêu cầu lần này.

## [2026-06-20] Khởi tạo bộ não dự án (AI project brain)

- **Agent:** Claude Code
- **Thay đổi:** Tạo `CLAUDE.md` (root), thay `AGENTS.md` (root) bằng bản pointer, tạo
  `docs/brain/00-06`. Điền nội dung từ khảo sát code thật (main.py, config.py, db/session.py,
  models.py, deps.py, run_server.py, README).
- **File đã tạo/sửa:** `CLAUDE.md`, `AGENTS.md`, `docs/brain/00-project-overview.md` →
  `docs/brain/06-ai-working-log.md`.
- **Lý do:** Thiết lập ngữ cảnh + quy tắc dùng chung để mọi agent đọc trước khi code; đồng bộ
  tài liệu với hiện trạng (CSRF đã bật, launcher là run_server.py, secret qua keyring).
- **Kiểm tra:** Các file tồn tại; Code Graph & schema khớp `backend/`. Không động vào code dự án.
- **Ghi chú:** `.claude/CLAUDE.md` (guardrails đầy đủ) được giữ nguyên làm nguồn chính thức.
