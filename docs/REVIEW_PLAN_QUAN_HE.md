# ĐÁNH GIÁ CHI TIẾT KẾ HOẠCH: Quan hệ & Auto tạo hồ sơ

> **Tài liệu gốc:** [PLAN_QUAN_HE.md](file:///d:/Github/csxh-pa01-v1/docs/PLAN_QUAN_HE.md)
> **Ngày đánh giá:** 2026-05-10
> **Người đánh giá:** Antigravity (AI Assistant)

---

## 1. TỔNG QUAN
Kế hoạch được lập rất chi tiết, có lộ trình rõ ràng (4 Sprint) và tuân thủ chặt chẽ các quy tắc an toàn hệ thống (`[SEC-1]`, `[ENV-1]`, `[UI-1]`). Kiến trúc **Hybrid (Graph + Satellite)** là điểm sáng nhất, giải quyết được sự linh hoạt giữa dữ liệu định danh (CCCD) và dữ liệu mô tả (người nước ngoài/không rõ lai lịch).

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| **Độ hoàn chỉnh** | 9/10 | Rất chi tiết, có cả wireframe và logic code |
| **Tính khả thi** | Cao | Các công nghệ sử dụng (SQLite, HTMX, Alpine) đã có sẵn |
| **Rủi ro kỹ thuật** | Trung bình | Chủ yếu nằm ở Sprint 2 (Sửa CCCD) và Migration |

---

## 2. CÁC ĐIỂM CẦN LƯU Ý KỸ THUẬT (CRITICAL)

### 🔴 Cao - Cần xử lý ngay trong Sprint 1 & 2

1. **Race Condition (T1.3):**
   - Đoạn logic `get` → `if not` → `create` không atomic. Nếu 2 request đồng thời tạo cùng 1 CCCD mới, có thể gây lỗi `UNIQUE constraint`.
   - **Giải pháp:** Sử dụng `try...except IntegrityError` hoặc cơ chế `ON CONFLICT DO NOTHING` của SQLite.

2. **Thứ tự Filesystem Rollback (T2.2):**
   - Việc đổi tên thư mục (`uploads/`) phải thực hiện **SAU khi COMMIT DB**.
   - **Rủi ro:** Nếu đổi tên trước mà DB fail → DB trỏ về path cũ nhưng file đã nằm ở path mới → mất liên kết dữ liệu.

3. **Stale Read trong `_is_orphan_draft`:**
   - Sau khi xóa edge, cần `db.flush()` hoặc `db.refresh()` đối tượng `DoiTuong` trước khi kiểm tra trạng thái "mồ côi" để tránh đọc cache cũ từ ORM.

---

### 🟡 Trung bình - Đề xuất bổ sung

4. **Bảo mật Endpoint Preview (T1.4):**
   - Endpoint `preview-cccd` cần được bảo vệ bởi middleware `require_login` để tránh việc kẻ xấu brute-force dò tìm danh sách CCCD có trong hệ thống.

5. **Chốt thư viện Đồ thị (Sprint 4):**
   - Đề xuất chốt luôn **ECharts** (theo tech stack hiện tại) để format JSON của API ở Sprint 1 đồng nhất với yêu cầu của frontend sau này.

6. **Giới hạn quy mô mạng lưới (T4.1):**
   - Ngoài `depth=3`, cần giới hạn tổng số node/edge tối đa (ví dụ: `max_nodes=100`, `max_edges=200`) để tránh treo trình duyệt khi gặp các hồ sơ có quan hệ cực kỳ phức tạp.

---

## 3. CHECKLIST BỔ SUNG CHO T1.9 (VERIFY)

Cần thêm các bước test sau vào giai đoạn cuối Sprint 1:
- [ ] **Test đồng thời:** 2 tab trình duyệt cùng tạo 1 hồ sơ quan hệ mới cùng lúc.
- [ ] **Test quyền truy cập:** Thử gọi endpoint `preview-cccd` khi chưa đăng nhập.
- [ ] **Test xóa đảo chiều:** Xóa quan hệ từ phía "người được liên kết" (B) thay vì "người chủ động" (A).
- [ ] **Test mồ côi:** Đảm bảo hồ sơ `is_draft=False` (chính thức) **KHÔNG bao giờ** bị xóa tự động kể cả khi không còn quan hệ.

---

## 4. PHẢN HỒI CÂU HỎI MỞ (Mục 12 của Kế hoạch)

1. **Tuần tự hay một mạch:** Nên làm tuần tự và báo cáo sau mỗi Task lớn (T1.1, T1.2...) để dễ dàng điều chỉnh UI/UX theo ý anh.
2. **Quyền sửa CCCD (Sprint 2):** Đề xuất chỉ **super_admin** mới có quyền này vì nó ảnh hưởng đến toàn bộ tính toàn vẹn của dữ liệu và hệ thống tệp tin.
3. **Rollback Migration (Sprint 3):** Rất cần thiết. Việc backup DB là bắt buộc, nhưng script rollback sẽ giúp xử lý nhanh nếu chỉ một phần dữ liệu bị sai.
4. **Thư viện đồ thị:** Chốt **ECharts**.

---

> [!IMPORTANT]
> **Khuyến nghị:** Bắt đầu Sprint 1 với Task T1.1 và T1.2 trước để định hình lại hệ thống nhãn quan hệ và cấu trúc bảng mới.

**Antigravity**
