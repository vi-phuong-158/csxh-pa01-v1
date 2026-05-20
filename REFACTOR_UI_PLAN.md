# REFACTOR UI PLAN — VCFED Frontend CAND Theme

> Trang thai: DANG THUC HIEN — Pha 0-3 HOAN THANH, chuan bi Pha 4
> Ngay bat dau: 2026-05-19
> Cap nhat lan cuoi: 2026-05-20
> Nguyen tac: CHI THAY DOI GIAO DIEN, GIU NGUYEN 100% LOGIC BACKEND

---

## QUYET DINH DA CHOT

| Hang muc | Quyet dinh |
|----------|-----------|
| Chien luoc CSS | Phuong an A: Them `cand-theme.css` override, load SAU `output.css` |
| Navigation menu | Giu nguyen menu hien tai (8 muc + admin), chi doi style |
| POC bat dau | Login + Dashboard |
| Stack | Van dung Jinja2 + HTMX + Alpine.js (TUYET DOI KHONG dung React) |

---

## NGUYEN TAC BAO VE (doc lai truoc moi pha)

1. **KHONG** dong vao bat ky file Python nao (routes/, services/, models/, schemas/)
2. **KHONG** doi ten URL endpoint, ten field POST, thuoc tinh name trong form
3. **GIU NGUYEN** tat ca `hx-get`, `hx-post`, `hx-target`, `hx-swap`, `hx-trigger`
4. **GIU NGUYEN** tat ca `x-data`, `x-show`, `x-text`, `x-on:*` cua Alpine.js
5. **GIU NGUYEN** bien Jinja: `{{ user.* }}`, `{{ stats.* }}`, `{{ flash_* }}`, `{{ request.state.csrf_token }}`
6. **GIU NGUYEN** toast system (HX-Trigger -> Alpine), CSRF injection, htmx-loader
7. Mau React (`new_frontend/`) chi la DESIGN REFERENCE — port sang Jinja2, KHONG be React vao

---

## PHA 0 — CHUAN BI (Khong dong template nao)

### Checklist:
- [x] 0.1 Copy `new_frontend/assets/logo-cand.png` -> `frontend/static/img/logo-cand.png`
- [x] 0.2 `trong-dong.png` da co san tai `frontend/static/img/` — KHONG can copy
- [x] 0.3 Tao `frontend/static/css/cand-theme.css` tu `new_frontend/styles.css`
      - Da sua duong dan asset: `url("assets/...")` -> `url("/static/img/...")`
      - Da scope class xung dot (.btn*, .nav-item, .badge*) duoi `.cand-ui`
      - Da doi ten toast/animation tranh trung: cand-toast, cand-pulse, cand-spin...
- [x] 0.4 Sua `base.html`:
      - Da them font Be Vietnam Pro + JetBrains Mono
      - Da them `<link rel="stylesheet" href="/static/css/cand-theme.css" />`
      - CHUA doi `<body>` class — dung ke hoach

### Verify Pha 0:
- [x] Chay app -> tat ca trang hien tai KHONG bi anh huong (CSS moi chua apply len gi)
- [x] File `cand-theme.css` load thanh cong (kiem tra DevTools)

---

## PHA 1 — POC: Login + Dashboard

### 1A. Login (`frontend/templates/auth/login.html`)

- [x] 1A.1 Doc `login.html` hien tai — ghi nhan cac element can giu:
      - `<form action="/auth/login" method="post">`
      - `<input name="username">`, `<input name="password">`
      - `<input type="hidden" name="_csrf" value="{{ request.state.csrf_token }}">`
      - Jinja blocks: `{% extends "base.html" %}`, `{% block content_no_auth %}`
- [x] 1A.2 Port giao dien theo `LoginScreen` trong `new_frontend/shell.jsx`:
      - Full-screen centered layout, trong-dong xoay lam nen
      - Login card giua man hinh voi nen do translucent
      - Logo CAND tren, ten he thong duoi, form dang nhap
- [x] 1A.3 Dam bao form POST van hoat dong dung
- [x] 1A.4 Dam bao flash_error/flash_success hien thi dung

### Verify 1A:
- [x] Dang nhap thanh cong voi tai khoan dung
- [x] Dang nhap that bai -> hien thong bao loi
- [x] Giao dien khop voi mau (full-screen, mau sac CAND)

### 1B. Dashboard (`frontend/templates/dashboard/index.html`)

- [x] 1B.1 Doc `dashboard/index.html` hien tai — ghi nhan:
      - Bien Jinja: `{{ stats.total }}`, `{{ stats.gioi_tinh }}`, `{{ stats.dac_thu }}`
      - ECharts: da co script voi chart ID
      - Cac link dieu huong: `/bao-cao`, `/tra-cuu`, `/profile/{{ r.cccd }}`
- [x] 1B.2 Port giao dien theo CAND theme classes:
      - Page header voi .page-header + .eyebrow + .sub + .page-header__actions
      - 4 stat tiles (.stats-grid + .stat-tile)
      - Grid 2 cot: Donut chart nghe nghiep + Bar chart dia ban (.card)
      - Bang ho so gan day (.card + .tbl)
      - Wrapper .cand-ui cho scoped classes (.btn, .pill)
- [x] 1B.3 ECharts: doi mau palette sang CAND_COLORS (red/gold/green)
- [x] 1B.4 Dam bao tat ca link dieu huong van dung URL cu

### Verify 1B:
- [x] Dashboard hien thi du lieu thuc tu backend (khong bi mat so lieu)
- [x] ECharts render dung
- [x] Cac nut "Xuat bao cao", "Nhap ho so moi" van hoat dong
- [x] Giao dien khop voi mau

---

## PHA 2 — Shell: base.html + sidebar + banner (SAU KHI PHA 1 OK)

- [x] 2.1 Tao `components/banner.html` moi (top banner do CAND)
      - Logo + ten don vi + notification bell (port tu header.html) + user info
      - Giu nguyen: user.ho_ten, user.role, vcfeHeader() Alpine logic, CSRF
- [x] 2.2 Refactor `components/sidebar.html`:
      - Doi tu glass dark -> paper kem (.sidebar style tu cand-theme.css)
      - GIU NGUYEN: nav_links, is_active logic, admin section, logout form
      - Them search box (placeholder, CHUA wire API)
      - Footer: hien thi trang thai ma hoa AES-256
- [x] 2.3 Refactor `base.html`:
      - Doi grid layout: .app-shell (banner 72px + sidebar 248px + main)
      - Doi body background tu dark -> paper kem (var(--paper))
      - Xoa orb divs, xoa header.html include, them banner.html include
      - Toast doi sang .cand-toast style, loading bar doi sang red-gold gradient
      - GIU NGUYEN: htmx-loader, toast-root, datalist, CSRF script, Alpine init
      - GIU NGUYEN: flash_success/flash_error logic
      - Watermark trong dong o .main::before (tu cand-theme.css)
- [x] 2.4 Verify TOAN BO trang (luot qua tung route):
      - /dashboard, /nhap-lieu, /nhap-excel, /tra-cuu, /ra-soat
      - /danh-ba, /network, /bao-cao, /lich-su-kien
      - /quan-ly-user, /nguon-du-lieu, /audit-log (admin)
      - /profile/<cccd>
      - Layout khong vo, sidebar/banner hien dung, noi dung chinh van hien

---

## PHA 2B — CSS Polish toan cuc (bo sung sau Pha 2)

> Thuc hien ngay 2026-05-20. Sua toan bo qua `cand-theme.css` LEGACY OVERRIDE,
> KHONG sua file template — ap dung global cho moi trang.

- [x] 2B.1 Fix contrast: nen trang + chu sang -> override tat ca .text-slate-*, .text-white/*
- [x] 2B.2 Fix input padding: chu sat vien -> padding 10px 14px, individual properties
- [x] 2B.3 Fix active menu: den+do -> nen do gradient + chu vang (.nav-item--active)
- [x] 2B.4 Fix card width: .max-w-sm 384px -> 480px, .max-w-md -> 560px trong .main
- [x] 2B.5 Fix card padding: .card, .glass-card, .glass-card-dark -> padding 24px
- [x] 2B.6 Fix dark dropdown: override .bg-slate-800 -> var(--card), .border-slate-600 -> var(--line)
- [x] 2B.7 Fix search icon overlap: .pl-7 -> padding-left 34px, dung :not([class*="pl-"]) exclusion
- [x] 2B.8 Cache bust: cand-theme.css?v=6

---

## PHA 3 — Trang nghiep vu (cluster 1) (SAU KHI PHA 2 OK)

- [x] 3.1 `tra_cuu/index.html` -> filter-bar + tbl style
- [x] 3.2 `nhap_lieu/index.html` + `nhap_lieu/form.html` -> form-grid + field style
- [x] 3.3 `nhap_excel/index.html` + `_results.html` -> drop-zone + progress style
- [x] 3.4 `danh_ba/index.html` + `_partials/danh_ba_results.html`
- [x] 3.5 Verify: tat ca form submit, HTMX partial reload van hoat dong

> Thuc hien boi Codex ngay 2026-05-20. Pham vi: chi refactor UI cac template Pha 3; giu nguyen backend, endpoint, field name, HTMX target/swap va partial reload. Verify da chay: Jinja parse/render, Python compileall, hook preservation, quet fetch/CDN/alert/confirm, node --check cho JS inline `tra_cuu`.

---

## PHA 4 — Ho so + Mang luoi (cluster 2) (SAU KHI PHA 3 OK)

- [ ] 4.1 `profile/index.html` -> profile-hero header
- [ ] 4.2 `profile/_tab_basic.html`
- [ ] 4.3 `profile/_tab_lien_he.html`
- [ ] 4.4 `profile/_tab_tai_chinh.html`
- [ ] 4.5 `profile/_tab_nhan_than.html`
- [ ] 4.6 `profile/_tab_phuong_tien.html`
- [ ] 4.7 `profile/_tab_ho_so_dac_thu.html`
- [ ] 4.8 `profile/_tab_tai_lieu.html`
- [ ] 4.9 `profile/_tab_qua_trinh.html`
- [ ] 4.10 `profile/_tab_mang_luoi.html`
- [ ] 4.11 `profile/_tab_quan_he.html`
- [ ] 4.12 `network/index.html` -> network-stage
- [ ] 4.13 `ra_soat/index.html` + `_results.html`
- [ ] 4.14 Verify: tab switching, HTMX partial load, modal xoa, form them/sua

---

## PHA 5 — He thong + phu tro (cluster 3) (SAU KHI PHA 4 OK)

- [ ] 5.1 `audit_log/index.html` -> tbl style, filter HTMX
- [ ] 5.2 `quan_ly_user/index.html` -> tbl + modal
- [ ] 5.3 `nguon_du_lieu/index.html`
- [ ] 5.4 `bao_cao/index.html` + `bao_cao_charts.js` (doi color palette)
- [ ] 5.5 `lich_su_kien/index.html`
- [ ] 5.6 `auth/change_password.html`
- [ ] 5.7 Verify: tat ca tinh nang admin hoat dong

---

## PHA 6 — Don dep & build (SAU KHI PHA 5 OK)

- [ ] 6.1 Xoa class cu khong con dung trong `input.css` (orb-1, orb-2, glass-*)
- [ ] 6.2 Chay Tailwind build: `npx tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css`
- [ ] 6.3 Kiem tra `build_app.bat` — dam bao asset moi duoc include
- [ ] 6.4 Build .exe va smoke test toan dien
- [ ] 6.5 Cap nhat CLAUDE.md: doi "Glassmorphism" -> "Paper CAND" trong triet ly UX/UI

---

## FILE BI ANH HUONG (theo pha)

### Pha 0 (3 file):
- TAO MOI: `frontend/static/css/cand-theme.css`
- COPY: `frontend/static/img/logo-cand.png`
- SUA: `frontend/templates/base.html` (them link CSS + font)

### Pha 1 (2 file):
- SUA: `frontend/templates/auth/login.html`
- SUA: `frontend/templates/dashboard/index.html`

### Pha 2 (3 file):
- TAO MOI: `frontend/templates/components/banner.html`
- SUA: `frontend/templates/components/sidebar.html`
- SUA: `frontend/templates/base.html`

### Pha 3 (5 file):
- SUA: `frontend/templates/tra_cuu/index.html`
- SUA: `frontend/templates/nhap_lieu/index.html` + `form.html`
- SUA: `frontend/templates/nhap_excel/index.html` + `_results.html`
- SUA: `frontend/templates/danh_ba/index.html` + `_partials/danh_ba_results.html`

### Pha 4 (14 file):
- SUA: `frontend/templates/profile/index.html` + 10 tab files
- SUA: `frontend/templates/network/index.html`
- SUA: `frontend/templates/ra_soat/index.html` + `_results.html`

### Pha 5 (6 file):
- SUA: `frontend/templates/audit_log/index.html`
- SUA: `frontend/templates/quan_ly_user/index.html`
- SUA: `frontend/templates/nguon_du_lieu/index.html`
- SUA: `frontend/templates/bao_cao/index.html` + `bao_cao_charts.js`
- SUA: `frontend/templates/lich_su_kien/index.html`
- SUA: `frontend/templates/auth/change_password.html`

### Pha 6 (3 file):
- SUA: `frontend/static/css/input.css`
- REBUILD: `frontend/static/css/output.css`
- SUA: `.claude/CLAUDE.md`

---

## KHONG LAM (out of scope)

- Khong port `tweaks-panel.jsx` (tinh nang moi, khong phai refactor)
- Khong them route backend moi
- Khong doi ten URL bat ky endpoint nao
- Khong doi cau truc du lieu tra ve tu backend
- Khong them tinh nang "Danh sach doi tuong" (can route moi)
