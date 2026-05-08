# KẾ HOẠCH: Refactor "Nhân thân" → "Quan hệ" + Auto tạo hồ sơ

> **Trạng thái:** Đã chốt thiết kế, chờ thực hiện.
> **Branch phát triển:** `claude/auto-create-profile-relationship-PBkZr`
> **Ngày lập kế hoạch:** 2026-05-08
> **Người phụ trách thực hiện:** Anh (sau chuyến công tác)

---

## 1. BỐI CẢNH & VẤN ĐỀ

### Vấn đề anh nêu
- Tab "Nhân thân" hiện tại bắt nhập CCCD nhưng dữ liệu chỉ là **thuộc tính** (satellite) của 1 hồ sơ.
- Khi sau này gặp lại chính người thân nhân đó để lập hồ sơ chính → **phải nhập lại từ đầu** mọi thông tin.
- Cần đổi tên thành "Quan hệ" (tổng quát hơn) để chuẩn bị cho roadmap **vẽ mạng lưới quan hệ**.

### Phát hiện trong codebase
- `backend/models/models.py:93` — bảng `nhan_than` (satellite, không FK sang DoiTuong khác).
- `backend/models/models.py:172` — bảng `quan_he_doi_tuong` (graph, có FK 2 chiều sang `doi_tuong.cccd`) — **đã định nghĩa từ trước nhưng CHƯA NƠI NÀO DÙNG**. Đây chính là bảng edge sẵn sàng cho graph visualization.

### Phát hiện vấn đề bonus: KHÔNG SỬA ĐƯỢC CCCD
- `DoiTuong.cccd` là **PRIMARY KEY** (`models.py:15`).
- 8 bảng FK `ON DELETE CASCADE` nhưng **KHÔNG có `ON UPDATE CASCADE`** → sai 1 số CCCD lúc nhập = phải xóa và tạo lại, mất hết dữ liệu liên kết.

---

## 2. QUYẾT ĐỊNH ĐÃ CHỐT (6 câu)

| # | Quyết định | Chi tiết |
|---|---|---|
| 1 | **Bỏ auto-draft** | Form nhập có họ tên → lưu hồ sơ chính thức (`is_draft=False`) ngay. Chỉ khi nhập mỗi CCCD trống tên → mới `is_draft=True` |
| 2 | **Sửa CCCD = Hướng A + C** | A: viết hàm `change_cccd` cập nhật transaction toàn bộ FK + filesystem. C: thêm bảng `cccd_history` để tra cứu CCCD cũ |
| 3 | **Sửa CCCD làm Sprint riêng** | Tách bạch khỏi sprint Quan hệ vì rủi ro cao (đụng 8 bảng FK + uploads/) |
| 4 | **Chính sách xóa quan hệ = Cách 2** | Auto dọn hồ sơ nháp mồ côi: sau khi xóa edge, nếu DoiTuong đối tác là `is_draft=True` AND không còn edge AND không có satellite → xóa luôn |
| 5 | **Refactor `LOAI_QUAN_HE` thành cặp có hướng** | "Cha-Con" thay vì "Bố"+"Con trai" lẫn lộn. Bắt buộc để render đảo chiều tự động |
| 6 | **Migration dữ liệu cũ làm Sprint riêng** | Code mới chạy song song với data cũ. Migrate khi anh sẵn sàng (cần backup DB) |

### Quyết định bonus (đã thống nhất qua thảo luận)
- **Phương án C (Hybrid)**: có CCCD → đi Graph; không có CCCD → fallback `nhan_than` (cho người nước ngoài thông tin mơ hồ).
- **Tab tên gọi**: "Quan hệ".
- **Quan hệ đảo chiều tự động**: 1 edge → render ở cả 2 hồ sơ với nhãn ngược chiều.
- **UI form 2-mode**: radio "Có CCCD" / "Không có CCCD" — bắt user chọn rõ trước khi nhập.

---

## 3. KIẾN TRÚC TỔNG THỂ

### Triết lý
> "Có CCCD → đi Graph (tạo hồ sơ thực sự + edge). Không CCCD → fallback Satellite (ghi chú quan hệ mơ hồ)."

### So sánh trước/sau

| | Trước | Sau |
|---|---|---|
| Tab tên | Nhân thân | Quan hệ |
| Bảng dùng | Chỉ `nhan_than` | `quan_he_doi_tuong` (graph) + `nhan_than` (fallback) |
| Khi nhập CCCD | Lưu text vào `nhan_than.cccd_nhan_than` | Tạo `DoiTuong` mới (nếu chưa có) + edge |
| Lần sau gặp người này | Nhập lại từ đầu | Click vào tab Quan hệ → mở hồ sơ đã có |
| Sửa CCCD | Phải xóa-tạo-lại | Có nút "Sửa CCCD" (Sprint 2) |
| Vẽ mạng lưới | Không thể | Sẵn sàng (Sprint 4) |

### Logic auto tạo hồ sơ
```python
if data['cccd_doi_tac'] hợp lệ:
    dt = db.get(DoiTuong, cccd_doi_tac)
    if not dt:
        # Chưa có → tạo mới
        is_draft = not bool(data.get('ho_ten'))  # có tên → chính thức luôn
        dt = DoiTuong(cccd=cccd_doi_tac, is_draft=is_draft, ho_ten=..., ...)
    else:
        # Đã có → CHỈ FILL Ô TRỐNG, không ghi đè
        if not dt.ho_ten and data.get('ho_ten'): dt.ho_ten = data['ho_ten']
        # ...

    # Chuẩn hóa cặp theo loai_quan_he
    cccd_1, cccd_2, loai_chuan = chuan_hoa_cap(cccd_chinh, cccd_doi_tac, loai)
    db.add(QuanHeDoiTuong(cccd_1, cccd_2, loai_chuan, ...))
```

### Logic chuẩn hóa cặp (đảo chiều tự động)
- Quan hệ **có hướng** (Cha-Con, Mẹ-Con): lưu nguyên thứ tự cccd_1=cha, cccd_2=con.
- Quan hệ **đối xứng** (Vợ chồng, Anh chị em, Bạn bè): chuẩn hóa `cccd_1 = min(a, b)`, `cccd_2 = max(a, b)` để 1 cặp người chỉ có 1 row.

### Render đảo chiều
Khi xem hồ sơ A:
```python
edges = query(QuanHeDoiTuong).filter(or_(cccd_1==A, cccd_2==A))
for edge in edges:
    if edge.cccd_1 == A:
        nhan = LOAI_QUAN_HE_DEF[edge.loai_quan_he]['label_xuoi']  # vd: "Cha"
        cccd_doi_tac = edge.cccd_2
    else:
        nhan = LOAI_QUAN_HE_DEF[edge.loai_quan_he]['label_nguoc']  # vd: "Con"
        cccd_doi_tac = edge.cccd_1
```

---

## 4. WIREFRAME UI

### Tab "Quan hệ" — Form thêm

```
┌─ Thêm quan hệ ──────────────────────────────────────┐
│ Loại quan hệ: [Chọn ▼]                              │
│   Options: Cha-Con, Mẹ-Con, Vợ chồng, Anh chị em,   │
│            Bạn bè, Đồng nghiệp, Khác                │
│                                                      │
│ Người này có CCCD/CMND không?                        │
│ ⊙ Có CCCD     ○ Không có / không rõ                 │
│                                                      │
│ ┌─ Nếu chọn "Có CCCD" ─────────────────────────────┐ │
│ │ CCCD *: [____________] (HTMX preview onblur)     │ │
│ │                                                   │ │
│ │ 🟢 Đã có hồ sơ: NGUYỄN VĂN A — sinh 1985         │ │
│ │    → Liên kết tới hồ sơ này. Form ẩn.            │ │
│ │ HOẶC                                              │ │
│ │ 🟡 Chưa có hồ sơ — sẽ tạo mới                    │ │
│ │    → Form đầy đủ trường hiện ra (ho_ten,         │ │
│ │       ngày sinh, dân tộc, tôn giáo, quốc tịch,   │ │
│ │       địa chỉ, nghề nghiệp...)                   │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─ Nếu chọn "Không có CCCD" ───────────────────────┐ │
│ │ ⚠ Sẽ lưu dạng ghi chú, không thể vẽ mạng lưới    │ │
│ │   hay liên kết hồ sơ.                            │ │
│ │ Họ tên: [______]  Quốc tịch: [______]            │ │
│ │ Mô tả/đặc điểm nhận dạng: [_______________]      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ Mô tả quan hệ: [________________]                    │
│                          [Hủy]    [Lưu]              │
└──────────────────────────────────────────────────────┘
```

### Tab "Quan hệ" — Bảng list

| Loại | Họ tên | CCCD | Loại nguồn | Hành động |
|---|---|---|---|---|
| Vợ | NGUYỄN THỊ B (link) | 012... | 🔗 Hồ sơ | [Xóa] |
| Cha | NGUYỄN VĂN C (link) | 011... | 🔗 Hồ sơ + 🟡 Nháp | [Xóa] |
| Bạn | John Smith | — | 📝 Ghi chú | [Xóa] |

---

## 5. SPRINT 1 — Tab "Quan hệ" (LÀM TRƯỚC)

### T1.1 — Refactor `LOAI_QUAN_HE` thành dạng cặp có hướng
**File:** `backend/constants.py` (sửa dòng 280-283)
**Việc cần làm:**
```python
LOAI_QUAN_HE_DEF = {
    "Cha-Con":   {"label_xuoi": "Cha", "label_nguoc": "Con", "doi_xung": False},
    "Mẹ-Con":    {"label_xuoi": "Mẹ", "label_nguoc": "Con", "doi_xung": False},
    "Vợ chồng":  {"label_xuoi": "Vợ/Chồng", "label_nguoc": "Vợ/Chồng", "doi_xung": True},
    "Anh chị em":{"label_xuoi": "Anh/Chị/Em", "label_nguoc": "Anh/Chị/Em", "doi_xung": True},
    "Bạn bè":    {"label_xuoi": "Bạn", "label_nguoc": "Bạn", "doi_xung": True},
    "Đồng nghiệp":{"label_xuoi": "Đồng nghiệp", "label_nguoc": "Đồng nghiệp", "doi_xung": True},
    "Khác":      {"label_xuoi": "Khác", "label_nguoc": "Khác", "doi_xung": True},
}

def get_quan_he_label(loai: str, vi_tri: int) -> str:
    """vi_tri=1 trả label_xuoi; vi_tri=2 trả label_nguoc"""
    info = LOAI_QUAN_HE_DEF.get(loai, {})
    return info.get('label_xuoi' if vi_tri == 1 else 'label_nguoc', loai)
```
**Kiểm chứng:** `from backend.constants import get_quan_he_label; print(get_quan_he_label("Cha-Con", 2))` → "Con"

---

### T1.2 — Cập nhật schema DB cho `quan_he_doi_tuong`
**File:** `backend/db/session.py` (theo pattern `_ensure_columns` dòng ~174) + `backend/models/models.py:172-181`
**Việc cần làm:**
- Thêm Index trên `cccd_1`, `cccd_2`, `loai_quan_he` (single + composite).
- Thêm UNIQUE constraint `(cccd_1, cccd_2, loai_quan_he)`.
- Service phải guard `cccd_1 != cccd_2` (cấm self-loop) — vì SQLite CHECK constraint không reliable.
- Tạo cơ chế migrate `_ensure_indexes` tương tự `_ensure_columns` để chạy lần đầu sau update.

**Kiểm chứng:** Chạy app, `sqlite> .schema quan_he_doi_tuong` thấy index mới.

---

### T1.3 — Service `services/quan_he.py` (file mới)
**File:** `backend/services/quan_he.py` (TẠO MỚI)
**Hàm cần viết:**
```python
def get_quan_he_full(db, cccd) -> List[Dict]:
    """Gộp graph + satellite, render đúng chiều"""

def add_quan_he_co_cccd(db, cccd_chinh, data) -> Tuple[bool, str]:
    """Tạo edge + auto tạo DoiTuong nếu chưa có (is_draft theo có ho_ten)"""

def add_quan_he_khong_cccd(db, cccd_chinh, data) -> Tuple[bool, str]:
    """Insert vào nhan_than (fallback)"""

def delete_quan_he_graph(db, cccd_chinh, edge_id) -> bool:
    """Xóa edge + auto-clean nháp mồ côi (Cách 2)"""

def delete_quan_he_satellite(db, item_id) -> bool:
    """Như delete_nhan_than cũ"""

def preview_cccd(db, cccd) -> Dict:
    """HTMX endpoint trả {has_profile, ho_ten, is_draft, autofill_data}"""

def _chuan_hoa_cap(cccd_a, cccd_b, loai) -> Tuple[str, str, str]:
    """
    Đối xứng: trả (min, max, loai)
    Có hướng: trả nguyên (cccd_a, cccd_b, loai)
    """

def _is_orphan_draft(db, cccd) -> bool:
    """is_draft=True AND không edge AND không satellite"""
```

**Logic auto-clean trong `delete_quan_he_graph`:**
```python
edge = db.get(QuanHeDoiTuong, edge_id)
cccd_doi_tac = edge.cccd_2 if edge.cccd_1 == cccd_chinh else edge.cccd_1
db.delete(edge); db.commit()

dt = db.get(DoiTuong, cccd_doi_tac)
if dt and dt.is_draft and _is_orphan_draft(db, cccd_doi_tac):
    db.delete(dt); db.commit()
```

**Test:** Tạo file `tests/test_quan_he_service.py` test các case: add, query, delete edge, auto-clean orphan, không xóa nếu không phải orphan.

---

### T1.4 — Routes `routes/quan_he.py` (file mới)
**File:** `backend/routes/quan_he.py` (TẠO MỚI), mount trong `backend/main.py`
**Endpoints:**
- `POST /profile/{cccd}/quan-he/graph` — form có CCCD
- `POST /profile/{cccd}/quan-he/satellite` — form không CCCD
- `DELETE /profile/{cccd}/quan-he/graph/{edge_id}`
- `DELETE /profile/{cccd}/quan-he/satellite/{item_id}`
- `GET /profile/{cccd}/quan-he/preview-cccd?cccd=...` — HTMX banner + autofill

**Lưu ý:**
- Validate CCCD đầu mỗi handler bằng `_cccd_dep` (đã có trong `routes/profile.py:78`).
- Cấm self-relation: `cccd_doi_tac == cccd_chinh` → trả banner đỏ.
- Toast qua `HX-Trigger` (theo `[UI-1]`).
- Apply [SEC-1], [ENV-1].

---

### T1.5 — Template `_tab_quan_he.html` (file mới, thay `_tab_nhan_than.html`)
**File:** `frontend/templates/profile/_tab_quan_he.html` (TẠO MỚI)
**Tham khảo template cũ:** `frontend/templates/profile/_tab_nhan_than.html`
**Cấu trúc:**
- Alpine.js `x-data="{mode: '', preview: null}"` toggle 2 block.
- Block "Có CCCD": ô CCCD `hx-get="/profile/{cccd}/quan-he/preview-cccd"` `hx-trigger="blur changed"` → trả banner xanh/vàng.
- Autofill: dùng `hx-swap-oob="true"` để fill nhiều ô cùng lúc khi preview.
- Block "Không CCCD": form đơn (ho_ten, quoc_tich, mo_ta).
- Bảng list: render từng item theo `item.type`:
  - `graph`: `<a href="/profile/{cccd_doi_tac}">` + badge "🔗 Hồ sơ", thêm badge "🟡 Nháp" nếu `is_draft`.
  - `satellite`: badge "📝 Ghi chú", không link.
- Nhãn quan hệ: dùng `get_quan_he_label(loai, vi_tri)` đã làm ở T1.1.

**Tuân thủ [UI-1]:** dùng class glassmorphism `bg-white/70 backdrop-blur-md`, không alert/confirm browser.

---

### T1.6 — Cập nhật profile route và tab-dispatch
**File:** `backend/routes/profile.py:140`
**Việc cần làm:**
- Sửa `template_map`: `"quan-he": "profile/_tab_quan_he.html"`.
- Giữ alias `"nhan-than"` 1 thời gian (trỏ sang template mới) để link cũ không vỡ.
- Endpoint cũ `POST/DELETE /profile/{cccd}/nhan-than` (`profile.py:187-207`): **xóa hẳn** (đã có endpoint mới ở T1.4 thay thế).
- `services/profile.py::get_profile_full` (`profile.py:48`): trường `nhan_than` → đổi thành `quan_he`, gọi `quan_he_svc.get_quan_he_full(db, cccd)`.

---

### T1.7 — Cập nhật điều hướng tab
**File:** `frontend/templates/profile/index.html`
**Việc cần làm:**
- Đổi label tab "Nhân thân" → "**Quan hệ**".
- Đổi `hx-get` URL từ `/tab/nhan-than` → `/tab/quan-he`.

---

### T1.8 — Cập nhật export DOCX và báo cáo Excel
**Files:**
- `backend/services/docx_export.py:144-148` — phần "Thân nhân" đổi tên "Quan hệ", merge graph + satellite.
- `backend/routes/bao_cao.py:454-482` — sheet "Nhân thân" → "Quan hệ", thêm cột "Loại nguồn".
- `backend/routes/bao_cao.py:682` — giữ `joinedload(DoiTuong.nhan_than)`, thêm load edge từ `quan_he_doi_tuong`.

---

### T1.9 — Tailwind rebuild + verify cuối
**Việc cần làm:**
1. **Anh tự chạy:** `npx tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css`
2. **Verify checklist:**
   - [ ] [SEC-1] không `import sqlite3` chuẩn ở code mới
   - [ ] [SEC-1] dùng `from sqlcipher3 import dbapi2 as sqlite3`
   - [ ] [SEC-1] PRAGMA key không bị xóa
   - [ ] [ENV-1] không thêm `secure=True` cho cookie
   - [ ] [UI-1] dùng HTMX + Alpine, không `alert()`/`confirm()`
   - [ ] [UI-1] giữ class glassmorphism nền
   - [ ] [PKG-1] đường dẫn dùng absolute từ `settings.BASE_DIR`, không dùng `sys._MEIPASS`
3. **Test functional:**
   - [ ] Tạo quan hệ với CCCD mới → có hồ sơ mới?
   - [ ] Tạo quan hệ với CCCD đã tồn tại → autofill hiển thị đúng?
   - [ ] Tạo quan hệ không CCCD → vào `nhan_than`?
   - [ ] Xóa quan hệ với hồ sơ nháp mồ côi → tự dọn?
   - [ ] Xóa quan hệ với hồ sơ KHÔNG mồ côi → giữ nguyên hồ sơ?
   - [ ] Mở hồ sơ B → thấy edge ngược chiều với nhãn đúng?
   - [ ] Self-loop bị chặn?
   - [ ] Edge trùng bị chặn?
   - [ ] Export DOCX có phần Quan hệ?
   - [ ] Báo cáo Excel có sheet Quan hệ?

---

## 6. SPRINT 2 — Sửa CCCD (Hướng A + C) — *làm sau Sprint 1*

### T2.1 — Tạo bảng `cccd_history`
**File:** `backend/models/models.py`
**Schema:**
```python
class CCCDHistory(Base):
    __tablename__ = "cccd_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cccd_cu: Mapped[str] = mapped_column(String, index=True)
    cccd_moi: Mapped[str] = mapped_column(String, index=True)
    doi_tuong_cccd_hien_tai: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd"))
    ly_do: Mapped[Optional[str]] = mapped_column(Text)
    nguoi_thuc_hien: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### T2.2 — Service `change_cccd(old, new, ly_do, user)`
**File:** `backend/services/profile.py`
**Logic:**
```python
def change_cccd(db, old_cccd, new_cccd, ly_do, user):
    validate_cccd(old_cccd); validate_cccd(new_cccd)
    if db.get(DoiTuong, new_cccd):
        return False, "CCCD mới đã tồn tại trong hệ thống"

    BEGIN
        # 1. Insert hồ sơ mới với cccd mới (copy field từ cũ)
        # 2. UPDATE từng bảng FK (LienHe, TaiChinh, PhuongTien, NhanThan,
        #    HoSoDacThu, TaiLieu, QuaTrinhHoatDong) SET cccd=new
        # 3. UPDATE QuanHeDoiTuong SET cccd_1=new WHERE cccd_1=old
        # 4. UPDATE QuanHeDoiTuong SET cccd_2=new WHERE cccd_2=old
        # 5. Insert CCCDHistory
        # 6. Đổi tên: data/uploads/avatars/<old> → <new>, docs/<old> → <new>
        # 7. UPDATE TaiLieu.duong_dan thay path
        # 8. DELETE DoiTuong WHERE cccd=old
        # 9. AuditLog
    COMMIT  # rollback toàn bộ + xóa thư mục mới nếu lỗi
```
**Lưu ý:** filesystem rename phải có rollback handler nếu DB transaction fail.

### T2.3 — Route + UI sửa CCCD
- Endpoint `POST /profile/{cccd}/change-cccd` — admin only (`require_admin`).
- Modal Alpine.js trên `_tab_basic.html`: nút "🔧 Sửa CCCD" → modal:
  - Nhập CCCD mới
  - Nhập lý do
  - Gõ lại CCCD mới để xác nhận
  - Cảnh báo "Hành động không thể hoàn tác"
- Sau khi đổi: `HX-Redirect` sang `/profile/{new_cccd}`.

### T2.4 — Tra cứu theo CCCD cũ
- Sửa `services/search.py`: khi tìm CCCD không thấy → query `cccd_history.cccd_cu` → redirect.

---

## 7. SPRINT 3 — Migration dữ liệu cũ — *làm khi sẵn sàng*

### T3.1 — Script `tools/migrate_nhan_than_to_graph.py`
**Logic:**
```
Cảnh báo: "Backup DB trước khi chạy! (cp data.db data.db.bak)"
Loop từng row nhan_than:
  if validate_cccd(row.cccd_nhan_than) OK:
    upsert DoiTuong(cccd=cccd_nhan_than, ho_ten, ngay_sinh, ..., is_draft=...)
    insert QuanHeDoiTuong(cccd_1=row.cccd, cccd_2=cccd_nhan_than, loai_quan_he=...)
    DELETE row nhan_than
  else:
    giữ nguyên (đúng phương án C)
```
**Flags:** `--dry-run` (chỉ log), `--commit` (thực thi).

### T3.2 — Nâng cấp bulk_import
**File:** `backend/utils/bulk_import/bulk_import/importers.py:133`
- Nếu cột "CCCD nhân thân" trong Excel hợp lệ → tạo edge (như T1.3).
- Không hợp lệ → giữ insert vào `nhan_than` như cũ.

---

## 8. SPRINT 4 — Vẽ mạng lưới (roadmap tương lai)

### T4.1 — Endpoint JSON `/api/network/{cccd}?depth=N`
- BFS từ `cccd` qua `quan_he_doi_tuong`, max depth 3, max 100 nodes.
- Trả `{nodes:[{cccd, ho_ten, is_draft}], links:[{source, target, label, do_tin_cay}]}` chuẩn ECharts.

### T4.2 — Tab "Mạng lưới" trên hồ sơ
- ECharts force-directed graph.
- Click node → mở hồ sơ.
- Filter theo loại quan hệ (chỉ "Vợ chồng + Cha-Con" = cây gia đình).

### T4.3 — Endpoint mạng lưới toàn cục
- `/network` — view all với filter địa bàn / nghề nghiệp.

---

## 9. THỨ TỰ THỰC HIỆN ĐỀ XUẤT

```
Sprint 1 (T1.1 → T1.9) — 1-2 ngày làm
   ↓
Test kỹ trên môi trường dev
   ↓
Deploy
   ↓
Sprint 2 (T2.1 → T2.4) — 1 ngày làm
   ↓
Sprint 3 (T3.1 → T3.2) — vài giờ + backup DB
   ↓
Sprint 4 (T4.1 → T4.3) — khi có thời gian
```

---

## 10. CHECKLIST TRƯỚC KHI BẮT ĐẦU CODE

- [ ] Đã backup DB hiện tại (`cp data/vcfe.db data/vcfe.db.backup-YYYYMMDD`)
- [ ] Đang ở branch `claude/auto-create-profile-relationship-PBkZr`
- [ ] Đã pull mới: `git pull origin claude/auto-create-profile-relationship-PBkZr`
- [ ] Đã xem lại file này 1 lượt

---

## 11. CÁC FILE SẼ ĐỤNG ĐẾN (TỔNG HỢP)

### Sprint 1 (Tab Quan hệ)
- ✏️ Sửa: `backend/constants.py` (T1.1)
- ✏️ Sửa: `backend/models/models.py` (T1.2)
- ✏️ Sửa: `backend/db/session.py` (T1.2)
- 🆕 Tạo: `backend/services/quan_he.py` (T1.3)
- 🆕 Tạo: `backend/routes/quan_he.py` (T1.4)
- 🆕 Tạo: `frontend/templates/profile/_tab_quan_he.html` (T1.5)
- ✏️ Sửa: `backend/main.py` (mount router, T1.4)
- ✏️ Sửa: `backend/routes/profile.py` (T1.6)
- ✏️ Sửa: `backend/services/profile.py` (T1.6)
- ✏️ Sửa: `frontend/templates/profile/index.html` (T1.7)
- ✏️ Sửa: `backend/services/docx_export.py` (T1.8)
- ✏️ Sửa: `backend/routes/bao_cao.py` (T1.8)
- 🆕 Tạo: `tests/test_quan_he_service.py` (T1.3)
- 🗑️ Xóa cuối sprint: `frontend/templates/profile/_tab_nhan_than.html` (sau khi alias không cần nữa)

### Sprint 2 (Sửa CCCD)
- ✏️ Sửa: `backend/models/models.py` (T2.1)
- ✏️ Sửa: `backend/services/profile.py` (T2.2)
- ✏️ Sửa: `backend/routes/profile.py` (T2.3)
- ✏️ Sửa: `frontend/templates/profile/_tab_basic.html` (T2.3)
- ✏️ Sửa: `backend/services/search.py` (T2.4)

### Sprint 3 (Migration)
- 🆕 Tạo: `tools/migrate_nhan_than_to_graph.py` (T3.1)
- ✏️ Sửa: `backend/utils/bulk_import/bulk_import/importers.py` (T3.2)

### Sprint 4 (Network)
- 🆕 Tạo: `backend/routes/network.py` (T4.1)
- 🆕 Tạo: `frontend/templates/profile/_tab_mang_luoi.html` (T4.2)
- 🆕 Tạo: `frontend/templates/network/index.html` (T4.3)

---

## 12. CÂU HỎI MỞ KHI THỰC HIỆN (anh trả lời sau khi đi công tác về)

1. Có muốn em làm tuần tự T1.1 → T1.9 và báo cáo sau mỗi task không, hay làm 1 mạch rồi báo cáo cuối?
2. Sprint 2 (Sửa CCCD) — có giới hạn chỉ super_admin được sửa, hay cả admin thường?
3. Sprint 3 (Migration) — có muốn em viết thêm script "rollback" để hoàn tác migration nếu phát hiện sai sót không?
4. Sprint 4 (Network) — ECharts hay thư viện khác (D3, Cytoscape)? Em đề xuất ECharts vì project đã có sẵn theo `[Tech Stack]`.

---

## 13. GHI CHÚ VỀ AN TOÀN

Tuân thủ tuyệt đối các quy tắc trong `.claude/CLAUDE.md`:
- **[SEC-1]**: SQLCipher, NullPool, không xóa `PRAGMA key`.
- **[ENV-1]**: localhost, không `secure=True` cookie.
- **[UI-1]**: HTMX + Alpine, không framework JS nặng, không `alert()`/`confirm()` mặc định.
- **[PKG-1]**: đường dẫn tuyệt đối từ `settings.BASE_DIR`, không `sys._MEIPASS`.
- **[KCG-2]**: viết code tối thiểu, không trừu tượng hóa sớm.
- **[KCG-3]**: surgical changes, không refactor code không liên quan.

---

**Hết kế hoạch.** File này được lưu trong git. Khi anh quay lại từ công tác:
```bash
cd /path/to/csxh-pa01-v1
git checkout claude/auto-create-profile-relationship-PBkZr
git pull
cat docs/PLAN_QUAN_HE.md   # Đọc lại
# Sau đó nhắn Claude: "Bắt đầu Sprint 1 - làm tuần tự"
```
