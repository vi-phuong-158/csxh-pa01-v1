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

## [2026-06-20] Hoàn thiện UI nhập Excel + review chuyên sâu backend

- **Agent:** Claude Code
- **Thay đổi:**
  - **UI nhập Excel (hoàn thiện WIP):** `_results.html` hiển thị kết quả theo từng sheet (WIP cũ),
    cập nhật hướng dẫn đa sheet ở `index.html`, alias font icon `.material-symbols-outlined`
    (`cand-theme.css`). Bổ sung phản hồi: số quan hệ + hồ sơ nháp tạo từ sheet Nhân thân — thêm
    `_SheetReport.notes`, `_import_nhan_than` ghi note, template render note (`services/nhap_excel.py`,
    `_results.html`).
  - **Review chuyên sâu backend:** soát search/fuzzy, network graph, dashboard, deduplication,
    events (fan-out 3 agent). Không có lỗ hổng bảo mật mới; ghi findings vào `Review.md` +
    backlog `04-current-tasks.md` (CHƯA sửa — theo yêu cầu chỉ review).
- **File đã sửa:** `backend/services/nhap_excel.py`, `frontend/templates/nhap_excel/{index,_results}.html`,
  `frontend/static/css/cand-theme.css`, `Review.md`, `docs/brain/04-current-tasks.md`.
- **Lý do:** Hoàn thiện vòng phản hồi UI cho tính năng nhập Excel (P1#3) + lấp khoảng trống review backend.
- **Kiểm tra:** `py_compile` sạch; test tích hợp 14/14 PASS (DB tạm cùng mật khẩu); render
  `_results.html` qua Jinja2 (notes + per-sheet + nhánh lỗi) OK.

## [2026-06-20] P3: zip-bomb, ẩn lỗi, mật khẩu cũ, partial-commit, xóa dead code

- **Agent:** Claude Code
- **Thay đổi:**
  - **Zip-bomb:** `_check_xlsx_bomb` (đọc tổng uncompressed-size từ metadata ZIP, ngưỡng 200MB)
    chặn file `.xlsx` bung quá lớn trước khi pandas parse (`services/nhap_excel.py`).
  - **Ẩn lỗi:** thay thông báo exception thô bằng message chung ở `routes/nhap_excel.py` và
    2 handler `routes/bao_cao.py`; chi tiết chỉ vào log.
  - **Đổi mật khẩu:** yêu cầu `current_password` + verify trước khi đổi
    (`services/auth.py`, `routes/auth.py`, `templates/auth/change_password.html`).
  - **Partial-commit:** ghi rõ trong docstring `import_workbook`.
  - **Dead code:** xóa cả thư mục `backend/utils/bulk_import/`.
- **File đã sửa:** `services/nhap_excel.py`, `routes/nhap_excel.py`, `routes/bao_cao.py`,
  `services/auth.py`, `routes/auth.py`, `templates/auth/change_password.html`, `Review.md`,
  `docs/brain/04-current-tasks.md`; xóa `backend/utils/bulk_import/**`.
- **Lý do:** Xử lý các mục P3 từ bản review 2026-06-20.
- **Kiểm tra:** `python -m py_compile` 5 file → sạch; test `_check_xlsx_bomb` (template=False,
  non-zip=False); `change_password` đổi chữ ký, đã rà chỉ 1 caller.

## [2026-06-20] P2: Dedup nhập Excel + document ngoại lệ fetch()/KI-02

- **Agent:** Claude Code
- **Thay đổi:**
  - **Dedup:** `_import_nhan_than`/`_import_qua_trinh`/`_import_dac_thu` (`services/nhap_excel.py`)
    nay chống trùng khi upload lại file qua `_load_satellite_keys` + check khóa:
    nhân thân `(cccd, loai_quan_he, ho_ten)`, quá trình `(cccd, noi_dung, ngay_bat_dau)`,
    đặc thù `(cccd, loai_hinh, noi_dung_chi_tiet)`. Dòng trùng báo lỗi thay vì nhân đôi.
  - **fetch():** ghi nhận ngoại lệ có chủ ý cho ECharts/đồ thị vào `03-decisions.md` (không
    refactor code viz đang chạy). **KI-02:** xác nhận là vấn đề tài liệu (đổi mật khẩu DB ngoài
    app), đã có ở README + decisions — không sửa nhầm form đổi mật khẩu tài khoản user.
- **File đã sửa:** `backend/services/nhap_excel.py`, `Review.md`,
  `docs/brain/03-decisions.md`, `docs/brain/04-current-tasks.md`.
- **Lý do:** Xử lý các mục P2 từ bản review 2026-06-20.
- **Kiểm tra:** `python -m py_compile` sạch; khóa dedup khớp thứ tự cột select của `_load_satellite_keys`.

## [2026-06-20] P1 #3: Khôi phục quan hệ graph khi nhập Excel + cập nhật Review.md

- **Agent:** Claude Code
- **Thay đổi:** `_import_nhan_than` (`services/nhap_excel.py`) nay tạo cạnh `QuanHeDoiTuong`
  khi dòng nhân thân có CCCD hợp lệ: tạo hồ sơ nháp (`is_draft=True`) cho CCCD nhân thân chưa
  tồn tại (ràng buộc FK) rồi thêm cạnh. Thêm bảng ánh xạ `_NHAN_THAN_GRAPH` + `_build_quan_he_edge`
  (Bố/Mẹ/Con/Vợ… → key graph Cha-Con/Mẹ-Con/Vợ chồng…, chuẩn hóa hướng theo giới tính ĐT chính,
  đối xứng dùng min/max). Thêm helper preload `_load_genders` / `_load_edges_touching` (chống N+1,
  chống vi phạm unique index `uq_quan_he_cap`). Viết lại `Review.md` (bản 2026-06-20).
- **File đã sửa:** `backend/services/nhap_excel.py`, `Review.md`,
  `docs/brain/03-decisions.md`, `docs/brain/04-current-tasks.md`.
- **Lý do:** P1 #3 từ bản review — nhập Excel chỉ ghi bảng vệ tinh `NhanThan`, không tạo cạnh
  quan hệ (thụt lùi so với module `bulk_import` cũ).
- **Kiểm tra:** `python -m py_compile` sạch; test logic ánh xạ `_build_quan_he_edge` 9/9 case pass.
- **Phạm vi:** KHÔNG đụng các sheet khác; dedup cho nhan_than/qua_trinh/dac_thu vẫn để P2.

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
