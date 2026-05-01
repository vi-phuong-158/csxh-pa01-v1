# UI Patterns — VCFE Database

> Hệ thống giao diện Dark Glassmorphism, màu Olive Green (Material You).
> CSS được định nghĩa trong `frontend/static/css/input.css` và biên dịch ra `output.css`.
> **Không viết CSS inline.** Dùng các component class đã định nghĩa.

---

## Hệ màu cốt lõi (Custom Tailwind Colors)

| Token | Hex | Dùng khi nào |
|-------|-----|--------------|
| `primary` | `#c3cc8c` | Text nổi bật, border active |
| `primary-container` | `#4b5320` | Background nút chính, badge active |
| `secondary-container` | `#ffdb3c` | Vàng gold, loading bar |
| `error` | `#ffb4ab` | Text lỗi |
| `error-container` | `#93000a` | Background nút nguy hiểm |
| `background` | `#13140f` | Nền tổng |
| `on-background` | `#e5e2db` | Text mặc định |
| `surface-container` | `#20201b` | Nền card/panel |
| `surface-container-high` | `#2a2a25` | Nền nút secondary |
| `outline` | `#919283` | Text mờ, border yếu |
| `outline-variant` | `#47483c` | Divider |

---

## Component Classes (đã định nghĩa trong input.css)

### Glass Panels

```html
<!-- Panel kính mờ (Sidebar, Header, Dialog) -->
<div class="glass-panel rounded-xl p-6">...</div>

<!-- Thẻ metric nổi bật (Olive nhạt) -->
<div class="glass-card rounded-xl p-6">...</div>

<!-- Thẻ tối (Bảng biểu, Biểu đồ) -->
<div class="glass-card-dark rounded-xl p-6">...</div>
```

### Buttons

```html
<!-- Nút chính (Olive xanh) -->
<button class="btn-primary">
  <span class="material-symbols-outlined text-[18px]">save</span>
  Lưu
</button>

<!-- Nút phụ (Gray) -->
<button class="btn-secondary">Hủy</button>

<!-- Nút nguy hiểm (Đỏ) -->
<button class="btn-danger">
  <span class="material-symbols-outlined text-[18px]">delete</span>
  Xóa
</button>

<!-- Nút ghost (trong suốt) -->
<button class="btn-ghost">Bỏ qua</button>

<!-- Nút với HTMX loading state -->
<button class="btn-primary" hx-post="/api/..." hx-target="#result"
        hx-disabled-elt="this">
  <span class="htmx-indicator material-symbols-outlined text-[16px] animate-spin">autorenew</span>
  Xử lý
</button>
```

### Form Inputs

```html
<!-- Input chuẩn -->
<div class="mb-4">
  <label class="label">Họ và tên</label>
  <input type="text" name="ho_ten" class="input" placeholder="Nhập họ và tên...">
</div>

<!-- Select dropdown -->
<div class="mb-4">
  <label class="label">Giới tính</label>
  <select name="gioi_tinh" class="input">
    <option value="">-- Chọn --</option>
    <option value="Nam">Nam</option>
    <option value="Nữ">Nữ</option>
  </select>
</div>

<!-- Textarea -->
<div class="mb-4">
  <label class="label">Ghi chú</label>
  <textarea name="ghi_chu" class="input" rows="3"></textarea>
</div>

<!-- Input lỗi -->
<input type="text" class="input input-error">
<p class="text-error text-label-caps mt-1">Trường này bắt buộc</p>
```

### HTMX Form chuẩn

```html
<!-- Form POST với HTMX (CSRF tự động inject qua base.html script) -->
<form hx-post="/profile/{{ cccd }}/nhan-than"
      hx-target="#nhan-than-list"
      hx-swap="outerHTML"
      hx-on::after-request="if(event.detail.successful) this.reset()">
  <input type="text" name="ho_ten" class="input" required>
  <button type="submit" class="btn-primary">Thêm</button>
</form>

<!-- Form với indicator loading -->
<form hx-post="/nhap-excel/upload"
      hx-target="#result-area"
      hx-swap="innerHTML"
      hx-encoding="multipart/form-data"
      hx-indicator="#upload-spinner">
  <input type="file" name="file" accept=".xlsx,.xls">
  <div id="upload-spinner" class="htmx-indicator">Đang xử lý...</div>
  <button type="submit" class="btn-primary">Upload</button>
</form>

<!-- DELETE với confirm -->
<button hx-delete="/profile/{{ cccd }}/nhan-than/{{ item.id }}"
        hx-target="#row-{{ item.id }}"
        hx-swap="outerHTML swap:0.3s"
        hx-confirm="Xóa thân nhân này?"
        class="btn-danger">
  <span class="material-symbols-outlined text-[16px]">delete</span>
</button>
```

### Tabs (Alpine.js)

```html
<!-- Tab container -->
<div x-data="{ activeTab: 'nhan_than' }">
  <!-- Tab nav -->
  <div class="flex border-b border-outline-variant gap-1 overflow-x-auto">
    <button @click="activeTab = 'nhan_than'"
            :class="activeTab === 'nhan_than' ? 'tab-btn tab-btn-active' : 'tab-btn'">
      Thân nhân
    </button>
    <button @click="activeTab = 'lien_he'"
            :class="activeTab === 'lien_he' ? 'tab-btn tab-btn-active' : 'tab-btn'">
      Liên hệ
    </button>
  </div>

  <!-- Tab content (HTMX lazy load) -->
  <div x-show="activeTab === 'nhan_than'"
       hx-get="/profile/{{ cccd }}/tab/nhan_than"
       hx-trigger="revealed"
       hx-target="this"
       hx-swap="innerHTML">
    <div class="p-6 text-outline">Đang tải...</div>
  </div>
</div>
```

### Modal (Alpine.js)

```html
<div x-data="{ open: false }">
  <!-- Trigger -->
  <button @click="open = true" class="btn-primary">Thêm mới</button>

  <!-- Backdrop + Modal -->
  <div x-show="open"
       x-transition:enter="transition ease-out duration-200"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
       @click.self="open = false">
    <div class="glass-panel rounded-xl p-6 w-full max-w-lg mx-4"
         @click.stop>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-h3 font-semibold text-on-surface">Tiêu đề Modal</h3>
        <button @click="open = false" class="btn-ghost p-1">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <!-- Nội dung -->
      <div class="mt-4 flex justify-end gap-3">
        <button @click="open = false" class="btn-secondary">Hủy</button>
        <button class="btn-primary">Xác nhận</button>
      </div>
    </div>
  </div>
</div>
```

### Toast Notification (kích hoạt từ backend)

```python
# Backend: gửi toast qua HX-Trigger header
from fastapi.responses import HTMLResponse
import json

response = HTMLResponse(content=partial_html)
response.headers["HX-Trigger"] = json.dumps({
    "showToast": {"type": "success", "msg": "Đã lưu thành công!"}
})
# hoặc type: "error"
```

```javascript
// Frontend: kích hoạt toast thủ công từ JS
window.dispatchEvent(new CustomEvent('show-toast', {
  detail: { type: 'success', msg: 'Thao tác thành công!' }
}));
// type: 'success' | 'error'
```

### Badges / Status Pills

```html
<span class="badge-active">Hoạt động</span>
<span class="badge-warning">Cần xem lại</span>
<span class="badge-alert">Lỗi</span>
<span class="badge-gray">Không rõ</span>
<span class="badge-green">Đã xác minh</span>
```

### Navigation Item (Sidebar)

```html
<!-- Item bình thường -->
<a href="/dashboard" class="nav-item">
  <span class="material-symbols-outlined text-[20px]">dashboard</span>
  Dashboard
</a>

<!-- Item đang active -->
<a href="/dashboard" class="nav-item nav-item-active">
  <span class="material-symbols-outlined text-[20px]" style="font-variation-settings:'FILL' 1;">dashboard</span>
  Dashboard
</a>
```

### Card / Section Header

```html
<!-- Section header chuẩn -->
<div class="flex items-center justify-between mb-6">
  <h2 class="text-h3 font-semibold text-on-surface flex items-center gap-2">
    <span class="material-symbols-outlined text-primary" style="font-variation-settings:'FILL' 1;">person</span>
    Tiêu đề
  </h2>
  <button class="btn-primary">Thêm mới</button>
</div>
```

### Table

```html
<div class="glass-card-dark rounded-xl overflow-hidden">
  <table class="table-auto w-full">
    <thead>
      <tr>
        <th>Họ tên</th>
        <th>Số CCCD</th>
        <th>Thao tác</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.ho_ten }}</td>
        <td class="font-code text-code">{{ item.cccd }}</td>
        <td>
          <a href="/profile/{{ item.cccd }}" class="btn-ghost text-xs">Chi tiết</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

### Icons (Material Symbols)

```html
<!-- Icon filled -->
<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">home</span>

<!-- Icon outlined (default) -->
<span class="material-symbols-outlined">home</span>

<!-- Icon có màu primary -->
<span class="material-symbols-outlined text-primary text-[20px]">check_circle</span>
```

---

## Layout chuẩn của một trang nội dung

```html
{% extends "base.html" %}
{% block title %}Tên trang - VCFE{% endblock %}

{% block content %}
<div class="space-y-6">
  <!-- Page header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-h3 font-semibold text-on-surface">Tên trang</h1>
      <p class="text-outline font-body-md mt-1">Mô tả ngắn</p>
    </div>
  </div>

  <!-- Nội dung chính -->
  <div class="glass-card-dark rounded-xl p-6">
    ...
  </div>
</div>
{% endblock %}
```

---

## Spacing chuẩn

| Class | Giá trị | Dùng khi nào |
|-------|---------|--------------|
| `p-container-padding` | 40px | Padding main content area |
| `gap-card-gap` | 24px | Gap giữa các card |
| `px-gutter` | 32px | Padding ngang section |
| `mt-section-margin` | 64px | Margin giữa các section lớn |
| `space-y-6` | 24px | Khoảng cách dọc giữa các block |
| `mb-4` | 16px | Margin dưới form field |
