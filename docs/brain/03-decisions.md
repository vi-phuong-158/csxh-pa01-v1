# 03 — Technical Decisions

> Ghi lại quyết định kỹ thuật quan trọng để agent sau không "phát minh lại" hoặc đảo ngược
> mà không biết lý do. Mỗi entry: quyết định gì, vì sao, đánh đổi gì.

---

## [2024] Mã hóa toàn bộ DB bằng SQLCipher (AES-256)

- **Quyết định:** Một file `.db` duy nhất, mã hóa qua `sqlcipher3-binary`; ép SQLAlchemy dùng
  `module=sqlcipher3.dbapi2`; PIN `PRAGMA cipher_compatibility = 4`.
- **Lý do:** Dữ liệu nghiệp vụ nhạy cảm, máy có thể bị thu giữ vật lý → cần mã hóa at-rest.
- **Đánh đổi:** Phụ thuộc binary SQLCipher; không dùng được `sqlite3` stdlib; PRAGMA không bind
  tham số nên phải escape key thủ công (`_escape_sqlcipher_key`).

## [2024] NullPool + PRAGMA key mỗi connection

- **Quyết định:** `poolclass=NullPool`, `timeout=30`, set `PRAGMA key`/`foreign_keys`/`WAL`
  trong event `connect`, có `_verify_key` fail-fast.
- **Lý do:** Tránh "database is locked" khi xử lý bất đồng bộ; đảm bảo không connection nào mở
  mà thiếu key (chống fail-open mở DB plaintext).
- **Đánh đổi:** Mỗi request mở connection mới (chậm hơn pool) — chấp nhận được vì tải nội bộ nhỏ.

## [v2.0] Zero-config secret: keyring + SECRET_KEY suy ra từ DB_PASSWORD

- **Quyết định:** Bỏ secret khỏi `.env`. `run_server.py` hỏi `DB_PASSWORD` (GUI/getpass), lưu
  Windows Credential Manager (keyring); `SECRET_KEY = PBKDF2(DB_PASSWORD, salt cố định)`.
- **Lý do:** "Mở là chạy", không lưu khóa bí mật ra file văn bản; nhập một lần.
- **Đánh đổi:** **KI-02** — đổi `DB_PASSWORD` → đổi `SECRET_KEY` → mọi session đăng nhập bị
  văng. Đổi `_SK_SALT` cũng invalidate toàn bộ session.

## [Phase 1–3] Bật CSRF toàn cục, gỡ CORS

- **Quyết định:** App-level `Depends(csrf_protect)` cho mọi request unsafe; middleware set cookie
  `csrf_token`; gỡ `CORS allow_origins=["*"]`.
- **Lý do:** App same-origin offline không cần CORS; CSRF vẫn đáng bật để chặn cross-site form.
  Thay thế ghi chú cũ "bỏ qua CSRF".
- **Đánh đổi:** Mọi client gọi API đổi state phải gắn `X-CSRF-Token` hoặc field `_csrf`.

## [F-14] Phân quyền hồ sơ theo `nguoi_phu_trach_id`

- **Quyết định:** User thường chỉ truy cập hồ sơ mình phụ trách hoặc hồ sơ chưa phân công
  (NULL); super_admin xem tất cả. cccd không tồn tại → 404 (giấu thông tin).
- **Lý do:** Giới hạn truy cập theo cán bộ; không phá dữ liệu cũ chưa migrate.
- **Đánh đổi:** Hồ sơ NULL hiện "công khai nội bộ" (default-allow) — muốn default-deny phải sửa
  `require_profile_access` trong `deps.py`.

## [F-14] Auto-migrate idempotent thay cho Alembic

- **Quyết định:** Thêm cột/index mới qua list `_PENDING_COLUMNS`/`_PENDING_INDEXES` trong
  `db/session.py`, chạy khi `init_db` (`create_all` không tự ALTER bảng cũ).
- **Lý do:** Đơn giản cho app đơn-file offline, không cần hệ migration nặng.
- **Đánh đổi:** Không có rollback/version; phải tự đảm bảo DDL idempotent.

## [2026-06-20] Nhập Excel tự tạo quan hệ graph từ sheet Nhân thân

- **Quyết định:** Khi dòng "Nhân thân" có CCCD hợp lệ (khác ĐT chính), ngoài bản ghi vệ tinh
  `NhanThan` còn tạo cạnh `QuanHeDoiTuong`; CCCD nhân thân chưa có hồ sơ → tạo hồ sơ nháp
  `is_draft=True`. Ánh xạ từ vựng nhân thân (Bố/Mẹ/Con/Vợ…) sang key graph
  (Cha-Con/Mẹ-Con/Vợ chồng…), hướng cha/mẹ-con xác định theo giới tính ĐT chính.
- **Lý do:** Khôi phục tính năng graph (P1 #3) từng có ở module `bulk_import` cũ; tận dụng
  unique index `uq_quan_he_cap` để dedup.
- **Đánh đổi:** Nhân thân có CCCD xuất hiện ở CẢ bảng vệ tinh lẫn graph (chủ ý). "Con trai/Con gái"
  khi ĐT chính không rõ giới tính mặc định "Cha-Con". Hồ sơ nháp cần cán bộ bổ sung sau.
- **Người quyết định:** Claude (theo yêu cầu user).

---

## Known Issues (xem README(VCFE).md)

- **KI-01:** `backend/utils/bulk_import/` là dead code (lồng `bulk_import/bulk_import/`, thiếu
  `__init__.py` ngoài, import kiểu Streamlit `from database import ...`). `nhap_excel.py` dùng
  implementation inline tối giản (1 sheet, 9 trường, commit 1 lần — vi phạm quy tắc chunk).
- **KI-02:** đổi mật khẩu DB kick toàn bộ session (do SECRET_KEY suy ra từ DB_PASSWORD).

---

## Template cho entry mới

```
## [YYYY-MM-DD] Tiêu đề quyết định

- **Quyết định:** <mô tả>
- **Lý do:** <vì sao chọn hướng này>
- **Đánh đổi:** <cái gì bị đánh đổi>
- **Người quyết định:** <user / Claude / Codex>
```
