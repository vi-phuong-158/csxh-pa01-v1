# Sửa lỗi Nhập liệu: Tab switching, Lưu dữ liệu, Hồ sơ đặc thù, Uppercase tên

## Tổng quan vấn đề

Có **6 lỗi chính** trong giao diện nhập liệu:

1. **Tab switching mất dữ liệu "Thông tin cơ bản"** — Khi chuyển tab rồi quay lại, nội dung basic tab bị mất
2. **Nhân thân không lưu được / dropdown không hoạt động**
3. **Liên hệ, Tài chính, Phương tiện không lưu được**
4. **Hồ sơ đặc thù thiếu nhiều trường** — Chỉ có "Loại hình" + "Nội dung chi tiết", cần thêm các trường riêng theo từng loại hình
5. **Loại hình hiển thị mã code** — Cần hiện tiếng Việt đầy đủ
6. **Họ tên cần tự động viết in hoa**

---

## Phân tích nguyên nhân gốc

### Bug 1: Tab switching mất "Thông tin cơ bản"

Trong [form.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/nhap_lieu/form.html#L26-L42):

```html
<div id="tab-content">
  <div x-show="activeTab==='basic'">
    {% include "profile/_tab_basic.html" %}
  </div>
</div>
```

Khi click tab khác, HTMX load nội dung vào `#tab-content` → **ghi đè toàn bộ** bao gồm cả basic div. Khi quay lại basic, div đó đã bị xóa.

**Cần sửa**: Tách `#tab-content` thành 2 vùng: `basic` luôn tồn tại (ẩn/hiện) + `#dynamic-tab-content` cho các tab HTMX.

### Bug 2 & 3: Nhập liệu satellite tables không lưu được

Trong [form.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/nhap_lieu/form.html#L29-L32), tab non-basic load URL:
```
/profile/{{ profile.cccd }}/tab/{{ id }}
```

Các tab template (nhan_than, lien_he, tai_chinh...) đều `hx-post` tới:
```
/profile/{{ profile.cccd }}/nhan-than
```

Nhưng route `/profile/{cccd}/nhan-than` yêu cầu `require_profile_access` (kiểm tra quyền phụ trách). Nếu hồ sơ đang ở trạng thái **draft** (is_draft=True) thì route nhập liệu (`/nhap-lieu/`) nên xử lý. Tuy nhiên các route POST satellite đều nằm dưới `/profile/`, nên cần xác nhận chúng hoạt động đúng.

Vấn đề thực sự: Các tab template dùng `hx-target="#dynamic-tab-content"` nhưng trong `nhap_lieu/form.html`, target div là `#tab-content` — **không khớp ID**.

### Bug 4: Hồ sơ đặc thù thiếu trường

Theo spec từ codebase Streamlit cũ, mỗi `loai_hinh` cần form riêng:

| Loại hình | Trường cần có |
|-----------|---------------|
| **Hon_Nhan_NN** | Họ tên đối tác, Quốc tịch, Số hộ chiếu, Tình trạng |
| **Lam_Viec_NN** | Tên tổ chức, Chức vụ, Thời gian, Địa điểm |
| **Hoc_Tap_Cong_Tac_NN** | Diện đi, Quốc gia, Thời gian đi, Thời gian về, Nghề sau về |
| **Vi_Pham_NN** | Quốc gia, Cơ quan bắt, Ngày vi phạm, Hình thức xử lý, Nội dung VP |
| **Xac_Minh** | Cơ quan XM, Ngày XM, Kết quả, Nội dung XM |

Hiện tại form chỉ có 1 dropdown + 1 textarea → cần xây dựng form động thay đổi theo loại hình, lưu vào `noi_dung_chi_tiet` dạng JSON.

### Bug 5: Loại hình hiển thị mã code

`LOAI_HINH_DAC_THU` đã là dict `{"Hon_Nhan_NN": "Kết hôn/sống chung..."}` nhưng template dropdown chỉ dùng `{{ lh }}` → hiện key (mã), cần hiện value (tiếng Việt).

### Bug 6: Họ tên tự động in hoa

Cần thêm `style="text-transform: uppercase"` và xử lý backend `.upper()`.

---

## Proposed Changes

### Frontend - Tab system fix

#### [MODIFY] [form.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/nhap_lieu/form.html)

- Tách layout thành 2 vùng: basic (luôn render) + `#dynamic-tab-content` (HTMX load)
- Khi click "Thông tin cơ bản" → show basic, hide dynamic
- Khi click tab khác → hide basic, show dynamic + HTMX load

---

### Frontend - Hồ sơ đặc thù form

#### [MODIFY] [_tab_ho_so_dac_thu.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/profile/_tab_ho_so_dac_thu.html)

- Thay dropdown + textarea bằng form động Alpine.js
- Mỗi loại hình có bộ trường riêng, hiển thị/ẩn theo `x-show`
- Dữ liệu chi tiết serialize thành JSON trước khi gửi

---

### Frontend - Loại hình hiển thị tiếng Việt

#### [MODIFY] [_tab_ho_so_dac_thu.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/profile/_tab_ho_so_dac_thu.html)

- Dropdown: `<option value="{{ key }}">{{ value }}</option>` thay vì `<option>{{ lh }}</option>`
- Hiển thị existing: dùng dict lookup label

---

### Frontend - Tên viết in hoa

#### [MODIFY] [_tab_basic.html](file:///d:/Code/csxh-pa01-v1/frontend/templates/profile/_tab_basic.html)

- Thêm `style="text-transform: uppercase"` cho input `ho_ten`

---

### Backend - Service xử lý tên in hoa

#### [MODIFY] [profile.py](file:///d:/Code/csxh-pa01-v1/backend/services/profile.py)

- Trong `update_basic_info()`: `data["ho_ten"] = data["ho_ten"].upper()` trước khi lưu

---

### Backend - Truyền `LOAI_HINH_DAC_THU` dict + constants mới

#### [MODIFY] [constants.py](file:///d:/Code/csxh-pa01-v1/backend/constants.py)

- Thêm constants cho dropdown phụ: `DANH_SACH_QUOC_GIA`, `KET_QUA_XAC_MINH`, `HINH_THUC_DU_HOC`
- Truyền sang templates qua `_CTX_OPTS`

#### [MODIFY] [profile.py (routes)](file:///d:/Code/csxh-pa01-v1/backend/routes/profile.py)

- Thêm constants mới vào `_CTX_OPTS`

#### [MODIFY] [nhap_lieu.py (routes)](file:///d:/Code/csxh-pa01-v1/backend/routes/nhap_lieu.py)

- Thêm constants mới vào `_CTX_OPTS`

---

## Verification Plan

### Automated Tests
- Khởi chạy server `python run_server.py`
- Dùng browser test: nhập CCCD → vào form → chuyển tab → quay lại basic → verify dữ liệu còn
- Test thêm nhân thân, liên hệ, tài chính, phương tiện
- Test thêm hồ sơ đặc thù từng loại hình
- Verify dropdown hiện tiếng Việt
- Verify họ tên tự động in hoa
