# Toàn bộ mã nguồn dự án PA01

## app.py
```py
# -*- coding: utf-8 -*-
"""
SECURITY PROFILE 360
Hệ thống Quản trị An ninh PA01
Phiên bản: 1.0 (với Authentication)
"""

from views.audit_log import page_audit_log
from views.nguon_du_lieu import page_nguon_du_lieu
import streamlit as st
import logging
from pathlib import Path

# Import database module
from database import create_tables

# Import authentication
# Import authentication
from app.services.auth_service import init_super_admin, is_super_admin

# Import login views
from views.login import (
    require_login,
    show_user_menu,
    show_self_change_password,
    get_current_user
)

# Import views
from views import (
    page_dashboard,
    page_nhap_lieu,
    page_tra_cuu,
    page_profile_view,
    page_ra_soat,
    page_nhap_excel
)
from views.quan_ly_user import page_quan_ly_user

# ============================================
# LOGGING CONFIGURATION
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CẤU HÌNH TRANG
# ============================================
st.set_page_config(
    page_title="Security Profile 360",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# LOAD CSS
# ============================================


@st.cache_data
def load_css():
    """Load custom CSS file (cached for performance)"""
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


css_content = load_css()
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# ============================================
# KHỞI TẠO DATABASE & SUPER ADMIN
# ============================================
# Import new DB init
from app.init_db import init_db

@st.cache_resource
def init_database():
    """Khởi tạo database và Super Admin nếu chưa tồn tại"""
    # Use new SQLAlchemy init
    init_db()
    
    # Legacy init for backward compatibility if needed, or just use new auth service later
    # For now, we still need init_super_admin from auth.py which uses legacy DB access
    # ideally we refactor auth.py next.
    init_super_admin()
    return True


init_database()

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'current_cccd' not in st.session_state:
    st.session_state.current_cccd = None
if 'view_profile_cccd' not in st.session_state:
    st.session_state.view_profile_cccd = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False

# If form submitted, update last_active to prevent timeout during long entry
if st.session_state.form_submitted:
    st.session_state.last_active = time.time()

# ============================================
# SESSION TIMEOUT CHECK (30 minutes)
# ============================================
SESSION_TIMEOUT = 1800  # 30 minutes
import time

if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()

if st.session_state.logged_in:
    if time.time() - st.session_state.last_active > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.error("⚠️ Phiên làm việc đã hết hạn do không hoạt động. Vui lòng đăng nhập lại.")
        st.stop()
    else:
        # Update activity time
        st.session_state.last_active = time.time()

# ============================================
# AUTHENTICATION CHECK
# ============================================
if not require_login():
    # Nếu chưa đăng nhập hoặc cần đổi mật khẩu, dừng ở đây
    st.stop()

# ============================================
# SIDEBAR & NAVIGATION (Sau khi đăng nhập)
# ============================================

# Import thêm các trang admin

with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.error(f"Logo not found at {logo_path}")
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Security Profile PA01</h3>",
                unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #e0e0e0; font-weight: 600; font-size: 8px;'>HỆ THỐNG QUẢN LÝ HỒ SƠ CSXH</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Menu items based on role
    user = get_current_user()

    menu_items = ["Dashboard", "Nhập liệu", "Nhập Excel", "Tra cứu", "Rà soát"]

    # Thêm menu Admin cho Super Admin
    if is_super_admin(user):
        menu_items.append("---")  # Separator
        menu_items.append("👥 Quản lý tài khoản")
        menu_items.append("📦 Nguồn dữ liệu")
        menu_items.append("📜 Lịch sử thay đổi")

    # Filter out separator
    display_menu = [m for m in menu_items if m != "---"]

    menu = st.radio(
        "Menu chính",
        display_menu,
        index=0,
        key="main_menu"
    )

    # User menu (đổi mật khẩu, đăng xuất)
    show_user_menu()

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>Thiết kế bởi Vi Phương</div>",
                unsafe_allow_html=True)

# ============================================
# ROUTING LOGIC
# ============================================

# Nếu đang đổi mật khẩu (tự nguyện)
if st.session_state.get('show_change_password'):
    show_self_change_password()

# Xử lý điều hướng đặc biệt (Xem chi tiết hồ sơ)
elif st.session_state.view_profile_cccd:
    # AUDIT LOGGING: Log view action if new CCCD is viewed
    if st.session_state.get('last_viewed_cccd') != st.session_state.view_profile_cccd:
        from views.audit_log import add_audit_log
        user = get_current_user()
        username = user.get('username') if user else 'Unknown'
        add_audit_log(
            bang='doi_tuong',
            hanh_dong='VIEW',
            khoa_chinh=st.session_state.view_profile_cccd,
            du_lieu_cu='',
            du_lieu_moi='Xem chi tiết hồ sơ',
            nguoi_thuc_hien=username
        )
        st.session_state.last_viewed_cccd = st.session_state.view_profile_cccd
        
    page_profile_view(st.session_state.view_profile_cccd)

else:
    # Điều hướng theo menu sidebar
    if menu == "Dashboard":
        page_dashboard()
    elif menu == "Nhập liệu":
        page_nhap_lieu()
    elif menu == "Nhập Excel":
        page_nhap_excel()
    elif menu == "Tra cứu":
        page_tra_cuu()
    elif menu == "Rà soát":
        page_ra_soat()
    elif menu == "👥 Quản lý tài khoản":
        page_quan_ly_user()
    elif menu == "📦 Nguồn dữ liệu":
        page_nguon_du_lieu()
    elif menu == "📜 Lịch sử thay đổi":
        page_audit_log()
    else:
        page_dashboard()

```

## auth.py
```py
# -*- coding: utf-8 -*-
"""
Module Authentication - Security Profile 360
Xử lý đăng nhập, phân quyền, quản lý tài khoản
"""
import bcrypt
import sqlite3
import os
import secrets
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database import get_connection
import logging

logger = logging.getLogger(__name__)

# Roles
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_USER = 'user'

# Default Super Admin credentials
DEFAULT_ADMIN_USERNAME = 'admin'


def hash_password(password: str) -> str:
    """Mã hóa mật khẩu với bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Kiểm tra mật khẩu có đúng không."""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Xác thực đăng nhập.

    Returns:
        Dict với thông tin user nếu thành công, None nếu thất bại
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, ho_ten, role, is_active, must_change_password
            FROM users 
            WHERE username = ? AND is_active = 1
        """, (username,))

        row = cursor.fetchone()

        if row and verify_password(password, row['password_hash']):
            # Cập nhật last_login
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now(), row['id']))
            conn.commit()

            return {
                'id': row['id'],
                'username': row['username'],
                'ho_ten': row['ho_ten'] or row['username'],
                'role': row['role'],
                'must_change_password': bool(row['must_change_password'])
            }

        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        conn.close()


def create_user(
    username: str,
    password: str,
    ho_ten: str = "",
    role: str = ROLE_USER,
    must_change_password: bool = False
) -> Tuple[bool, str]:
    """
    Tạo tài khoản mới.

    Returns:
        (success, message)
    """
    if not username or not password:
        return False, "Username và password không được trống"

    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Kiểm tra username đã tồn tại chưa
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, f"Username '{username}' đã tồn tại"

        # Tạo user mới
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, ho_ten, role, must_change_password)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, ho_ten, role, int(must_change_password)))

        conn.commit()
        logger.info(f"Đã tạo user: {username} (role: {role})")
        return True, f"Đã tạo tài khoản '{username}' thành công"

    except Exception as e:
        logger.error(f"Lỗi tạo user: {e}")
        return False, f"Lỗi tạo tài khoản: {e}"
    finally:
        conn.close()


def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    Xóa tài khoản (soft delete - set is_active = 0).

    Returns:
        (success, message)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Không cho xóa super_admin cuối cùng
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE role = ? AND is_active = 1 AND id != ?
        """, (ROLE_SUPER_ADMIN, user_id))

        admin_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT role, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            return False, "Không tìm thấy tài khoản"

        if user['role'] == ROLE_SUPER_ADMIN and admin_count == 0:
            return False, "Không thể xóa Super Admin cuối cùng"

        # Soft delete
        cursor.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()

        logger.info(f"Đã xóa user: {user['username']}")
        return True, f"Đã xóa tài khoản '{user['username']}'"

    except Exception as e:
        logger.error(f"Lỗi xóa user: {e}")
        return False, f"Lỗi xóa tài khoản: {e}"
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Đổi mật khẩu."""
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        password_hash = hash_password(new_password)

        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, must_change_password = 0
            WHERE id = ?
        """, (password_hash, user_id))

        conn.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        logger.error(f"Lỗi đổi mật khẩu: {e}")
        return False, f"Lỗi đổi mật khẩu: {e}"
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    """Lấy danh sách tất cả users (chỉ active)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, ho_ten, role, created_at, last_login
            FROM users 
            WHERE is_active = 1
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách users: {e}")
        return []
    finally:
        conn.close()


def init_super_admin():
    """
    Tạo Super Admin mặc định nếu chưa có user nào.
    Được gọi khi khởi động app.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Kiểm tra đã có user nào chưa
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        if count == 0:
            # Get password from env or generate random
            env_password = os.environ.get('ADMIN_PASSWORD')
            if env_password:
                password = env_password
                is_generated = False
            else:
                password = secrets.token_urlsafe(16)
                is_generated = True

            # Tạo super admin mặc định
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, ho_ten, role, must_change_password)
                VALUES (?, ?, ?, ?, ?)
            """, (
                DEFAULT_ADMIN_USERNAME,
                password_hash,
                'Administrator',
                ROLE_SUPER_ADMIN,
                1  # Bắt buộc đổi mật khẩu lần đầu
            ))
            conn.commit()
            logger.info(f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")

            if is_generated:
                print("="*60)
                print(f"[SECURITY NOTICE] Generated Random Super Admin Password")
                print(f"Username: {DEFAULT_ADMIN_USERNAME}")
                print(f"Password: {password}")
                print(f"Please change this password immediately after logging in.")
                print("="*60)
            else:
                print(f"[i] Super Admin initialized with provided environment password.")
    except Exception as e:
        logger.error(f"Lỗi init super admin: {e}")
    finally:
        conn.close()


def is_super_admin(user: Dict) -> bool:
    """Kiểm tra user có phải Super Admin không."""
    if not user:
        return False
    return user.get('role') == ROLE_SUPER_ADMIN

```

## Bao_cao_phan_mem_PA01.md
# BÁO CÁO ĐỀ XUẤT TRIỂN KHAI THÍ ĐIỂM HỆ THỐNG QUẢN TRỊ AN NINH PA01 (SECURITY PROFILE 360)

**Kính gửi:** Thủ trưởng đơn vị / Lãnh đạo Phòng

**Về việc:** Đề xuất triển khai thí điểm Phần mềm Quản trị hồ sơ nghiệp vụ an ninh (Security Profile 360).

---

## I. GIỚI THIỆU CHUNG VỀ PHẦN MỀM

Hệ thống **Security Profile 360 (PA01)** là phần mềm đặc tả nghiệp vụ được xây dựng với mục tiêu số hóa, quản lý và khai thác hiệu quả hồ sơ đối tượng thuộc diện quản lý chuyên sâu (CSXH), có yếu tố nước ngoài hoặc các đối tượng nghiệp vụ an ninh.

Phần mềm được thiết kế tối ưu hóa cho môi trường mạng nội bộ, đảm bảo tính bảo mật cao (local/offline) kết hợp với các công cụ phân tích dữ liệu ứng dụng thuật toán thông minh, nâng cao hiệu suất làm việc của cán bộ trinh sát và cán bộ quản lý so với phương pháp thủ công hoặc trên Excel truyền thống.

---

## II. CÁC TÍNH NĂNG CHÍNH (KEY FEATURES)

Hệ thống được thiết kế dưới dạng Modular, phân loại theo nhu cầu thực tế của công tác trinh sát nghiệp vụ:

1. **Bảng điều khiển trung tâm (Dashboard)**
   - Trực quan hóa dữ liệu tổng quan dưới dạng biểu đồ (tương tác thời gian thực bằng ECharts/Plotly).
   - Thống kê tự động theo: phân bổ địa bàn (Top xã/phường), phân loại nghề nghiệp, cơ cấu giới tính, mức độ gia tăng hồ sơ.
   - Thống kê tỷ trọng các nhóm đối tượng đặc thù (Kết hôn nước ngoài, làm việc cho tổ chức NGO, Du học sinh, Vi phạm pháp luật ở nước ngoài...).

2. **Hồ sơ đối tượng toàn diện 360 độ (Profile 360)**
   Xây dựng mạng lưới thông tin liên kết xoay quanh 1 Số Định danh cá nhân (CCCD) bao gồm 8 nhóm dữ liệu lõi:
   - Thông tin cơ bản & Avatar.
   - Thông tin liên hệ (SĐT, Email, Mạng xã hội Zalo/Telegram/Facebook...).
   - Tài chính (Tài khoản ngân hàng đa nền tảng).
   - Phương tiện (Biển kiểm soát xe).
   - Các mối quan hệ nhân thân (Trực hệ & Phi trực hệ).
   - Hồ sơ nghiệp vụ đặc thù CSXH.
   - Quá trình hoạt động (Timeline).
   - Tài liệu/Chứng cứ số đính kèm (Hình ảnh, Scan PDF).

3. **Luân chuyển & Cập nhật Dữ liệu lớn (Bulk Import)**
   - Nhập liệu thủ công (Form chuẩn hóa).
   - Nhập liệu hàng loạt bằng file Excel linh hoạt qua 5 sheet riêng biệt.
   - Tự động sinh file mẫu phù hợp dựa vào loại hồ sơ muốn thao tác.

4. **Tìm kiếm & Rà soát thông minh hàng loạt (Batch Screening)**
   - Tra cứu chi tiết theo nhiều tiêu chí (Từ khóa viết tắt, địa phương, yếu tố nước ngoài...).
   - Rà soát chéo danh sách lớn: Upload 1 danh sách Excel hàng ngàn đối tượng để đối chiếu với CSDL.
   - Công cụ xuất Excel báo cáo danh sách kết quả chỉ với 1 click.

5. **Phân quyền & Giám sát An ninh (Audit & RBAC)**
   - Phân quyền theo Nhóm (Super Admin quản lý và cán bộ User nhập liệu).
   - Audit Log (Nhật ký hệ thống): Lưu vết mọi hành động Thêm/Sửa/Xóa, xem chi tiết, lịch sử xuất file của bất kỳ người dùng nào với địa chỉ IP và dán nhãn thời gian.

---

## III. LUỒNG XỬ LÝ DỮ LIỆU (DATA FLOW)

Luồng hoạt động của hệ thống được tối ưu hóa nhằm đảm bảo dữ liệu "Sạch - Sống - Bảo mật":

1. **Khâu Đầu vào (Data Ingress):**
   - **Thủ công:** Cán bộ nhập data qua giao diện Web -> Hệ thống kiểm tra Validation (tránh bỏ trống trường bắt buộc, validate định dạng cccd).
   - **Hàng loạt:** Tải lên file Excel -> Hàm `validate_excel_data` kiểm tra qua từng dòng -> Xác định các dòng lỗi (sai định dạng, thiếu CCCD). -> **Tách biệt dòng lỗi & dòng hợp lệ**.

2. **Khâu Xử lý (Data Processing & Sanitizing):**
   - Nội dung text được chuẩn hóa (loại bỏ khoảng trắng thừa, unidecode nếu cần tra cứu).
   - Hình ảnh, file đính kèm được đưa vào hàm `sanitize_filename` nhằm loại trừ triệt để mã độc hoặc các cuộc tấn công thay đổi đường dẫn (Path Traversal/Null Byte Injection), sau đó băm tạo tên file duy nhất.

3. **Khâu Lưu trữ (Storage):**
   - Dữ liệu chuẩn được đưa vào SQL Database (SQLite nội bộ chống rò rỉ).
   - Hành động lưu trữ ngay lập tức kích hoạt ghi log tự động vào bảng `audit_log`.

4. **Khâu Tra cứu/Xử lý (Retrieval & Fuzzy Match):**
   - Khi tìm kiếm/rà list: Dữ liệu tải từ DB (SQL) được đưa vào Module Python.
   - Nếu so sánh tên, sử dụng thuật toán tính vector chuỗi. Trả về mức độ tương đồng.
   - Kết xuất ra màn hình UI hoặc tải về dạng CSV có mã hóa UTF8-BOM để chống lỗi font trên Excel Windows.

---

## IV. CÁC ĐIỂM ĐỘT PHÁ CÔNG NGHỆ (CORE BREAKTHROUGHS)

Đề xuất phần mềm PA01 thay thế cách làm thủ công bởi 4 điểm đột phá mạnh mẽ:

### 1. Thuật toán Rà soát thông minh mờ (Fuzzy Matching Engine)

Khác với tính năng "Ctrl+F" trên Excel yêu cầu khớp chính xác 100%, hoặc câu lệnh SQL LIKE thông thường, hệ thống tích hợp thư viện `thefuzz/rapidfuzz`.

- Thuật toán cho phép đánh giá mức độ tương đồng của 2 chuỗi ký tự theo tỷ lệ `%`.
- **Ví dụ thực tiễn:** Tên "Nguyễn Văn An" và "Nguyễn Văn Ân" hoặc sai lệch cấu trúc "Văn An Nguyễn" vẫn được máy tính phát hiện với độ tương đồng `> 80%`. Hệ thống tự nhãn thành biểu tượng "⚠️ Nghi vấn" để cán bộ rà soát thủ công, tránh 100% tình trạng "lọt lưới" đối tượng do cố tình khai báo sai lệch một vài âm tiết.

### 2. Thuật toán Xử lý ngoại lệ Excel thông minh (Smart Bulk Import)

Khi cán bộ đưa danh sách vài nghìn dòng vào, thay vì báo lỗi toàn bộ file và từ chối nếu có 1 ô sai (như nhiều phần mềm hành chính), hệ thống có cơ chế chia tách thông minh:

- Tự động nhận diện những bản ghi hợp lệ và sẵn sàng `Import`.
- Tự động gạn lọc riêng các bản ghi lỗi, **xuất ngược lại cho người dùng 1 file Excel "Báo cáo lỗi"**, trỏ rõ chính xác dòng nào lỗi và lỗi do đâu để cán bộ sửa. Tiết kiệm tối đa thời gian làm sạch dữ liệu.

### 3. Kiến trúc Bảo mật từ cấp chứng cứ số (Zero-path-traversal)

Hệ thống được build kèm các lớp Security mặc định cho nghiệp vụ Công an:

- Session timeout nội bộ, tự đăng xuất sau 30 phút không thao tác nhằm tránh lộ lọt khi cán bộ rời vị trí.
- Cơ chế upload Avatar/Chứng cứ số chặn mã độc XSS, chặn tuyệt đối việc vượt rào thư mục cấp Server ảo.
- Ghi nhật ký mọi cú click chuột xem chi tiết đối tượng. Tránh trường hợp tra cứu chéo sai mục đích, phục vụ đắc lực công tác bảo vệ nội bộ.

### 4. Triển khai siêu di động & Nhẹ nhàng

Không yêu cầu cơ sở hạ tầng Server phức tạp hay cài đặt Database cồng kềnh (No SQL Server/MySQL required). Kiến trúc kết hợp Streamlit + SQLite được đóng gói cho phép hệ thống "Chạy trên mọi máy tính nội bộ", kể cả các máy cấu hình thấp, triển khai trong 3 phút là sẵn sàng hoạt động mà không bị phụ thuộc Internet bên ngoài.

---

## V. ĐỀ XUẤT, KIẾN NGHỊ

Từ những phân tích về hiệu quả nghiệp vụ thực tiễn nêu trên, kính đề xuất Lãnh đạo xem xét cho triển khai thí điểm phần mềm **Security Profile 360** trên 01 tổ/đội chuyên trách để áp dụng nhập liệu và quản lý tệp đối tượng có yếu tố nước ngoài.

Sau 1 tháng thí điểm sẽ có báo cáo đánh giá thực tiễn về thời gian tiết kiệm được và hiệu suất trích xuất thông tin trước khi nhân rộng trong đơn vị.

Kính trình Lãnh đạo xem xét, phê duyệt./.

**Người lập báo cáo**
*(Đã ký)*


## constants.py
```py
# -*- coding: utf-8 -*-
"""
Constants cho hệ thống Security Profile 360
Danh sách 148 đơn vị hành chính cấp xã/phường tỉnh Phú Thọ
(Cập nhật ngày 11/01/2026)
"""

# Danh sách 15 phường
DANH_SACH_PHUONG = [
    "Phường Âu Cơ",
    "Phường Hòa Bình",
    "Phường Kỳ Sơn",
    "Phường Nông Trang",
    "Phường Phong Châu",
    "Phường Phú Thọ",
    "Phường Phúc Yên",
    "Phường Tân Hòa",
    "Phường Thanh Miếu",
    "Phường Thống Nhất",
    "Phường Vân Phú",
    "Phường Việt Trì",
    "Phường Vĩnh Phúc",
    "Phường Vĩnh Yên",
    "Phường Xuân Hòa",
]

# Danh sách 133 xã
DANH_SACH_XA = [
    "Xã An Bình",
    "Xã An Nghĩa",
    "Xã Bản Nguyên",
    "Xã Bao La",
    "Xã Bằng Luân",
    "Xã Bình Nguyên",
    "Xã Bình Phú",
    "Xã Bình Tuyền",
    "Xã Bình Xuyên",
    "Xã Cao Dương",
    "Xã Cao Phong",
    "Xã Cao Sơn",
    "Xã Cẩm Khê",
    "Xã Chân Mộng",
    "Xã Chí Đám",
    "Xã Chí Tiên",
    "Xã Cự Đồng",
    "Xã Dân Chủ",
    "Xã Dũng Tiến",
    "Xã Đà Bắc",
    "Xã Đại Đình",
    "Xã Đại Đồng",
    "Xã Đan Thượng",
    "Xã Đào Xá",
    "Xã Đạo Trù",
    "Xã Đông Thành",
    "Xã Đồng Lương",
    "Xã Đức Nhàn",
    "Xã Hạ Hòa",
    "Xã Hải Lựu",
    "Xã Hiền Lương",
    "Xã Hiền Quan",
    "Xã Hoàng An",
    "Xã Hoàng Cương",
    "Xã Hội Thịnh",
    "Xã Hợp Kim",
    "Xã Hợp Lý",
    "Xã Hùng Việt",
    "Xã Hương Cần",
    "Xã Hy Cương",
    "Xã Khả Cửu",
    "Xã Kim Bôi",
    "Xã Lạc Lương",
    "Xã Lạc Sơn",
    "Xã Lạc Thủy",
    "Xã Lai Đồng",
    "Xã Lâm Thao",
    "Xã Lập Thạch",
    "Xã Liên Châu",
    "Xã Liên Hòa",
    "Xã Liên Minh",
    "Xã Liên Sơn",
    "Xã Long Cốc",
    "Xã Lương Sơn",
    "Xã Mai Châu",
    "Xã Mai Hạ",
    "Xã Minh Đài",
    "Xã Minh Hòa",
    "Xã Mường Bi",
    "Xã Mường Động",
    "Xã Mường Hoa",
    "Xã Mường Thàng",
    "Xã Mường Vang",
    "Xã Nật Sơ",
    "Xã Ngọc Sơn",
    "Xã Nguyệt Đức",
    "Xã Nhân Nghĩa",
    "Xã Pà Cò",
    "Xã Phú Khê",
    "Xã Phú Mỹ",
    "Xã Phù Ninh",
    "Xã Phùng Nguyên",
    "Xã Quảng Yên",
    "Xã Quy Đức",
    "Xã Quyết Thắng",
    "Xã Sơn Đông",
    "Xã Sơn Lương",
    "Xã Sông Lô",
    "Xã Tam Dương",
    "Xã Tam Dương Bắc",
    "Xã Tam Đảo",
    "Xã Tam Hồng",
    "Xã Tam Nông",
    "Xã Tam Sơn",
    "Xã Tân Lạc",
    "Xã Tân Mai",
    "Xã Tân Pheo",
    "Xã Tân Sơn",
    "Xã Tây Cốc",
    "Xã Tề Lỗ",
    "Xã Thái Hòa",
    "Xã Thanh Ba",
    "Xã Thanh Sơn",
    "Xã Thanh Thủy",
    "Xã Thịnh Minh",
    "Xã Thổ Tang",
    "Xã Thọ Văn",
    "Xã Thu Cúc",
    "Xã Thung Nai",
    "Xã Thượng Cốc",
    "Xã Thượng Long",
    "Xã Tiên Lương",
    "Xã Tiên Lữ",
    "Xã Toàn Thắng",
    "Xã Trạm Thản",
    "Xã Trung Sơn",
    "Xã Tu Vũ",
    "Xã Văn Lang",
    "Xã Văn Miếu",
    "Xã Vạn Xuân",
    "Xã Vân Bán",
    "Xã Vân Sơn",
    "Xã Vĩnh An",
    "Xã Vĩnh Chân",
    "Xã Vĩnh Hưng",
    "Xã Vĩnh Phú",
    "Xã Vĩnh Thành",
    "Xã Vĩnh Tường",
    "Xã Võ Miếu",
    "Xã Xuân Đài",
    "Xã Xuân Lãng",
    "Xã Xuân Lũng",
    "Xã Xuân Viên",
    "Xã Yên Kỳ",
    "Xã Yên Lạc",
    "Xã Yên Lãng",
    "Xã Yên Lập",
    "Xã Yên Phú",
    "Xã Yên Sơn",
    "Xã Yên Thủy",
    "Xã Yên Trị",
]

# Danh sách đầy đủ 148 đơn vị hành chính cấp xã/phường (dùng cho dropdown)
DANH_SACH_XA_PHU_THO = DANH_SACH_PHUONG + DANH_SACH_XA

# Các lựa chọn cho trường giới tính
GIOI_TINH_OPTIONS = ["Nam", "Nữ"]

# Các lựa chọn cho trường tỉnh
TINH_OPTIONS = ["Phú Thọ", "Khác"]

# Các lựa chọn cho phân loại nghề nghiệp
PHAN_LOAI_NGHE_NGHIEP_OPTIONS = [
    "Cơ quan nhà nước",
    "Lao động tự do",
    "Doanh nghiệp tư nhân",
    "Nông nghiệp",
    "FDI",
    "NGO",
    "Học sinh/Sinh viên",
    "Hưu trí",
    "Thất nghiệp",
    "Khác"
]

# Các loại liên hệ
LOAI_LIEN_HE_OPTIONS = ["SĐT", "Email", "Facebook",
                        "Zalo", "Telegram", "Instagram", "Tiktok", "Khác"]

# Các loại phương tiện
LOAI_XE_OPTIONS = ["Ô tô", "Xe máy", "Ô tô con",
                   "Ô tô tải", "Xe khách", "Xe đạp điện", "Khác"]

# Các loại hình hồ sơ đặc thù (Yếu tố nước ngoài & Nghiệp vụ)
LOAI_HINH_DAC_THU = {
    "Hon_Nhan_NN": "Kết hôn/sống chung với người nước ngoài",
    "Lam_Viec_NN": "Làm việc cho tổ chức nước ngoài (NGO/FDI)",
    "Hoc_Tap_Cong_Tac_NN": "Du học/Công tác nước ngoài",
    "Vi_Pham_NN": "Từng vi phạm pháp luật ở nước ngoài",
    "Xac_Minh": "Đã từng được xác minh",
}

# Danh sách quốc gia chuẩn hóa (các quốc gia thường gặp)
DANH_SACH_QUOC_GIA = [
    # Đông Á
    "Trung Quốc", "Hàn Quốc", "Nhật Bản", "Đài Loan", "Hồng Kông", "Macao",
    # Đông Nam Á
    "Thái Lan", "Lào", "Campuchia", "Myanmar", "Malaysia", "Singapore",
    "Indonesia", "Philippines", "Brunei", "Đông Timor",
    # Nam Á
    "Ấn Độ", "Pakistan", "Bangladesh", "Nepal", "Sri Lanka",
    # Trung Đông
    "UAE", "Ả Rập Xê Út", "Qatar", "Kuwait", "Israel", "Thổ Nhĩ Kỳ",
    # Châu Âu
    "Nga", "Đức", "Pháp", "Anh", "Ý", "Tây Ban Nha", "Hà Lan", "Bỉ",
    "Thụy Sĩ", "Áo", "Ba Lan", "Séc", "Hungary", "Ukraine", "Romania",
    # Châu Mỹ
    "Mỹ", "Canada", "Brazil", "Argentina", "Mexico", "Chile",
    # Châu Úc
    "Úc", "New Zealand",
    # Châu Phi
    "Nam Phi", "Ai Cập", "Nigeria", "Kenya",
    # Khác
    "Khác"
]

# Các loại hình tổ chức nước ngoài
LOAI_HINH_TO_CHUC_NN = ["FDI", "NGO", "Đại sứ quán",
                        "Lãnh sự quán", "Tổ chức quốc tế", "Khác"]

# Hình thức du học/công tác
HINH_THUC_DU_HOC = ["Du học", "Công tác", "Thuê lao động", "Thăm thân", "Khác"]

# Kết quả xác minh
KET_QUA_XAC_MINH = ["Đủ điều kiện", "Không đủ điều kiện",
                    "Đang xác minh", "Chưa có kết quả", "Khác"]

# Ngân hàng phổ biến
DANH_SACH_NGAN_HANG = [
    "Vietcombank", "Vietinbank", "BIDV", "Agribank", "Techcombank",
    "MB Bank", "ACB", "Sacombank", "VPBank", "TPBank", "HDBank",
    "SHB", "OCB", "VIB", "MSB", "Eximbank", "LienVietPostBank", "Khác"
]

# Loại tài liệu đính kèm
LOAI_TAI_LIEU_OPTIONS = [
    "Báo cáo xác minh",
    "Ảnh chân dung",
    "CMND/CCCD (bản scan)",
    "Hộ chiếu (bản scan)",
    "Biên bản làm việc",
    "Hợp đồng/Thỏa thuận",
    "Ảnh liên quan",
    "Tài liệu nghiệp vụ",
    "Khác"
]

# File extensions được phép upload
ALLOWED_EXTENSIONS: list[str] = [
    'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif']

# Giới hạn dung lượng file (MB)
MAX_FILE_SIZE_MB: int = 10

# Giới hạn số file per CCCD
MAX_FILES_PER_CCCD: int = 50


# ============================================
# MESSAGES - Các thông báo chuẩn hóa
# ============================================
class Messages:
    """Các thông báo UI chuẩn hóa để tránh magic strings"""
    # Errors
    CCCD_NOT_FOUND = "⚠️ CCCD không tồn tại trong hệ thống!"
    CCCD_INVALID = "⚠️ Vui lòng nhập đúng 12 số CCCD!"
    CCCD_EXISTS = "⚠️ CCCD đã tồn tại trong hệ thống!"
    MISSING_REQUIRED = "⚠️ Vui lòng nhập đầy đủ thông tin!"
    MISSING_NAME = "⚠️ Vui lòng nhập họ tên!"
    SYSTEM_ERROR = "❌ Đã xảy ra lỗi hệ thống. Vui lòng thử lại."

    # Success
    SAVE_SUCCESS = "✅ Lưu thành công!"
    DELETE_SUCCESS = "✅ Đã xóa thành công!"
    UPDATE_SUCCESS = "✅ Cập nhật thành công!"
    UPLOAD_SUCCESS = "✅ Đã upload thành công!"

    # Info
    NO_DATA = "💡 Chưa có dữ liệu."
    PLEASE_SAVE_PERSONAL_FIRST = "⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)"

```

## database.py
```py
# -*- coding: utf-8 -*-
"""
Database module cho hệ thống Security Profile 360
Tạo cơ sở dữ liệu SQLite với các bảng theo Schema PRD
"""

import logging
import re
import sqlite3
import os
import streamlit as st

# Tên file database
DB_NAME = "security_profile.db"


def get_db_path():
    """Lấy đường dẫn đầy đủ đến file database"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection():
    """Tạo kết nối đến database"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    # Bật foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@st.cache_resource
def get_cached_connection():
    """Tạo connection dùng lại (cached), dùng cho read-only queries"""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    """Tạo tất cả các bảng trong database"""
    conn = get_connection()
    cursor = conn.cursor()

    # ========================================
    # BẢNG DỮ LIỆU GỐC (Trung tâm hệ thống)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doi_tuong (
            cccd TEXT PRIMARY KEY,
            ho_ten TEXT,
            ngay_sinh DATE,
            gioi_tinh TEXT,
            dia_chi_tinh TEXT DEFAULT 'Phú Thọ',
            dia_chi_xa TEXT,
            anh_chan_dung TEXT,
            phan_loai_nghe_nghiep TEXT,
            chi_tiet_nghe_nghiep TEXT,
            ghi_chu_chung TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================
    # BẢNG VỆ TINH - TẦNG 1
    # ========================================

    # Bảng liên hệ (SĐT, Email, Facebook, Zalo, Telegram)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lien_he (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_lien_he TEXT,
            gia_tri TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # Bảng tài chính (Tài khoản ngân hàng)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tai_chinh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            ngan_hang TEXT,
            so_tai_khoan TEXT,
            chu_tai_khoan TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # Bảng phương tiện (Xe cộ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phuong_tien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_xe TEXT,
            bien_kiem_soat TEXT,
            ten_phuong_tien TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # Bảng nhân thân (Bố, Mẹ, Vợ/Chồng, Quan hệ khác)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nhan_than (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_quan_he TEXT NOT NULL,
            ho_ten TEXT,
            cccd_nhan_than TEXT,
            ngay_sinh DATE,
            nghe_nghiep TEXT,
            noi_o TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # ========================================
    # BẢNG ĐẶC THÙ - TẦNG 2 (Yếu tố nước ngoài & Nghiệp vụ)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ho_so_dac_thu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_hinh TEXT NOT NULL,
            noi_dung_chi_tiet TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # ========================================
    # BẢNG TÀI LIỆU ĐÍNH KÈM
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tai_lieu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            ten_file_goc TEXT,
            ten_file_luu TEXT,
            duong_dan TEXT,
            loai_tai_lieu TEXT,
            mo_ta TEXT,
            dung_luong INTEGER,
            dinh_dang TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # ========================================
    # BẢNG QUÁ TRÌNH HOẠT ĐỘNG
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qua_trinh_hoat_dong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            thoi_gian TEXT,
            noi_dung TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

    # ========================================
    # BẢNG NGUỒN DỮ LIỆU (Source Tracking - OSINT Pattern)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nguon_du_lieu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_nguon TEXT NOT NULL,
            loai_nguon TEXT,
            thoi_gian_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            nguoi_import TEXT,
            file_goc TEXT,
            ghi_chu TEXT
        )
    """)

    # ========================================
    # BẢNG QUAN HỆ ĐỐI TƯỢNG (Person-to-Person Connection)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quan_he_doi_tuong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd_1 TEXT NOT NULL,
            cccd_2 TEXT NOT NULL,
            loai_quan_he TEXT,
            mo_ta TEXT,
            nguon_id INTEGER,
            do_tin_cay INTEGER DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd_1) REFERENCES doi_tuong(cccd) ON DELETE CASCADE,
            FOREIGN KEY (cccd_2) REFERENCES doi_tuong(cccd) ON DELETE CASCADE,
            FOREIGN KEY (nguon_id) REFERENCES nguon_du_lieu(id)
        )
    """)

    # ========================================
    # BẢNG LỊCH SỬ THAY ĐỔI (Audit Trail)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bang TEXT NOT NULL,
            hanh_dong TEXT NOT NULL,
            khoa_chinh TEXT,
            du_lieu_cu TEXT,
            du_lieu_moi TEXT,
            nguoi_thuc_hien TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================
    # BẢNG NGƯỜI DÙNG (Authentication)
    # ========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            ho_ten TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            must_change_password INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Tạo index để tăng tốc truy vấn
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_lien_he_cccd ON lien_he(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_tai_chinh_cccd ON tai_chinh(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_phuong_tien_cccd ON phuong_tien(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_nhan_than_cccd ON nhan_than(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_cccd ON ho_so_dac_thu(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_loai_hinh ON ho_so_dac_thu(loai_hinh)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_qua_trinh_hoat_dong_cccd ON qua_trinh_hoat_dong(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_tai_lieu_cccd ON tai_lieu(cccd)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_doi_tuong_ho_ten ON doi_tuong(ho_ten)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_doi_tuong_created_at ON doi_tuong(created_at)")

    # Index cho các bảng mới
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_quan_he_cccd1 ON quan_he_doi_tuong(cccd_1)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_quan_he_cccd2 ON quan_he_doi_tuong(cccd_2)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_bang ON audit_log(bang)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_khoa ON audit_log(khoa_chinh)")

    conn.commit()
    conn.close()

    print(f"[OK] Da tao database thanh cong: {get_db_path()}")
    print("[i] Cac bang da tao:")
    print("   - doi_tuong (Bang du lieu goc)")
    print("   - lien_he (Thong tin lien he)")
    print("   - tai_chinh (Tai khoan ngan hang)")
    print("   - phuong_tien (Phuong tien)")
    print("   - ho_so_dac_thu (Yeu to nuoc ngoai & Nghiep vu)")
    print("   - qua_trinh_hoat_dong (Qua trinh hoat dong)")
    print("   - nguon_du_lieu (Theo doi nguon du lieu)")
    print("   - quan_he_doi_tuong (Quan he giua cac doi tuong)")
    print("   - audit_log (Lich su thay doi)")


def save_qua_trinh_hoat_dong(cccd, thoi_gian, noi_dung, ghi_chu=""):
    """Lưu thông tin quá trình hoạt động"""
    if not noi_dung:
        return
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO qua_trinh_hoat_dong (cccd, thoi_gian, noi_dung, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, thoi_gian, noi_dung, ghi_chu))
        conn.commit()
    finally:
        conn.close()


def get_qua_trinh_hoat_dong(cccd):
    """Lấy danh sách quá trình hoạt động theo CCCD"""
    conn = get_connection()
    try:
        # Sắp xếp theo ID giảm dần (mới nhất lên đầu) hoặc có thể parse thời gian nếu cần
        # Ở đây để đơn giản ta sort theo created_at/id
        query = "SELECT * FROM qua_trinh_hoat_dong WHERE cccd = ? ORDER BY id DESC"
        # Trả về list of sqlite3.Row -> có thể convert sang dict hoặc DataFrame
        # Để nhất quán với usage trong views (pandas read_sql), ta có thể dùng pandas ở view
        # Tuy nhiên user yêu cầu hàm này SELECT dữ liệu.
        # Ở đay trả về list dict cho linh hoạt
        cursor = conn.cursor()
        cursor.execute(query, (cccd,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_qua_trinh_hoat_dong(qt_id: int) -> bool:
    """Xóa quá trình hoạt động theo ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM qua_trinh_hoat_dong WHERE id = ?", (qt_id,))
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Lỗi xóa quá trình hoạt động: {e}")
        return False
    finally:
        conn.close()


# Logging configuration
logger = logging.getLogger(__name__)


def verify_database():
    """Kiểm tra cấu trúc database đã tạo"""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Lấy danh sách các bảng
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        logger.info("Cấu trúc Database:")

        for table in tables:
            table_name = table[0]
            if table_name.startswith("sqlite_"):
                continue

            # SECURITY: Sanitize table_name để tránh SQL injection
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                logger.warning(f"Invalid table name detected: {table_name}")
                continue

            logger.info(f"[TABLE] {table_name}")

            # Lấy thông tin các cột - sau khi đã validate table_name
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                pk_marker = "[PK]" if is_pk else "    "
                null_marker = "NOT NULL" if not_null else ""
                default_marker = f"DEFAULT {default_val}" if default_val else ""
                logger.debug(
                    f"   {pk_marker} {col_name}: {col_type} {null_marker} {default_marker}")
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Khởi tạo Database Security Profile 360...")
    create_tables()
    verify_database()
    logger.info("Hoàn tất! Database đã sẵn sàng sử dụng.")

```

## Mo_ta_chi_tiet_PA01.md
# MÔ TẢ CHI TIẾT DỰ ÁN (SECURITY PROFILE 360)

## 1. Giới thiệu chung
**Tên dự án:** Hệ thống Quản trị An ninh PA01 (Security Profile 360)
**Mục tiêu:** Số hóa, quản lý và khai thác hiệu quả hồ sơ đối tượng thuộc diện quản lý chuyên sâu (CSXH), đối tượng có yếu tố nước ngoài hoặc các diện đối tượng nghiệp vụ an ninh khác.

### Công nghệ sử dụng
- **Giao diện người dùng (Frontend):** Streamlit (Python).
- **Tiến trình xử lý (Backend):** Python (`services.py`, `auth.py`, `database.py`, `utils`).
- **Cơ sở dữ liệu (Database):** SQLite (`security_profile.db`).
- **Thư viện cốt lõi:** `pandas` (xử lý dữ liệu lớn), `thefuzz`/`rapidfuzz` (thuật toán rà soát/so khớp mờ), `ECharts`/`Plotly` (vẽ biểu đồ trực quan).

### Kiến trúc Dữ liệu "Profile 360 độ"
Điểm lõi của hệ thống là xoay quanh **Số Định danh cá nhân (CCCD)**, tạo ra một mạng lưới thông tin vệ tinh bao gồm 8 nhóm dữ liệu:
1. **Thông tin gốc (Đối tượng):** Tên, năm sinh, quê quán, nghề nghiệp, ảnh chân dung.
2. **Thông tin Liên hệ:** Số điện thoại, Email, Mạng xã hội.
3. **Tài chính:** Tài khoản ngân hàng, ví điện tử.
4. **Phương tiện:** Các phương tiện đăng ký.
5. **Nhân thân:** Quan hệ gia đình, thân nhân.
6. **Hồ sơ Đặc thù:** Các yếu tố nghiệp vụ CSXH.
7. **Quá trình hoạt động:** Dòng thời gian (Timeline) theo dõi di biến động.
8. **Tài liệu đính kèm:** Hồ sơ chứng cứ, tài liệu scan.

### Các tính năng Đột phá & An toàn
- **Dashboard trực quan:** Thống kê theo xã/phường, nhóm đối tượng thông qua biểu đồ tự động.
- **Nhập liệu & Xử lý Excel thông minh (Smart Bulk Import):** Quản lý đầu vào qua Upload Excel hàng nghìn dòng. Lọc lỗi thông minh.
- **Rà soát danh sách chéo bằng So khớp mờ (Fuzzy Matching):** So khớp tương đối, không yêu cầu khớp 100%.
- **Bảo mật Nội bộ & Phân quyền (Audit Trails & RBAC):** Phân quyền Super Admin / User, nhật ký lưu vết mọi thao tác (Audit Log), chống Path Traversal.

---

## 2. SƠ ĐỒ LUỒNG XỬ LÝ (PROCESSING FLOW DIAGRAM)
Hệ thống xử lý phân tầng rõ ràng từ Frontend (Giao diện người dùng) -> Backend (Xử lý Python) -> Database (SQLite).

```mermaid
block-beta
  columns 3

  %% Hàng 1: Người dùng và Giao diện
  User(("Cán bộ\nSử dụng"))
  Admin(("Super Admin"))
  Login["Đăng nhập\nAuthentication"]
  User --> Login
  Admin --> Login
  
  %% Row 2: Khối chức năng Frontend
  space
  block:Frontend:3
    columns 5
    Dash["Dashboard\nTổng quan"]
    InputM["Nhập liệu\nThủ công"]
    InputE["Nhập Excel\nHàng loạt"]
    Search["Tra cứu &\nRà soát chéo"]
    SysAdmin["Quản lý Hệ thống\n& Ghi Log"]
    
    Dash --> InputM
    Dash --> InputE
    Dash --> Search
    Dash --> SysAdmin
  end

  %% Liên kết từ Login xuống Frontend
  Login --> Frontend

  %% Row 3: Logic Xử lý Backend
  space
  block:Backend:3
    columns 5
    Auth["Xác thực\nThẩm quyền"]
    Valid["Chuẩn hóa &\nKiểm duyệt đầu vào"]
    Parser["Tách bản ghi\nHợp lệ / Lỗi"]
    FileProcess["Xử lý File &\nChặn mã độc"]
    Fuzzy["Thuật toán mờ\n(Fuzzy Match)"]

    Auth --> Valid
    Parser --> Valid
  end

  %% Liên kết Frontend xuống Backend
  InputM --> Valid
  InputE --> Parser
  Search --> Fuzzy
  SysAdmin --> Auth

  %% Row 4: Cơ sở dữ liệu SQLite
  space
  block:Database:3
    columns 5
    DBUser[("Tài khoản User")]
    DBMain[("Dữ liệu Lõi\n(Đối tượng)")]
    DBSatellite[("Dữ liệu Vệ tinh\n(8 bảng)")]
    DBAudit[("Lịch sử thao tác\n(Audit Log)")]
    DBSource[("Nguồn OSINT\n(Import log)")]
  end

  %% Tương tác Backend - Database
  Auth --> DBUser
  Valid --> DBMain
  Valid --> DBSatellite
  FileProcess --> Storage[("Kho Upload\nFiles/Avatar")]
  Fuzzy --> DBMain

  %% Luồng kích hoạt Audit (Nhật ký)
  DBMain --> DBAudit
  DBSatellite --> DBAudit
  SysAdmin --> DBAudit

  %% Xử lý kết quả phản hồi lên Frontend
  Parser --> FileError["File Excel Báo lỗi"]
  Fuzzy --> Res["Hiện Kết quả &\nCảnh báo độ trùng khớp"]

  %% Định dạng màu sắc sơ đồ (Styling tùy chọn)
  style Frontend fill:#eef,stroke:#333,stroke-width:2px;
  style Backend fill:#eaf8e6,stroke:#333,stroke-width:2px;
  style Database fill:#fdf1e6,stroke:#333,stroke-width:2px;
```


## run_app.py
```py
import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    import sys
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())

```

## services.py
```py
# -*- coding: utf-8 -*-
"""
Service Layer - Xử lý business logic
Tách từ nhap_lieu.py và ho_so_chi_tiet.py để tránh circular import

Module này chứa tất cả các hàm save/delete/update cho database.
Các views chỉ cần import từ đây thay vì import lẫn nhau.
"""

import json
import logging
import re
import uuid
from pathlib import Path
from datetime import datetime
from database import get_connection
from constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def validate_cccd(cccd: str) -> bool:
    """
    Validate CCCD string to prevent path traversal and injection.
    Only allows alphanumeric characters.
    """
    if not cccd:
        return False
    # Only allow alphanumeric characters
    return cccd.isalnum()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename để ngăn path traversal và injection attacks.

    Bảo vệ chống:
    - Path traversal (../)
    - Null byte injection
    - Ký tự đặc biệt nguy hiểm
    - Filename quá dài
    """
    import os

    if not filename:
        return 'unnamed_file'

    # Lấy tên file, loại bỏ path
    filename = Path(filename).name

    # Loại bỏ null bytes (null byte injection)
    filename = filename.replace('\x00', '')

    # Loại bỏ các ký tự đặc biệt nguy hiểm
    # Chỉ giữ lại: chữ cái (bao gồm Unicode), số, dấu gạch ngang, gạch dưới, dấu chấm, khoảng trắng
    filename = re.sub(r'[^\w\-_\. ]', '', filename, flags=re.UNICODE)

    # Loại bỏ path traversal patterns
    filename = filename.replace('..', '')

    # Giới hạn độ dài filename
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename.strip() if filename.strip() else 'unnamed_file'


def get_upload_folder(cccd):
    """Lấy thư mục upload cho một CCCD"""
    if not validate_cccd(cccd):
        raise ValueError("Invalid CCCD: Must be alphanumeric only")

    base_path = Path(__file__).parent / "uploads" / cccd
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


# ============================================
# SAVE FUNCTIONS
# ============================================

def save_lien_he(cccd, loai, gia_tri, ghi_chu=""):
    """Lưu thông tin liên hệ"""
    if not gia_tri:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lien_he (cccd, loai_lien_he, gia_tri, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, loai, gia_tri, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu liên hệ: {e}")
        return False
    finally:
        conn.close()


def save_tai_chinh(cccd, ngan_hang, so_tai_khoan, chu_tai_khoan="", ghi_chu=""):
    """Lưu thông tin tài khoản ngân hàng"""
    if not so_tai_khoan:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tai_chinh (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu tài chính: {e}")
        return False
    finally:
        conn.close()


def save_phuong_tien(cccd, loai_xe, bien_so, ten_xe, ghi_chu=""):
    """Lưu thông tin phương tiện"""
    if not bien_so:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO phuong_tien (cccd, loai_xe, bien_kiem_soat, ten_phuong_tien, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (cccd, loai_xe, bien_so, ten_xe, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu phương tiện: {e}")
        return False
    finally:
        conn.close()


def save_nhan_than(cccd, loai_quan_he, ho_ten, cccd_nhan_than="", ngay_sinh=None, nghe_nghiep="", noi_o="", ghi_chu=""):
    """Lưu thông tin nhân thân"""
    if not ho_ten:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nhan_than (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu nhân thân: {e}")
        return False
    finally:
        conn.close()


def save_ho_so_dac_thu(cccd, loai_hinh, noi_dung_dict, ghi_chu=""):
    """Lưu hồ sơ đặc thù (CSXH)"""
    if not noi_dung_dict:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ho_so_dac_thu (cccd, loai_hinh, noi_dung_chi_tiet, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, loai_hinh, json.dumps(noi_dung_dict, ensure_ascii=False), ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu hồ sơ đặc thù: {e}")
        return False
    finally:
        conn.close()


def save_tai_lieu(cccd, uploaded_file, loai_tai_lieu, mo_ta=""):
    """Lưu tài liệu đính kèm"""
    if not uploaded_file:
        return False, "Không có file"

    file_size = len(uploaded_file.getvalue())
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB"

    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng không hỗ trợ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"

    safe_filename = sanitize_filename(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_filename}"

    upload_folder = get_upload_folder(cccd)
    file_path = upload_folder / unique_name

    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    except Exception as e:
        logger.exception(f"Lỗi lưu file: {e}")
        return False, "Đã xảy ra lỗi khi lưu file. Vui lòng thử lại."

    duong_dan = f"uploads/{cccd}/{unique_name}"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tai_lieu (cccd, ten_file_goc, ten_file_luu, duong_dan, loai_tai_lieu, mo_ta, dung_luong, dinh_dang)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cccd, safe_filename, unique_name, duong_dan, loai_tai_lieu, mo_ta, file_size, file_ext))
        conn.commit()
        return True, "Đã upload thành công!"
    except Exception as e:
        logger.exception(f"Lỗi lưu metadata: {e}")
        if file_path.exists():
            file_path.unlink()
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def save_doi_tuong(data):
    """Lưu thông tin đối tượng chính"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO doi_tuong (cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_tinh, 
                                   dia_chi_xa, anh_chan_dung, phan_loai_nghe_nghiep, 
                                   chi_tiet_nghe_nghiep, ghi_chu_chung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['cccd'],
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data.get('anh_chan_dung', ''),
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung']
        ))

        # Handle Avatar Upload AFTER inserting record
        avatar_file = data.get('avatar_file')
        if avatar_file:
            try:
                # SECURITY CHECK: Validate file extension
                parts = avatar_file.name.split('.')
                if len(parts) > 1:
                    file_ext = parts[-1].lower()
                else:
                    file_ext = ""

                if file_ext not in ALLOWED_EXTENSIONS:
                    logger.error(f"Security: Attempted to upload invalid extension '{file_ext}' for CCCD {data['cccd']}")
                    conn.rollback()
                    return False, f"Định dạng ảnh không hợp lệ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"

                # SECURITY: Validate CCCD before using in file path
                if not validate_cccd(data['cccd']):
                    logger.error("Security: Invalid CCCD for avatar path")
                    conn.rollback()
                    return False, "CCCD không hợp lệ"

                import time
                base_path = Path(__file__).parent / "uploads" / data['cccd']
                base_path.mkdir(parents=True, exist_ok=True)

                safe_name = f"avatar_{int(time.time())}.{file_ext}"
                save_path = base_path / safe_name

                with open(save_path, "wb") as f:
                    f.write(avatar_file.getbuffer())

                relative_path = f"uploads/{data['cccd']}/{safe_name}"
                cursor.execute("UPDATE doi_tuong SET anh_chan_dung = ? WHERE cccd = ?",
                               (relative_path, data['cccd']))
            except Exception as e:
                logger.error(f"Error saving avatar on create: {e}")

        conn.commit()
        return True, "Lưu thành công!"
    except Exception as e:
        logger.exception(f"Lỗi lưu đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


# ============================================
# CHECK FUNCTIONS
# ============================================

def check_cccd_exists(cccd: str) -> bool:
    """Kiểm tra CCCD đã tồn tại chưa"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM doi_tuong WHERE cccd = ?", (cccd,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()

```

## style.css
```css
/* ============================================
   SECURITY PROFILE 360 - GLASSMORPHISM THEME
   Phong cách Kính mờ (Glassmorphism)
   Tối ưu cho độ tương phản và dễ đọc
   ============================================ */

/* Import Google Fonts - Inter cho typography hiện đại */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ============================================
   CSS VARIABLES - Biến màu sắc và hiệu ứng
   ============================================ */
:root {
    /* Gradient Background - Tối hơn để chữ nổi bật */
    --bg-gradient-1: #0a0a1a;
    --bg-gradient-2: #1a1a3e;
    --bg-gradient-3: #151530;

    /* Glassmorphism Colors - Tăng độ mờ */
    --glass-bg: rgba(255, 255, 255, 0.1);
    --glass-bg-hover: rgba(255, 255, 255, 0.15);
    --glass-bg-strong: rgba(255, 255, 255, 0.12);
    --glass-border: rgba(255, 255, 255, 0.2);
    --glass-shadow: rgba(0, 0, 0, 0.4);

    /* Text Colors - Tăng độ sáng (Toàn bộ trắng để tương phản trên nền đen) */
    --text-primary: #ffffff;
    --text-secondary: #ffffff;
    --text-muted: #e0e0e0;
    --text-label: #ffffff;

    /* Accent Colors */
    --accent-primary: #667eea;
    --accent-secondary: #764ba2;
    --accent-success: #00d9a5;
    --accent-warning: #ffc107;
    --accent-danger: #ff6b6b;
    --accent-info: #17a2b8;

    /* Blur Effect */
    --blur-amount: 20px;

    /* Border Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 20px;
    --radius-xl: 30px;

    /* Sidebar Width */
    --sidebar-width: 320px;
}

/* ============================================
   MAIN BACKGROUND - Gradient động
   ============================================ */
/* ============================================
   MAIN BACKGROUND - Nền Đơn Giản
   ============================================ */
.stApp {
    /* Nền màu tối đơn giản, độ tương phản cao */
    background: #0e1117 !important;
    background-image: none !important;
}

/* Ẩn các hiệu ứng nền động (animated orbs) nếu có, để tránh rối mắt */
.stApp::before {
    display: none !important;
}

/* ============================================
   GLOBAL TEXT OVERRIDE - Force White Text
   ============================================ */
/* Bắt buộc tất cả văn bản màu trắng cho các thành phần chính */
.stApp,
.stApp>header,
.stApp>div,
.stApp footer,
.stMarkdown,
.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4,
.stMarkdown h5,
.stMarkdown h6,
.stText,
.stCodeBlock,
.stCaption,
label,
p {
    color: #ffffff !important;
}

/*
   FIX DROPDOWN & INPUTS
   Dropdown menu của Streamlit (BaseWeb) thường bị ảnh hưởng bởi global style.
   Cần set lại màu chữ cho dropdown menu và các ô input.
*/

/* 1. Các ô nhập liệu (Input, SelectBox, DateInput...) có nền sáng -> Chữ phải màu ĐEN */
input,
textarea,
select,
.stSelectbox [data-baseweb="select"] div {
    color: #000000 !important;
}

/* Cụ thể hơn cho Streamlit Input Widgets */
.stTextInput>div>div>input,
.stSelectbox>div>div>div,
.stDateInput>div>div>input,
.stTextArea textarea,
.stNumberInput>div>div>input {
    color: #1a1a2e !important;
    -webkit-text-fill-color: #1a1a2e !important;
    /* Dành cho Chrome/Safari */
    font-weight: 600 !important;
}

/* 2. Dropdown Menu Items (Danh sách xổ xuống) */
/* Container của dropdown menu - Nền TỐI, chữ SÁNG */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"] {
    background-color: #1e1e3f !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    overflow: hidden !important;
}

/* Các item trong menu dropdown -> Chữ TRẮNG SÁNG, dễ đọc */
[data-baseweb="popover"] li,
[data-baseweb="popover"] div,
[data-baseweb="popover"] span,
[data-baseweb="menu"] li,
[data-baseweb="menu"] div,
[role="option"],
[role="option"] div,
[role="option"] span {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    background-color: transparent !important;
}

/* Mỗi option item */
[role="option"] {
    padding: 12px 16px !important;
    transition: all 0.2s ease !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Hover state cho dropdown item - Highlight màu accent */
[role="option"]:hover {
    background-color: rgba(102, 126, 234, 0.4) !important;
}

/* Selected option - Màu đậm hơn */
[role="option"][aria-selected="true"],
[role="option"][data-highlighted="true"] {
    background-color: rgba(102, 126, 234, 0.5) !important;
    font-weight: 600 !important;
}

/* Placeholder */
input::placeholder,
textarea::placeholder {
    color: #888888 !important;
    -webkit-text-fill-color: #888888 !important;
    font-weight: 400 !important;
}

@keyframes float {

    0%,
    100% {
        transform: translate(0, 0) rotate(0deg);
    }

    25% {
        transform: translate(2%, 2%) rotate(1deg);
    }

    50% {
        transform: translate(-1%, 3%) rotate(-1deg);
    }

    75% {
        transform: translate(3%, -2%) rotate(1deg);
    }
}

/* ============================================
   SIDEBAR - Thanh điều hướng bên trái
   ============================================ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10, 10, 26, 0.98) 0%, rgba(26, 26, 62, 0.98) 100%) !important;
    backdrop-filter: blur(var(--blur-amount)) !important;
    -webkit-backdrop-filter: blur(var(--blur-amount)) !important;
    border-right: 1px solid var(--glass-border) !important;
    width: var(--sidebar-width) !important;
}

[data-testid="stSidebar"]>div:first-child {
    background: transparent !important;
    padding: 1.5rem 1rem !important;
}

/* Sidebar Collapse/Expand Button - Nút đóng/mở sidebar */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
}

button[data-testid="stSidebarCollapseButton"],
button[kind="sidebarCollapse"],
[data-testid="stSidebar"] button[kind="header"] {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    visibility: visible !important;
}

button[data-testid="stSidebarCollapseButton"]:hover,
button[kind="sidebarCollapse"]:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

button[data-testid="stSidebarCollapseButton"] svg,
button[kind="sidebarCollapse"] svg {
    color: white !important;
    fill: white !important;
    width: 20px !important;
    height: 20px !important;
}

/* Nút mở sidebar khi đã đóng */
[data-testid="stSidebarNav"] button,
[data-testid="collapsedControl"] button {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px !important;
    padding: 10px !important;
    visibility: visible !important;
    display: flex !important;
}

[data-testid="collapsedControl"] button svg {
    color: white !important;
    fill: white !important;
}

/* Nút expand sidebar khi collapsed - cực kỳ rõ ràng */
[data-testid="stSidebarCollapsedControl"] {
    position: fixed !important;
    top: 10px !important;
    left: 10px !important;
    z-index: 9999 !important;
    display: block !important;
    visibility: visible !important;
}

[data-testid="stSidebarCollapsedControl"] button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: 2px solid white !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    min-width: 50px !important;
    min-height: 50px !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6),
        0 0 30px rgba(102, 126, 234, 0.3) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="stSidebarCollapsedControl"] button:hover {
    transform: scale(1.15) !important;
    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.8) !important;
}

[data-testid="stSidebarCollapsedControl"] button svg {
    color: white !important;
    fill: white !important;
    width: 24px !important;
    height: 24px !important;
}

/* Selector rộng hơn cho nút mở sidebar - Streamlit versions khác nhau */
button[aria-label*="sidebar"],
button[aria-label*="Expand"],
button[aria-label*="menu"],
[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"]+div button:first-of-type,
.stApp>header button:first-of-type {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: 2px solid white !important;
    border-radius: 10px !important;
    min-width: 44px !important;
    min-height: 44px !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6) !important;
    visibility: visible !important;
    opacity: 1 !important;
}

button[aria-label*="sidebar"] svg,
button[aria-label*="Expand"] svg,
button[aria-label*="menu"] svg {
    color: white !important;
    fill: white !important;
}

/* Sidebar Title */
[data-testid="stSidebar"] .stMarkdown h1 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.4rem !important;
    text-align: center;
    margin-bottom: 1.5rem !important;
    text-shadow: 0 2px 15px rgba(102, 126, 234, 0.4);
    letter-spacing: 0.5px;
}

/* Sidebar Radio Buttons - Navigation với chiều rộng bằng nhau */
[data-testid="stSidebar"] .stRadio>div {
    gap: 0.5rem !important;
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stSidebar"] .stRadio>div>label {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem 1.2rem !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
}

/* Force text color inside radio labels */
[data-testid="stSidebar"] .stRadio>div>label span,
[data-testid="stSidebar"] .stRadio>div>label p,
[data-testid="stSidebar"] .stRadio>div>label div,
[data-testid="stSidebar"] .stRadio label span {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

[data-testid="stSidebar"] .stRadio>div>label:hover {
    background: var(--glass-bg-hover) !important;
    border-color: var(--accent-primary) !important;
    transform: translateX(5px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
}

[data-testid="stSidebar"] .stRadio>div>label[data-checked="true"],
[data-testid="stSidebar"] .stRadio div[data-checked="true"]>label {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    border-color: transparent !important;
    box-shadow: 0 5px 25px rgba(102, 126, 234, 0.5) !important;
}

/* Hide radio circle */
[data-testid="stSidebar"] .stRadio input[type="radio"] {
    display: none !important;
}

/* Force all text in sidebar to be white */
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
}

/* ============================================
   MAIN CONTENT - Khu vực nội dung chính
   ============================================ */
.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1400px !important;
}

/* ============================================
   GLASSMORPHISM CONTAINERS
   ============================================ */
/* Glass Card Container */
.element-container {
    margin-bottom: 0.5rem;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: var(--glass-bg-strong) !important;
    backdrop-filter: blur(var(--blur-amount)) !important;
    -webkit-backdrop-filter: blur(var(--blur-amount)) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 32px var(--glass-shadow) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px var(--glass-shadow) !important;
    border-color: var(--accent-primary) !important;
}

[data-testid="stMetric"] label {
    color: var(--text-label) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.8rem !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* Expander / Accordion */
.streamlit-expanderHeader {
    background: var(--glass-bg-strong) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

.streamlit-expanderContent {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
}

/* ============================================
   TYPOGRAPHY - Font chữ to rõ, dễ đọc
   ============================================ */
.stMarkdown h1 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
    text-shadow: 0 3px 15px rgba(0, 0, 0, 0.4);
    letter-spacing: -0.5px;
}

.stMarkdown h2 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.8rem !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.stMarkdown h3 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.4rem !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}

.stMarkdown h4 {
    color: var(--text-label) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}

.stMarkdown h5 {
    color: var(--text-label) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    margin-top: 0.8rem !important;
    margin-bottom: 0.5rem !important;
}

.stMarkdown p,
.stMarkdown li {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem;
    /* Removed !important to allow overrides */
    line-height: 1.7 !important;
}

/* Sidebar Paragraphs (Subtitle, Footer) - Fix font size */
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown div {
    font-size: 11px !important;
    line-height: 1.4 !important;
    color: #e0e0e0 !important;
}

/* ============================================
   FORM ELEMENTS - Input, Select, Button
   Tăng độ tương phản và dễ đọc
   ============================================ */
/* Label chung cho tất cả form elements */
.stTextInput label,
.stSelectbox label,
.stDateInput label,
.stTextArea label,
.stNumberInput label,
.stRadio label,
.stCheckbox label {
    color: var(--text-label) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    margin-bottom: 0.3rem !important;
}

/* Text Input */
.stTextInput>div>div>input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    padding: 0.9rem 1rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput>div>div>input::placeholder {
    color: #666666 !important;
    font-weight: 400 !important;
}

.stTextInput>div>div>input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.25) !important;
    background: rgba(255, 255, 255, 0.95) !important;
}

/* Select Box */
.stSelectbox>div>div {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
}

.stSelectbox>div>div>div {
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
}

/* Date Input */
.stDateInput>div>div>input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    padding: 0.9rem 1rem !important;
}

/* Text Area */
.stTextArea textarea {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    padding: 0.9rem 1rem !important;
}

.stTextArea textarea::placeholder {
    color: #666666 !important;
    font-weight: 400 !important;
}

/* Number Input */
.stNumberInput>div>div>input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.9rem 2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.35) !important;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.stButton>button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5) !important;
}

.stButton>button:active {
    transform: translateY(-1px) !important;
}

/* Download Button */
.stDownloadButton>button {
    background: linear-gradient(135deg, var(--accent-success) 0%, #00b894 100%) !important;
    box-shadow: 0 5px 20px rgba(0, 217, 165, 0.35) !important;
}

.stDownloadButton>button:hover {
    box-shadow: 0 10px 30px rgba(0, 217, 165, 0.5) !important;
}

/* ============================================
   DATA DISPLAY - Tables, DataFrames
   Dark Glassmorphism Theme
   ============================================ */
.stDataFrame {
    background: var(--glass-bg-strong) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: transparent !important;
}

/* DataFrame container - làm tối nền */
.stDataFrame>div,
.stDataFrame [data-testid="glideDataEditor"],
.stDataFrame [data-testid="stDataFrameResizable"]>div {
    background: rgba(20, 20, 45, 0.95) !important;
}

/* Table Header - Header với gradient */
.stDataFrame thead th,
.stDataFrame [role="columnheader"],
.stDataFrame [data-testid="glideDataEditor"] [role="columnheader"] {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.35) 0%, rgba(118, 75, 162, 0.25) 100%) !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border-bottom: 1px solid var(--glass-border) !important;
    padding: 1rem 0.8rem !important;
}

/* Table Rows - Các hàng dữ liệu */
.stDataFrame tbody td,
.stDataFrame [role="gridcell"],
.stDataFrame [data-testid="glideDataEditor"] [role="gridcell"] {
    background: rgba(25, 25, 55, 0.9) !important;
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: 0.8rem !important;
}

/* Table Row Hover */
.stDataFrame tbody tr:hover td,
.stDataFrame [role="row"]:hover [role="gridcell"] {
    background: rgba(102, 126, 234, 0.15) !important;
    color: #ffffff !important;
}

/* Glide DataEditor specific - Streamlit's new data editor */
[data-testid="glideDataEditor"] {
    background: rgba(20, 20, 45, 0.95) !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="glideDataEditor"] canvas {
    background: transparent !important;
}

/* DataFrame scroll area */
.stDataFrame [data-testid="stDataFrameResizable"]>div>div {
    background: rgba(20, 20, 45, 0.95) !important;
}

/* Cell text colors */
.stDataFrame td,
.stDataFrame th,
.stDataFrame [role="cell"],
.stDataFrame [role="columnheader"] span {
    color: #ffffff !important;
}

/* ============================================
   TABS - Tab navigation
   ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--glass-bg-strong) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.6rem !important;
    border: 1px solid var(--glass-border) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.9rem 1.5rem !important;
    transition: all 0.3s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: var(--glass-bg-hover) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

/* Tab highlight bar */
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Tab panel content */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* ============================================
   ALERTS & MESSAGES
   ============================================ */
.stAlert {
    background: var(--glass-bg-strong) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(var(--blur-amount)) !important;
}

.stAlert>div {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
}

/* Success Alert */
div[data-testid="stAlert"][data-baseweb="notification"] {
    background: rgba(0, 217, 165, 0.15) !important;
    border-left: 4px solid var(--accent-success) !important;
}

/* Info Alert */
.stInfo {
    background: rgba(23, 162, 184, 0.15) !important;
    border-left: 4px solid var(--accent-info) !important;
}

/* Warning Alert */
.stWarning {
    background: rgba(255, 193, 7, 0.15) !important;
    border-left: 4px solid var(--accent-warning) !important;
}

/* Error Alert */
.stError {
    background: rgba(255, 107, 107, 0.15) !important;
    border-left: 4px solid var(--accent-danger) !important;
}

/* ============================================
   DIVIDER
   ============================================ */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent) !important;
    margin: 1.5rem 0 !important;
}

/* ============================================
   COLUMNS - Cân đối các cột
   ============================================ */
[data-testid="column"] {
    padding: 0 0.5rem !important;
}

/* ============================================
   FILE UPLOADER
   ============================================ */
.stFileUploader {
    background: var(--glass-bg) !important;
    border: 2px dashed var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
}

.stFileUploader:hover {
    border-color: var(--accent-primary) !important;
    background: var(--glass-bg-hover) !important;
}

/* ============================================
   SCROLLBAR - Custom scrollbar
   ============================================ */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 10px;
    border: 2px solid transparent;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary);
}

/* ============================================
   RESPONSIVE - Responsive design
   ============================================ */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }

    .stMarkdown h1 {
        font-size: 1.8rem !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }

    [data-testid="stSidebar"] {
        width: 280px !important;
    }
}

/* ============================================
   FORM SECTION STYLING
   ============================================ */
/* Form Section Header */
.form-section-header {
    background: linear-gradient(90deg, rgba(102, 126, 234, 0.2) 0%, transparent 100%);
    padding: 0.8rem 1rem;
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
    border-left: 4px solid var(--accent-primary);
}

/* ============================================
   SIDEBAR METRIC STYLING
   ============================================ */
[data-testid="stSidebar"] [data-testid="stMetric"] {
    background: rgba(102, 126, 234, 0.1) !important;
    padding: 1rem !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="stSidebar"] [data-testid="stMetric"] label {
    font-size: 0.85rem !important;
}

[data-testid="stSidebar"] [data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 2rem !important;
}

/* ============================================
   CUSTOM GLASS CARD CLASS
   ============================================ */
.glass-card {
    background: var(--glass-bg-strong);
    backdrop-filter: blur(var(--blur-amount));
    -webkit-backdrop-filter: blur(var(--blur-amount));
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 2rem;
    box-shadow: 0 8px 32px var(--glass-shadow);
}

/* ============================================
   CHECKBOX & RADIO STYLING
   ============================================ */
.stCheckbox>label>span {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
}

/* ============================================
   Hide Streamlit branding
   ============================================ */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

/* Show deploy button for development */
/* .stDeployButton {display: block !important;} */

/* ============================================
   EXPANDER - Nút mở rộng (Thêm liên hệ, tài khoản, phương tiện)
   ============================================ */
/* Expander container */
div[data-testid="stExpander"] {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.15) 100%) !important;
    border: 1px solid rgba(102, 126, 234, 0.5) !important;
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(10px) !important;
    margin: 10px 0 !important;
    overflow: hidden;
}

/* Expander header (nút bấm) */
div[data-testid="stExpander"]>details>summary {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.2) 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;
}

/* Expander header hover */
div[data-testid="stExpander"]>details>summary:hover {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.5) 0%, rgba(118, 75, 162, 0.35) 100%) !important;
    border-color: rgba(102, 126, 234, 0.8) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

/* Expander icon (mũi tên) */
div[data-testid="stExpander"]>details>summary svg {
    color: white !important;
    fill: white !important;
}

/* Expander content (nội dung bên trong) */
div[data-testid="stExpander"]>details>div {
    background: rgba(20, 20, 40, 0.6) !important;
    border-top: 1px solid rgba(102, 126, 234, 0.3) !important;
    padding: 16px !important;
}

/* Expander khi mở */
div[data-testid="stExpander"]>details[open] {
    border-color: rgba(102, 126, 234, 0.7) !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2) !important;
}

div[data-testid="stExpander"]>details[open]>summary {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.4) 0%, rgba(118, 75, 162, 0.3) 100%) !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
}

/* ============================================
   TABS - Styling cho st.tabs
   ============================================ */
/* Tab container */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background: rgba(20, 20, 40, 0.6) !important;
    border-radius: var(--radius-md) !important;
    padding: 8px !important;
}

/* Tab buttons - mặc định */
.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: var(--radius-sm) !important;
    color: rgba(255, 255, 255, 0.7) !important;
    font-weight: 500 !important;
    padding: 10px 16px !important;
    transition: all 0.3s ease !important;
}

/* Tab buttons - hover */
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(102, 126, 234, 0.2) !important;
    border-color: rgba(102, 126, 234, 0.5) !important;
    color: white !important;
}

/* Tab buttons - active/selected */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.7) 100%) !important;
    border-color: transparent !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
}

/* Tab buttons - NOT selected (fix highlight issue) */
.stTabs [data-baseweb="tab"][aria-selected="false"] {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
    color: rgba(255, 255, 255, 0.6) !important;
    box-shadow: none !important;
}

/* Tab content panel */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 16px !important;
}

/* Remove default tab highlight indicator */
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Nested tabs (tabs trong tabs) styling */
.stTabs .stTabs [data-baseweb="tab-list"] {
    background: rgba(30, 30, 60, 0.4) !important;
}

.stTabs .stTabs [data-baseweb="tab"] {
    font-size: 0.9rem !important;
    padding: 8px 12px !important;
}

/* ============================================
   FILE UPLOADER & TÀI LIỆU ĐÍNH KÈM
   ============================================ */

/* File uploader container */
[data-testid="stFileUploader"] {
    background: rgba(30, 30, 60, 0.6) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
}

/* File uploader text */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    color: #ffffff !important;
}

/* File uploader drag area */
[data-testid="stFileUploader"] section {
    border-color: rgba(102, 126, 234, 0.5) !important;
    background: rgba(40, 40, 80, 0.4) !important;
}

[data-testid="stFileUploader"] section:hover {
    border-color: rgba(102, 126, 234, 0.8) !important;
    background: rgba(50, 50, 90, 0.5) !important;
}

/* File name display */
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
    color: #ffffff !important;
}

/* Uploaded file info */
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] [class*="uploadedFileName"] {
    color: #e0e0e0 !important;
}

/* Expander for "Upload tài liệu mới" */
.stExpander {
    background: rgba(30, 30, 60, 0.5) !important;
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    border-radius: var(--radius-md) !important;
}

.stExpander summary {
    color: #ffffff !important;
    font-weight: 600 !important;
}

.stExpander [data-testid="stExpanderDetails"] {
    background: rgba(20, 20, 50, 0.3) !important;
}

/* Caption text color */
.stCaption,
[data-testid="stCaptionContainer"] {
    color: #b0b0ff !important;
}

/* ============================================
   FILE UPLOADER - ENSURE WHITE TEXT
   ============================================ */
/* Uploaded file name - all possible selectors */
[data-testid="stFileUploader"] * {
    color: #ffffff !important;
}

[data-testid="stFileUploader"] div[data-testid] span,
[data-testid="stFileUploader"] button span,
[data-testid="stFileUploader"] [class*="FileName"],
[data-testid="stFileUploader"] [class*="fileName"],
[data-testid="stFileUploader"] [class*="file-name"],
[data-testid="stFileUploader"] small {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* File size info */
[data-testid="stFileUploader"] [class*="fileSize"],
[data-testid="stFileUploader"] [class*="FileSize"] {
    color: #b0b0ff !important;
}

/* Delete button X icon */
[data-testid="stFileUploader"] button[kind="secondary"] {
    color: #ff6b6b !important;
    background: rgba(255, 107, 107, 0.2) !important;
    border: 1px solid rgba(255, 107, 107, 0.5) !important;
}
```

## .agent/workflows/full-power.md
---
description: Chạy các lệnh phát triển với toàn quyền (không cần hỏi)
---

// turbo-all

Sử dụng workflow này để thực hiện các tác vụ phát triển mà không cần xác nhận thủ công.

### 1. Cài đặt môi trường
Chạy lệnh này để cài đặt các package cần thiết:
```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng Streamlit
Khởi động giao diện quản lý:
```bash
streamlit run app.py
```

### 3. Import dữ liệu mẫu
Chạy script import dữ liệu:
```bash
python bulk_import.py
```

### 4. Kiểm tra Database
Chạy script kiểm tra cơ sở dữ liệu:
```bash
python database.py
```


## app/init_db.py
```py

import logging
from app.db.session import engine
from app.db.base import Base
# Import models to register them with metadata
from app.models.models import User, DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan, HoSoDacThu, TaiLieu, QuaTrinhHoatDong, NguonDuLieu, QuanHeDoiTuong, AuditLog

logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e

```

## app/__init__.py
```py
# App package

```

## app/core/config.py
```py

import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Security Profile 360"
    PROJECT_VERSION: str = "2.0.0"
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Database
    DB_NAME = "security_profile.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{BASE_DIR}/{DB_NAME}"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()

```

## app/core/__init__.py
```py
# App Core Package

```

## app/db/base.py
```py

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

```

## app/db/session.py
```py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine
# check_same_thread=False is needed for SQLite in multi-threaded envs like Streamlit
connect_args = {"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URI else {}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```

## app/db/__init__.py
```py
# App Database Package

```

## app/models/models.py
```py

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base

# ============================================
# Core Person Model
# ============================================
class DoiTuong(Base):
    __tablename__ = "doi_tuong"

    cccd: Mapped[str] = mapped_column(String, primary_key=True)
    ho_ten: Mapped[Optional[str]] = mapped_column(String)
    ngay_sinh: Mapped[Optional[datetime]] = mapped_column(Date)
    gioi_tinh: Mapped[Optional[str]] = mapped_column(String)
    dia_chi_tinh: Mapped[Optional[str]] = mapped_column(String, default="Phú Thọ")
    dia_chi_xa: Mapped[Optional[str]] = mapped_column(String)
    anh_chan_dung: Mapped[Optional[str]] = mapped_column(String)
    phan_loai_nghe_nghiep: Mapped[Optional[str]] = mapped_column(String)
    chi_tiet_nghe_nghiep: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu_chung: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    lien_he: Mapped[List["LienHe"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    tai_chinh: Mapped[List["TaiChinh"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    phuong_tien: Mapped[List["PhuongTien"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    nhan_than: Mapped[List["NhanThan"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    ho_so_dac_thu: Mapped[List["HoSoDacThu"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    tai_lieu: Mapped[List["TaiLieu"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    qua_trinh: Mapped[List["QuaTrinhHoatDong"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")


# ============================================
# Satellite Models
# ============================================
class LienHe(Base):
    __tablename__ = "lien_he"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_lien_he: Mapped[Optional[str]] = mapped_column(String) # SDT, Email, Facebook...
    gia_tri: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="lien_he")

class TaiChinh(Base):
    __tablename__ = "tai_chinh"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    ngan_hang: Mapped[Optional[str]] = mapped_column(String)
    so_tai_khoan: Mapped[Optional[str]] = mapped_column(String)
    chu_tai_khoan: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="tai_chinh")

class PhuongTien(Base):
    __tablename__ = "phuong_tien"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_xe: Mapped[Optional[str]] = mapped_column(String)
    bien_kiem_soat: Mapped[Optional[str]] = mapped_column(String)
    ten_phuong_tien: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="phuong_tien")

class NhanThan(Base):
    __tablename__ = "nhan_than"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_quan_he: Mapped[str] = mapped_column(String) # Bo, Me, Vo, Chong
    ho_ten: Mapped[Optional[str]] = mapped_column(String)
    cccd_nhan_than: Mapped[Optional[str]] = mapped_column(String)
    ngay_sinh: Mapped[Optional[datetime]] = mapped_column(Date)
    nghe_nghiep: Mapped[Optional[str]] = mapped_column(String)
    noi_o: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="nhan_than")

class HoSoDacThu(Base):
    __tablename__ = "ho_so_dac_thu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_hinh: Mapped[str] = mapped_column(String)
    noi_dung_chi_tiet: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="ho_so_dac_thu")

class TaiLieu(Base):
    __tablename__ = "tai_lieu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    ten_file_goc: Mapped[Optional[str]] = mapped_column(String)
    ten_file_luu: Mapped[Optional[str]] = mapped_column(String)
    duong_dan: Mapped[Optional[str]] = mapped_column(String)
    loai_tai_lieu: Mapped[Optional[str]] = mapped_column(String)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    dung_luong: Mapped[Optional[int]] = mapped_column(Integer)
    dinh_dang: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="tai_lieu")

class QuaTrinhHoatDong(Base):
    __tablename__ = "qua_trinh_hoat_dong"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    thoi_gian: Mapped[Optional[str]] = mapped_column(String)
    noi_dung: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="qua_trinh")

# ============================================
# System Models
# ============================================
class NguonDuLieu(Base):
    __tablename__ = "nguon_du_lieu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ten_nguon: Mapped[str] = mapped_column(String)
    loai_nguon: Mapped[Optional[str]] = mapped_column(String)
    thoi_gian_import: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    nguoi_import: Mapped[Optional[str]] = mapped_column(String)
    file_goc: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)

class QuanHeDoiTuong(Base):
    __tablename__ = "quan_he_doi_tuong"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd_1: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    cccd_2: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_quan_he: Mapped[Optional[str]] = mapped_column(String)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    nguon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nguon_du_lieu.id"))
    do_tin_cay: Mapped[Optional[int]] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bang: Mapped[str] = mapped_column(String)
    hanh_dong: Mapped[str] = mapped_column(String)
    khoa_chinh: Mapped[Optional[str]] = mapped_column(String)
    du_lieu_cu: Mapped[Optional[str]] = mapped_column(Text)
    du_lieu_moi: Mapped[Optional[str]] = mapped_column(Text)
    nguoi_thuc_hien: Mapped[Optional[str]] = mapped_column(String)
    ip_address: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    ho_ten: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String, default='user')
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    must_change_password: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

```

## app/models/__init__.py
```py
# App Models Package

```

## app/services/auth_service.py
```py

import bcrypt
import os
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.models.models import User

logger = logging.getLogger(__name__)

# Roles
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_USER = 'user'
DEFAULT_ADMIN_USERNAME = 'admin'

def get_db():
    return SessionLocal()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False

def authenticate(username: str, password: str) -> Optional[Dict]:
    db = get_db()
    try:
        stmt = select(User).where(User.username == username, User.is_active == 1)
        user = db.execute(stmt).scalar_one_or_none()
        
        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            db.commit()
            return {
                'id': user.id,
                'username': user.username,
                'ho_ten': user.ho_ten or user.username,
                'role': user.role,
                'must_change_password': bool(user.must_change_password)
            }
        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        db.close()

def create_user(username: str, password: str, ho_ten: str = "", role: str = ROLE_USER, must_change_password: bool = False) -> Tuple[bool, str]:
    if not username or not password:
        return False, "Username và password không được trống"
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
        
    db = get_db()
    try:
        stmt = select(User).where(User.username == username)
        if db.execute(stmt).scalar_one_or_none():
            return False, f"Username '{username}' đã tồn tại"
            
        password_hash = hash_password(password)
        new_user = User(
            username=username,
            password_hash=password_hash,
            ho_ten=ho_ten,
            role=role,
            must_change_password=int(must_change_password)
        )
        db.add(new_user)
        db.commit()
        logger.info(f"Đã tạo user: {username} (role: {role})")
        return True, f"Đã tạo tài khoản '{username}' thành công"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi tạo user: {e}")
        return False, f"Lỗi tạo tài khoản: {e}"
    finally:
        db.close()

def delete_user(user_id: int) -> Tuple[bool, str]:
    db = get_db()
    try:
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()
        
        if not user:
            return False, "Không tìm thấy tài khoản"

        # Check super admin count
        stmt_count = select(func.count(User.id)).where(User.role == ROLE_SUPER_ADMIN, User.is_active == 1, User.id != user_id)
        admin_count = db.execute(stmt_count).scalar_one()

        if user.role == ROLE_SUPER_ADMIN and admin_count == 0:
            return False, "Không thể xóa Super Admin cuối cùng"

        user.is_active = 0
        db.commit()
        return True, f"Đã xóa tài khoản '{user.username}'"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi xóa user: {e}")
        return False, f"Lỗi xóa tài khoản: {e}"
    finally:
        db.close()

def change_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
        
    db = get_db()
    try:
        user = db.get(User, user_id)
        if not user:
             return False, "User not found"
             
        user.password_hash = hash_password(new_password)
        user.must_change_password = 0
        db.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi đổi mật khẩu: {e}")
        return False, f"Lỗi đổi mật khẩu: {e}"
    finally:
        db.close()

def get_all_users() -> List[Dict]:
    db = get_db()
    try:
        stmt = select(User).where(User.is_active == 1).order_by(User.created_at.desc())
        users = db.execute(stmt).scalars().all()
        return [
            {
                'id': u.id,
                'username': u.username,
                'ho_ten': u.ho_ten,
                'role': u.role,
                'created_at': u.created_at,
                'last_login': u.last_login
            } for u in users
        ]
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách users: {e}")
        return []
    finally:
        db.close()

def init_super_admin():
    db = get_db()
    try:
        stmt = select(func.count(User.id))
        count = db.execute(stmt).scalar_one()
        
        if count == 0:
            env_password = os.environ.get('ADMIN_PASSWORD')
            if env_password:
                password = env_password
                is_generated = False
            else:
                password = secrets.token_urlsafe(16)
                is_generated = True
                
            password_hash = hash_password(password)
            super_admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=password_hash,
                ho_ten='Administrator',
                role=ROLE_SUPER_ADMIN,
                must_change_password=1
            )
            db.add(super_admin)
            db.commit()
            
            logger.info(f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")
            if is_generated:
                print("="*60)
                print(f"[SECURITY NOTICE] Generated Random Super Admin Password")
                print(f"Username: {DEFAULT_ADMIN_USERNAME}")
                print(f"Password: {password}")
                print("="*60)
    except Exception as e:
        logger.error(f"Lỗi init super admin: {e}")
    finally:
        db.close()

def is_super_admin(user: Dict) -> bool:
    if not user:
        return False
    return user.get('role') == ROLE_SUPER_ADMIN

```

## app/services/__init__.py
```py
# Services package

```

## utils/deduplication.py
```py
# -*- coding: utf-8 -*-
"""
Module Khử trùng lặp dữ liệu - Security Profile 360
Áp dụng patterns từ dedupe library: Record Linkage, Blocking, Clustering
"""
from rapidfuzz import fuzz
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
import re

# Trọng số cho các trường (weight) - Pattern từ dedupe
FIELD_WEIGHTS = {
    'cccd': 100,        # CCCD trùng = chắc chắn cùng người
    'ho_ten': 40,       # Tên quan trọng
    'ngay_sinh': 30,    # Ngày sinh
    'sdt': 25,          # SĐT
    'dia_chi': 10,      # Địa chỉ ít quan trọng nhất
}

# Ngưỡng (User-approved: 80%)
DUPLICATE_THRESHOLD = 80


def normalize_phone(phone: str) -> str:
    """
    Chuẩn hóa SĐT về định dạng chuẩn.
    Ví dụ: 0912345678 -> 84912345678
    """
    if not phone:
        return ""
    phone = ''.join(c for c in str(phone) if c.isdigit())
    if phone.startswith('0'):
        phone = '84' + phone[1:]
    return phone


def normalize_name(name: str) -> str:
    """Chuẩn hóa tên để so sánh."""
    if not name:
        return ""
    name = str(name).lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def compare_records(record1: dict, record2: dict) -> dict:
    """
    So sánh 2 bản ghi theo nhiều trường.

    Pattern: Record Linkage từ dedupe
    - Mỗi trường có trọng số khác nhau
    - Tính điểm tổng hợp có trọng số

    Returns:
        Dict với field_scores, overall_score, is_duplicate
    """
    scores = {}
    weighted_sum = 0
    total_weight = 0

    # So sánh CCCD (exact match - quan trọng nhất)
    if record1.get('cccd') and record2.get('cccd'):
        cccd1 = str(record1['cccd']).strip()
        cccd2 = str(record2['cccd']).strip()
        if cccd1 == cccd2:
            scores['cccd'] = 100
        else:
            scores['cccd'] = 0
        weighted_sum += scores['cccd'] * FIELD_WEIGHTS['cccd']
        total_weight += FIELD_WEIGHTS['cccd']

    # So sánh họ tên (fuzzy match)
    if record1.get('ho_ten') and record2.get('ho_ten'):
        scores['ho_ten'] = fuzz.token_set_ratio(
            normalize_name(record1['ho_ten']),
            normalize_name(record2['ho_ten'])
        )
        weighted_sum += scores['ho_ten'] * FIELD_WEIGHTS['ho_ten']
        total_weight += FIELD_WEIGHTS['ho_ten']

    # So sánh ngày sinh (exact match)
    if record1.get('ngay_sinh') and record2.get('ngay_sinh'):
        dob1 = str(record1['ngay_sinh']).strip()
        dob2 = str(record2['ngay_sinh']).strip()
        if dob1 == dob2:
            scores['ngay_sinh'] = 100
        else:
            scores['ngay_sinh'] = 0
        weighted_sum += scores['ngay_sinh'] * FIELD_WEIGHTS['ngay_sinh']
        total_weight += FIELD_WEIGHTS['ngay_sinh']

    # So sánh SĐT (normalized match)
    sdt1 = record1.get('sdt') or record1.get(
        'gia_tri')  # Có thể ở bảng lien_he
    sdt2 = record2.get('sdt') or record2.get('gia_tri')
    if sdt1 and sdt2:
        phone1 = normalize_phone(sdt1)
        phone2 = normalize_phone(sdt2)
        if phone1 and phone2:
            if phone1 == phone2:
                scores['sdt'] = 100
            else:
                scores['sdt'] = 0
            weighted_sum += scores['sdt'] * FIELD_WEIGHTS['sdt']
            total_weight += FIELD_WEIGHTS['sdt']

    # So sánh địa chỉ (fuzzy match)
    addr1 = record1.get('dia_chi_xa') or record1.get('dia_chi')
    addr2 = record2.get('dia_chi_xa') or record2.get('dia_chi')
    if addr1 and addr2:
        scores['dia_chi'] = fuzz.token_set_ratio(
            normalize_name(str(addr1)),
            normalize_name(str(addr2))
        )
        weighted_sum += scores['dia_chi'] * FIELD_WEIGHTS['dia_chi']
        total_weight += FIELD_WEIGHTS['dia_chi']

    # Tính điểm tổng hợp
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0

    return {
        'field_scores': scores,
        'overall_score': round(overall_score, 2),
        'is_duplicate': overall_score >= DUPLICATE_THRESHOLD
    }


def block_by_birth_year(records: List[dict]) -> Dict[str, List[Tuple[int, dict]]]:
    """
    Blocking - Nhóm theo năm sinh trước khi so sánh.

    Pattern từ dedupe: Giảm số cặp cần so sánh từ O(n²) xuống O(n).
    Chỉ so sánh các bản ghi trong cùng block.

    Returns:
        Dict mapping year -> list of (original_index, record) tuples
    """
    blocks = defaultdict(list)

    for idx, record in enumerate(records):
        dob = record.get('ngay_sinh')
        if dob:
            # Extract year từ nhiều format khác nhau
            dob_str = str(dob)
            if len(dob_str) >= 4:
                year = dob_str[:4]  # Assume YYYY-MM-DD or YYYY/MM/DD
                if year.isdigit():
                    blocks[year].append((idx, record))
                    continue

        # Nếu không có ngày sinh, đưa vào block 'unknown'
        blocks['unknown'].append((idx, record))

    return dict(blocks)


def find_duplicates_in_batch(records: List[dict]) -> List[Tuple[int, int, dict]]:
    """
    Tìm các cặp trùng lặp trong batch import.

    Pattern: Blocking + Pairwise comparison

    Returns:
        List of (index1, index2, comparison_result) tuples
    """
    duplicates = []
    blocks = block_by_birth_year(records)

    for block_key, block_records in blocks.items():
        n = len(block_records)
        for i in range(n):
            for j in range(i + 1, n):
                idx1, rec1 = block_records[i]
                idx2, rec2 = block_records[j]

                comparison = compare_records(rec1, rec2)
                if comparison['is_duplicate']:
                    duplicates.append((idx1, idx2, comparison))

    return duplicates


def cluster_duplicates(duplicates: List[Tuple[int, int, dict]]) -> List[Set[int]]:
    """
    Clustering - Gom các bản ghi trùng thành nhóm.

    Pattern từ dedupe: Union-Find algorithm
    Nếu A trùng B, B trùng C thì {A, B, C} là 1 cluster.

    Returns:
        List of sets, each set contains indices of duplicate records
    """
    if not duplicates:
        return []

    # Union-Find algorithm
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Link all duplicate pairs
    for i, j, _ in duplicates:
        union(i, j)

    # Group by cluster root
    clusters = defaultdict(set)
    for idx in parent.keys():
        clusters[find(idx)].add(idx)

    # Only return clusters with more than 1 record
    return [cluster for cluster in clusters.values() if len(cluster) > 1]


def merge_duplicate_cluster(records: List[dict], cluster: Set[int]) -> dict:
    """
    Merge các bản ghi trùng thành 1 bản ghi duy nhất.

    Strategy: Ưu tiên giá trị không rỗng, giá trị xuất hiện nhiều nhất.

    Returns:
        Merged record
    """
    cluster_records = [records[i] for i in cluster]
    merged = {}

    # Các trường cần merge
    fields = ['cccd', 'ho_ten', 'ngay_sinh', 'gioi_tinh', 'dia_chi_xa',
              'phan_loai_nghe_nghiep', 'chi_tiet_nghe_nghiep', 'ghi_chu_chung']

    for field in fields:
        values = [r.get(field) for r in cluster_records if r.get(field)]
        if values:
            # Ưu tiên giá trị xuất hiện nhiều nhất
            merged[field] = max(set(values), key=values.count)

    return merged


def deduplicate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[dict]]:
    """
    API chính cho việc khử trùng batch import từ DataFrame.

    Args:
        df: DataFrame chứa dữ liệu cần khử trùng

    Returns:
        (cleaned_df, duplicate_report)
        - cleaned_df: DataFrame đã loại bỏ trùng lặp
        - duplicate_report: Báo cáo chi tiết về các bản ghi trùng
    """
    records = df.to_dict('records')

    # Tìm các cặp trùng
    duplicates = find_duplicates_in_batch(records)

    if not duplicates:
        return df, []

    # Gom nhóm
    clusters = cluster_duplicates(duplicates)

    duplicate_report = []
    indices_to_remove = set()

    for cluster in clusters:
        if len(cluster) > 1:
            cluster_list = sorted(cluster)
            keep_idx = cluster_list[0]  # Giữ bản ghi đầu tiên
            remove_indices = cluster_list[1:]

            indices_to_remove.update(remove_indices)

            duplicate_report.append({
                'kept_index': keep_idx,
                'kept_record': records[keep_idx],
                'removed_indices': remove_indices,
                'removed_records': [records[i] for i in remove_indices],
                'cluster_size': len(cluster)
            })

    # Xóa các bản ghi trùng
    cleaned_df = df.drop(index=list(indices_to_remove)).reset_index(drop=True)

    return cleaned_df, duplicate_report


def generate_duplicate_report(duplicate_report: List[dict]) -> str:
    """
    Tạo báo cáo text về các bản ghi trùng lặp.
    """
    if not duplicate_report:
        return "✅ Không phát hiện trùng lặp."

    lines = [f"⚠️ Phát hiện {len(duplicate_report)} nhóm trùng lặp:"]
    lines.append("")

    for i, group in enumerate(duplicate_report, 1):
        kept = group['kept_record']
        removed_count = len(group['removed_records'])

        lines.append(f"**Nhóm {i}**: {group['cluster_size']} bản ghi")
        lines.append(
            f"  - Giữ lại: {kept.get('ho_ten', 'N/A')} (CCCD: {kept.get('cccd', 'N/A')})")
        lines.append(f"  - Loại bỏ: {removed_count} bản ghi trùng")
        lines.append("")

    return "\n".join(lines)

```

## utils/fuzzy_matching.py
```py
# -*- coding: utf-8 -*-
"""
Module Fuzzy Matching cho tiếng Việt - Security Profile 360
Áp dụng patterns từ thefuzz/rapidfuzz với ngưỡng 80%
"""
from rapidfuzz import fuzz, process
import unicodedata
import re
from typing import List, Dict, Optional, Tuple

# Ngưỡng độ tương đồng (User-approved: 80%)
THRESHOLD_EXACT = 95      # Khớp chính xác
THRESHOLD_SUSPECT = 80    # Nghi vấn - cần kiểm tra (ngưỡng chính)
THRESHOLD_LOW = 60        # Có thể liên quan


def normalize_vietnamese(text: str) -> str:
    """
    Chuẩn hóa chuỗi tiếng Việt:
    - Chuyển lowercase
    - Loại bỏ dấu câu thừa
    - Giữ nguyên dấu tiếng Việt
    """
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def remove_vietnamese_diacritics(text: str) -> str:
    """
    Chuyển đổi chữ có dấu thành không dấu.
    Ví dụ: 'Nguyễn Văn An' -> 'Nguyen Van An'
    """
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))


def compare_names(name1: str, name2: str) -> Dict[str, int]:
    """
    So sánh 2 tên với nhiều thuật toán khác nhau.
    Returns dict với các loại score khác nhau (0-100).

    Pattern từ thefuzz:
    - ratio: Levenshtein distance cơ bản
    - partial_ratio: So sánh substring
    - token_sort: Sắp xếp từ trước khi so sánh
    - token_set: Bỏ qua thứ tự và từ trùng
    - weighted: Tự động chọn thuật toán tốt nhất
    """
    n1 = normalize_vietnamese(name1)
    n2 = normalize_vietnamese(name2)

    if not n1 or not n2:
        return {
            'ratio': 0,
            'partial_ratio': 0,
            'token_sort': 0,
            'token_set': 0,
            'weighted': 0,
            'best': 0
        }

    scores = {
        'ratio': fuzz.ratio(n1, n2),
        'partial_ratio': fuzz.partial_ratio(n1, n2),
        'token_sort': fuzz.token_sort_ratio(n1, n2),
        'token_set': fuzz.token_set_ratio(n1, n2),
        'weighted': fuzz.WRatio(n1, n2),
    }
    scores['best'] = max(scores.values())

    return scores


def find_similar_names(
    query: str,
    candidates: List[str],
    threshold: int = THRESHOLD_SUSPECT,
    limit: int = 10
) -> List[Dict]:
    """
    Tìm các tên tương tự trong danh sách.

    Pattern: extractOne với custom scorer (token_set_ratio)
    Đặc biệt phù hợp cho tiếng Việt vì bỏ qua thứ tự họ/tên.

    Args:
        query: Tên cần tìm
        candidates: Danh sách tên để so sánh
        threshold: Ngưỡng tối thiểu (mặc định 80%)
        limit: Số kết quả tối đa

    Returns:
        List of dicts với {name, score, index}
    """
    if not candidates or not query:
        return []

    normalized_query = normalize_vietnamese(query)

    if not normalized_query:
        return []

    # Sử dụng token_set_ratio - tốt nhất cho tiếng Việt
    results = process.extract(
        normalized_query,
        candidates,
        scorer=fuzz.token_set_ratio,
        limit=limit
    )

    return [
        {'name': name, 'score': score, 'index': idx}
        for name, score, idx in results
        if score >= threshold
    ]


def classify_match(score: int) -> Tuple[str, str]:
    """
    Phân loại kết quả match dựa trên score.

    Returns:
        (status_text, status_type)
    """
    if score >= THRESHOLD_EXACT:
        return ('✅ Khớp chính xác', 'exact')
    elif score >= THRESHOLD_SUSPECT:
        return ('⚠️ Nghi vấn - cần kiểm tra', 'suspect')
    elif score >= THRESHOLD_LOW:
        return ('🔍 Có thể liên quan', 'related')
    else:
        return ('❌ Không khớp', 'no_match')


def batch_screen(
    input_names: List[str],
    database_names: List[str],
    threshold: int = THRESHOLD_SUSPECT
) -> List[Dict]:
    """
    Rà soát hàng loạt - So sánh danh sách đầu vào với database.

    Pattern từ process.extractWithoutOrder của thefuzz.

    Args:
        input_names: Danh sách tên cần rà soát
        database_names: Danh sách tên trong database
        threshold: Ngưỡng (mặc định 80%)

    Returns:
        List of screening results
    """
    results = []

    for query in input_names:
        if not query or not str(query).strip():
            continue

        query = str(query).strip()
        matches = find_similar_names(query, database_names, threshold)

        if matches:
            best = matches[0]
            status, status_type = classify_match(best['score'])
            results.append({
                'input': query,
                'matched': best['name'],
                'score': best['score'],
                'status': status,
                'status_type': status_type,
                'alternatives': matches[1:5]  # Top 4 alternatives
            })
        else:
            results.append({
                'input': query,
                'matched': None,
                'score': 0,
                'status': '❌ Không tìm thấy',
                'status_type': 'not_found',
                'alternatives': []
            })

    return results


def find_potential_duplicates(names: List[str], threshold: int = THRESHOLD_SUSPECT) -> List[Dict]:
    """
    Tìm các cặp tên có thể trùng lặp trong danh sách.
    Phục vụ cho việc khử trùng khi import Excel.

    Args:
        names: Danh sách tên
        threshold: Ngưỡng coi là trùng (mặc định 80%)

    Returns:
        List of potential duplicate pairs
    """
    duplicates = []
    n = len(names)

    for i in range(n):
        for j in range(i + 1, n):
            if not names[i] or not names[j]:
                continue

            score = fuzz.token_set_ratio(
                normalize_vietnamese(names[i]),
                normalize_vietnamese(names[j])
            )

            if score >= threshold:
                duplicates.append({
                    'index_1': i,
                    'index_2': j,
                    'name_1': names[i],
                    'name_2': names[j],
                    'score': score,
                    'status': classify_match(score)[0]
                })

    return duplicates


# Convenience functions for common use cases
def quick_match(name1: str, name2: str) -> int:
    """Quick match score between two names using WRatio."""
    return fuzz.WRatio(
        normalize_vietnamese(name1),
        normalize_vietnamese(name2)
    )


def is_likely_same_person(name1: str, name2: str, threshold: int = THRESHOLD_SUSPECT) -> bool:
    """Check if two names likely belong to the same person."""
    return quick_match(name1, name2) >= threshold

```

## utils/security_utils.py
```py
# -*- coding: utf-8 -*-
"""
Security Utility Functions
"""
import pandas as pd

def sanitize_for_csv(value):
    """
    Sanitize a value to prevent CSV Injection (Excel Formula Injection).
    Prepends a single quote (') if the value starts with =, +, -, or @.
    """
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def sanitize_dataframe_for_csv(df):
    """
    Sanitize all string columns in a DataFrame to prevent CSV Injection.
    Returns a new DataFrame with sanitized values.
    """
    if df is None:
        return None

    # Create a copy to avoid modifying the original dataframe
    df_sanitized = df.copy()

    # Apply sanitization to object (string) columns
    for col in df_sanitized.select_dtypes(include=['object']).columns:
        df_sanitized[col] = df_sanitized[col].apply(sanitize_for_csv)

    return df_sanitized

```

## utils/text_utils.py
```py
# -*- coding: utf-8 -*-
"""
Text Utility Functions
"""
import unicodedata
import re


def remove_accents(input_str):
    """
    Loại bỏ dấu tiếng Việt
    """
    if not input_str:
        return ""
    # Thay thế Đ/đ
    s1 = u'Đ'.encode('utf-8')
    s2 = u'đ'.encode('utf-8')
    input_str = input_str.replace(
        s1.decode('utf-8'), 'D').replace(s2.decode('utf-8'), 'd')
    # Chuẩn hóa NFD và loại bỏ ký tự combining marks (dấu)
    return ''.join(c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn')


def normalize_string(s):
    """
    Chuẩn hóa chuỗi cho tìm kiếm: bỏ dấu, thường, bỏ khoảng trắng và ký tự đặc biệt
    Ví dụ: "Nguyễn Văn A" -> "nguyenvana"
    """
    if not s:
        return ""
    s = remove_accents(s).lower()
    return re.sub(r'[^a-z0-9]', '', s)

```

## utils/__init__.py
```py

```

## utils/bulk_import/constants.py
```py
# -*- coding: utf-8 -*-

# Định nghĩa cấu trúc cột cho từng loại CSXH
CSXH_TEMPLATES = {
    "Hon_Nhan_NN": {
        "name": "Hôn nhân với người nước ngoài",
        "headers": ["CCCD (*)", "Quốc tịch người nước ngoài (*)", "Họ tên người nước ngoài (*)",
                    "Năm kết hôn", "Nơi đăng ký kết hôn", "Tình trạng hiện tại",
                    "Địa chỉ hiện tại", "Ghi chú"],
        "sample": ["001234567890", "Trung Quốc", "WANG Xiaoming",
                   "2020", "UBND TP Việt Trì", "Đang chung sống",
                   "Xã Thanh Ba, huyện Thanh Ba, Phú Thọ", "Đang theo dõi"]
    },
    "Lam_Viec_NN": {
        "name": "Làm việc cho tổ chức nước ngoài",
        "headers": ["CCCD (*)", "Tên tổ chức (*)", "Quốc gia gốc của tổ chức (*)",
                    "Loại hình (FDI/NGO/Khác)", "Vị trí công việc",
                    "Năm bắt đầu", "Năm kết thúc", "Địa chỉ làm việc", "Ghi chú"],
        "sample": ["001234567890", "Samsung Electronics Vietnam", "Hàn Quốc",
                   "FDI", "Kỹ sư phần mềm",
                   "2018", "2023", "KCN Yên Phong, Bắc Ninh", ""]
    },
    "Hoc_Tap_Cong_Tac_NN": {
        "name": "Du học - Công tác nước ngoài",
        "headers": ["CCCD (*)", "Quốc gia (*)", "Tên trường/Tổ chức (*)",
                    "Hình thức (Du học/Công tác/Thuê lao động)", "Chuyên ngành/Công việc",
                    "Năm đi", "Năm về", "Nguồn tài trợ", "Ghi chú"],
        "sample": ["001234567890", "Nhật Bản", "Đại học Tokyo",
                   "Du học", "Thạc sĩ CNTT",
                   "2015", "2019", "Học bổng MEXT", ""]
    },
    "Vi_Pham_NN": {
        "name": "Vi phạm pháp luật ở nước ngoài",
        "headers": ["CCCD (*)", "Quốc gia xảy ra vi phạm (*)", "Năm vi phạm (*)",
                    "Loại vi phạm", "Nội dung chi tiết",
                    "Hình thức xử lý", "Tình trạng hiện tại", "Ghi chú"],
        "sample": ["001234567890", "Đài Loan", "2014",
                   "Cư trú bất hợp pháp", "Ở quá hạn visa 30 ngày",
                   "Trục xuất", "Đã về nước", ""]
    },
    "Xac_Minh": {
        "name": "Đã từng được xác minh",
        "headers": ["CCCD (*)", "Ngày đề nghị xác minh (*)", "Cơ quan đề nghị (*)",
                    "Nội dung xác minh", "Cơ quan thực hiện",
                    "Ngày hoàn thành", "Kết quả", "Ghi chú"],
        "sample": ["001234567890", "15/01/2024", "Sở Công thương",
                   "Xác minh lý lịch để bổ nhiệm", "PA01",
                   "30/01/2024", "Đủ điều kiện", ""]
    }
}

# Cấu hình cho các loại dữ liệu nhập liệu khác
TEMPLATE_DEFINITIONS = {
    "doi_tuong": {
        "name": "Thông tin đối tượng",
        "headers": ["CCCD (*)", "Họ và tên (*)", "Ngày sinh (dd/mm/yyyy)",
                    "Giới tính", "Tỉnh/TP", "Xã/Phường",
                    "Phân loại nghề nghiệp", "Chi tiết nơi làm việc", "Ghi chú chung"],
        "sample": ["001234567890", "Nguyễn Văn A", "01/01/1990", "Nam",
                   "Phú Thọ", "Phường Thanh Miếu", "Cơ quan nhà nước",
                   "Công an tỉnh Phú Thọ", "Ghi chú mẫu"]
    },
    "lien_he": {
        "name": "Thông tin liên hệ",
        "headers": ["CCCD (*)", "Loại liên hệ", "Giá trị (*)", "Ghi chú"],
        "sample": ["001234567890", "Số điện thoại", "0912345678", "SĐT chính"]
    },
    "than_nhan": {  # Mới thêm theo yêu cầu
        "name": "Thân nhân",
        "headers": ["CCCD (*)", "Họ tên thân nhân", "Quan hệ", "Năm sinh",
                    "Nghề nghiệp/Nơi làm việc", "Địa chỉ", "Ghi chú"],
        "sample": ["001234567890", "Nguyễn Văn B", "Bố đẻ", "1960",
                   "Hưu trí", "Việt Trì, Phú Thọ", ""]
    },
    "tai_chinh": {
        "name": "Tài chính & Ngân hàng",
        "headers": ["CCCD (*)", "Ngân hàng", "Số tài khoản (*)", "Chủ tài khoản", "Ghi chú"],
        "sample": ["001234567890", "Vietcombank", "1234567890123", "NGUYEN VAN A", "TK chính"]
    },
    "phuong_tien": {
        "name": "Phương tiện đí lại",
        "headers": ["CCCD (*)", "Loại xe", "Biển kiểm soát (*)", "Tên phương tiện", "Ghi chú"],
        "sample": ["001234567890", "Ô tô", "19A-12345", "Toyota Vios 2022", "Xe cá nhân"]
    },
    "qua_trinh_hoat_dong": {  # Mới thêm
        "name": "Quá trình hoạt động",
        "headers": ["CCCD (*)", "Thời gian (từ năm-đến năm)", "Nội dung hoạt động", "Ghi chú"],
        "sample": ["001234567890", "2010-2015", "Học sinh trường THPT Chuyên Hùng Vương", ""]
    }
}

```

## utils/bulk_import/exporters.py
```py
# -*- coding: utf-8 -*-
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def export_error_excel(validation_results):
    """
    Tạo file Excel chứa các dòng lỗi với cột lý do để user fix
    Returns: bytes của file Excel hoặc None nếu không có lỗi
    """
    wb = Workbook()

    # Style cho header
    header_font = Font(bold=True, color="FFFFFF")
    error_fill = PatternFill(start_color="dc3545",
                             end_color="dc3545", fill_type="solid")
    header_fill = PatternFill(start_color="667eea",
                              end_color="667eea", fill_type="solid")

    has_errors = False
    first_sheet = True

    # Sheet tên và dữ liệu
    sheet_configs = [
        ('1. Đối tượng - LỖI', 'doi_tuong'),
        ('2. Liên hệ - LỖI', 'lien_he'),
        ('3. Tài chính - LỖI', 'tai_chinh'),
        ('4. Phương tiện - LỖI', 'phuong_tien'),
        ('5. CSXH - LỖI', 'ho_so_dac_thu'),
        ('6. Quá trình - LỖI', 'qua_trinh_hoat_dong'), # Added this
        ('7. Thân nhân - LỖI', 'than_nhan'), # Added this
    ]

    for sheet_name, key in sheet_configs:
        error_rows = validation_results.get(key, {}).get('error_rows', [])
        if error_rows:
            has_errors = True

            if first_sheet:
                ws = wb.active
                ws.title = sheet_name
                first_sheet = False
            else:
                ws = wb.create_sheet(sheet_name)

            # Tạo DataFrame từ error_rows
            df = pd.DataFrame(error_rows)

            # Đảm bảo cột LY_DO_LOI ở cuối
            if 'LY_DO_LOI' in df.columns:
                cols = [c for c in df.columns if c !=
                        'LY_DO_LOI'] + ['LY_DO_LOI']
                df = df[cols]

            # Viết header
            for col_idx, col_name in enumerate(df.columns, 1):
                cell = ws.cell(row=1, column=col_idx, value=col_name)
                if col_name == 'LY_DO_LOI':
                    cell.fill = error_fill
                else:
                    cell.fill = header_fill
                cell.font = header_font
                ws.column_dimensions[cell.column_letter].width = max(
                    15, len(str(col_name)) + 5)

            # Viết dữ liệu - sử dụng enumerate để có row number chính xác
            for row_num, (_, row) in enumerate(df.iterrows(), start=2):
                for col_idx, value in enumerate(row.values, 1):
                    # Security: Sanitize potential formula injection
                    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
                        value = "'" + value

                    cell = ws.cell(row=row_num, column=col_idx, value=value)
                    # Highlight cột lý do lỗi
                    if df.columns[col_idx - 1] == 'LY_DO_LOI':
                        cell.font = Font(color="dc3545", bold=True)

    if not has_errors:
        return None

    # Lưu vào buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()

```

## utils/bulk_import/importers.py
```py
# -*- coding: utf-8 -*-
import pandas as pd
import json
from datetime import datetime
from database import get_connection

def bulk_import_all(validated_data, update_existing=False):
    """
    Thực hiện import dữ liệu đã validate vào database (Transaction nguyên tử)
    Nếu có lỗi bất kỳ đâu -> rollback toàn bộ
    Returns: (success, message, stats)
    """
    conn = get_connection()
    cursor = conn.cursor()

    stats = {
        'doi_tuong': 0,
        'lien_he': 0,
        'than_nhan': 0,
        'tai_chinh': 0,
        'phuong_tien': 0,
        'ho_so_dac_thu': 0,
        'qua_trinh_hoat_dong': 0
    }

    # Helper function to get value safely
    def get_val(row, col):
        val = row.get(col)
        return str(val).strip() if pd.notna(val) else None

    try:
        # Bắt đầu transaction
        conn.execute("BEGIN TRANSACTION")

        # ===== INSERT ĐỐI TƯỢNG =====
        if validated_data['doi_tuong']['data'] is not None:
            df = validated_data['doi_tuong']['data']
            data_list = []

            for _, row in df.iterrows():
                # Xử lý ngày sinh
                ngay_sinh = None
                raw_ns = row.get('ngay_sinh')
                if pd.notna(raw_ns):
                    try:
                        if isinstance(raw_ns, str):
                            ngay_sinh = datetime.strptime(
                                raw_ns, '%d/%m/%Y').strftime('%Y-%m-%d')
                        elif hasattr(raw_ns, 'strftime'):
                            ngay_sinh = raw_ns.strftime('%Y-%m-%d')
                    except ValueError as e:
                        raise ValueError(
                            f"Lỗi xử lý ngày sinh cho CCCD {row.get('cccd')}: {str(e)}")

                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'ho_ten'),
                    ngay_sinh,
                    get_val(row, 'gioi_tinh'),
                    get_val(row, 'dia_chi_tinh') or 'Phú Thọ',
                    get_val(row, 'dia_chi_xa'),
                    get_val(row, 'phan_loai_nghe_nghiep'),
                    get_val(row, 'chi_tiet_nghe_nghiep'),
                    get_val(row, 'ghi_chu_chung')
                ))

            if data_list:
                if update_existing:
                    # UPSERT Logic
                    sql = """
                        INSERT INTO doi_tuong 
                        (cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_tinh, dia_chi_xa, 
                         phan_loai_nghe_nghiep, chi_tiet_nghe_nghiep, ghi_chu_chung)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(cccd) DO UPDATE SET
                        ho_ten=excluded.ho_ten,
                        ngay_sinh=excluded.ngay_sinh,
                        gioi_tinh=excluded.gioi_tinh,
                        dia_chi_tinh=excluded.dia_chi_tinh,
                        dia_chi_xa=excluded.dia_chi_xa,
                        phan_loai_nghe_nghiep=excluded.phan_loai_nghe_nghiep,
                        chi_tiet_nghe_nghiep=excluded.chi_tiet_nghe_nghiep,
                        ghi_chu_chung=excluded.ghi_chu_chung,
                        updated_at=CURRENT_TIMESTAMP
                    """
                else:
                    # Skip duplicate rows
                    sql = """
                        INSERT OR IGNORE INTO doi_tuong 
                        (cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_tinh, dia_chi_xa, 
                         phan_loai_nghe_nghiep, chi_tiet_nghe_nghiep, ghi_chu_chung)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                cursor.executemany(sql, data_list)
                stats['doi_tuong'] = len(data_list)

        # ===== INSERT LIÊN HỆ =====
        if validated_data['lien_he']['data'] is not None:
            df = validated_data['lien_he']['data']
            data_list = []
            for _, row in df.iterrows():
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'loai_lien_he'),
                    str(row['gia_tri']).strip(),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO lien_he (cccd, loai_lien_he, gia_tri, ghi_chu)
                    VALUES (?, ?, ?, ?)
                """, data_list)
                stats['lien_he'] = len(data_list)

        # ===== INSERT THÂN NHÂN =====
        if 'than_nhan' in validated_data and validated_data['than_nhan']['data'] is not None:
            df = validated_data['than_nhan']['data']
            data_list = []
            for _, row in df.iterrows():
                data_list.append((
                    str(row['cccd']).strip(),
                    str(row['ho_ten']).strip(),
                    get_val(row, 'quan_he'),
                    get_val(row, 'nam_sinh'),
                    get_val(row, 'nghe_nghiep'),
                    get_val(row, 'dia_chi'),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO nhan_than (cccd, ho_ten, loai_quan_he, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, data_list)
                stats['than_nhan'] = len(data_list)
            # Note: The original code used `loai_quan_he` as `quan_he`, `ngay_sinh` as `nam_sinh`, `noi_o` as `dia_chi`
            # But the table schema has `loai_quan_he`, `ngay_sinh`, `noi_o`.
            # I matched the VALUES to the columns.
            # Original insert:
            # INSERT INTO than_nhan (cccd, ho_ten, quan_he, nam_sinh, nghe_nghiep, dia_chi, ghi_chu)
            # Schema from database.py:
            # INSERT INTO nhan_than (..., loai_quan_he, ..., ngay_sinh, ..., noi_o, ...)
            # I must ensure the SQL matches the table schema in database.py
            # Table is `nhan_than`. Columns: cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu
            # The excel has `quan_he` -> `loai_quan_he`, `nam_sinh` -> `ngay_sinh`, `dia_chi` -> `noi_o`.
            # I adjusted the query above to match table schema names.

        # ===== INSERT TÀI CHÍNH =====
        if validated_data['tai_chinh']['data'] is not None:
            df = validated_data['tai_chinh']['data']
            data_list = []
            for _, row in df.iterrows():
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'ngan_hang'),
                    str(row['so_tai_khoan']).strip(),
                    get_val(row, 'chu_tai_khoan'),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO tai_chinh (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu)
                    VALUES (?, ?, ?, ?, ?)
                """, data_list)
                stats['tai_chinh'] = len(data_list)

        # ===== INSERT PHƯƠNG TIỆN =====
        if validated_data['phuong_tien']['data'] is not None:
            df = validated_data['phuong_tien']['data']
            data_list = []
            for _, row in df.iterrows():
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'loai_xe'),
                    str(row['bien_kiem_soat']).strip(),
                    get_val(row, 'ten_phuong_tien'),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO phuong_tien (cccd, loai_xe, bien_kiem_soat, ten_phuong_tien, ghi_chu)
                    VALUES (?, ?, ?, ?, ?)
                """, data_list)
                stats['phuong_tien'] = len(data_list)

        # ===== INSERT HỒ SƠ CSXH =====
        if validated_data['ho_so_dac_thu']['data'] is not None:
            df = validated_data['ho_so_dac_thu']['data']
            data_list = []
            for _, row in df.iterrows():
                noi_dung_dict = {
                    'quoc_tich': get_val(row, 'quoc_tich') or '',
                    'ten_to_chuc': get_val(row, 'ten_to_chuc') or '',
                    'thoi_gian_tu': get_val(row, 'thoi_gian_tu') or '',
                    'thoi_gian_den': get_val(row, 'thoi_gian_den') or '',
                    'noi_dung': get_val(row, 'noi_dung_chi_tiet') or '',
                    'co_quan_xm': get_val(row, 'co_quan_xm') or '',
                    'ket_qua': get_val(row, 'ket_qua') or '',
                }

                data_list.append((
                    str(row['cccd']).strip(),
                    str(row['loai_hinh']).strip(),
                    json.dumps(noi_dung_dict, ensure_ascii=False),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO ho_so_dac_thu (cccd, loai_hinh, noi_dung_chi_tiet, ghi_chu)
                    VALUES (?, ?, ?, ?)
                """, data_list)
                stats['ho_so_dac_thu'] = len(data_list)

        # ===== INSERT QUÁ TRÌNH HOẠT ĐỘNG =====
        if 'qua_trinh_hoat_dong' in validated_data and validated_data['qua_trinh_hoat_dong']['data'] is not None:
            df = validated_data['qua_trinh_hoat_dong']['data']
            data_list = []
            for _, row in df.iterrows():
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'thoi_gian'),
                    str(row['noi_dung']).strip(),
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO qua_trinh_hoat_dong (cccd, thoi_gian, noi_dung, ghi_chu)
                    VALUES (?, ?, ?, ?)
                """, data_list)
                stats['qua_trinh_hoat_dong'] = len(data_list)

        # Commit transaction
        conn.commit()
        conn.close()

        total = sum(stats.values())
        return True, f"Import thành công {total} bản ghi!", stats

    except Exception as e:
        # Rollback nếu có lỗi
        conn.rollback()
        conn.close()
        return False, f"Lỗi import tại bước SQL: {str(e)}", stats

```

## utils/bulk_import/templates.py
```py
# -*- coding: utf-8 -*-
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from .constants import CSXH_TEMPLATES, TEMPLATE_DEFINITIONS

def style_header_row(ws, headers):
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="667eea",
                              end_color="667eea", fill_type="solid")
    thin_border = Border(left=Side('thin'), right=Side(
        'thin'), top=Side('thin'), bottom=Side('thin'))

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
        ws.column_dimensions[cell.column_letter].width = max(
            15, len(header) + 5)


def create_excel_template(import_type="all", csxh_type=None):
    """
    Tạo file Excel mẫu
    Args:
        import_type: 'all' (5 sheet) hoặc key trong TEMPLATE_DEFINITIONS ('doi_tuong', 'lien_he'...)
        csxh_type: Loại CSXH cụ thể (nếu import_type='ho_so_dac_thu')
    """
    wb = Workbook()

    if import_type == "all":
        create_full_template(wb, csxh_type)
    elif import_type == "ho_so_dac_thu":
        # Tạo sheet CSXH lẻ
        if csxh_type and csxh_type in CSXH_TEMPLATES:
            tpl = CSXH_TEMPLATES[csxh_type]
            ws = wb.active
            ws.title = "Hồ sơ CSXH"
            style_header_row(ws, tpl['headers'])
            ws.append(tpl['sample'])
            ws.cell(row=4, column=1, value=f"Loại hình: {csxh_type}")
        else:
            # CSXH Tổng hợp
            create_csxh_general_sheet(wb)
    elif import_type in TEMPLATE_DEFINITIONS:
        # Tạo sheet đơn cho các loại khác
        tpl = TEMPLATE_DEFINITIONS[import_type]
        ws = wb.active
        ws.title = tpl['name']
        style_header_row(ws, tpl['headers'])
        ws.append(tpl['sample'])
        ws.cell(row=5, column=1,
                value="(*) cột bắt buộc. CCCD dùng để định danh đối tượng.")

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def create_full_template(wb, csxh_type):
    # ========== SHEET 1: ĐỐI TƯỢNG ==========
    ws1 = wb.active
    ws1.title = "1. Đối tượng"
    # Dòng mẫu
    ws1.append(["001234567890", "Nguyễn Văn A", "01/01/1990", "Nam",
                "Phú Thọ", "Phường Thanh Miếu", "Cơ quan nhà nước",
                "Công an tỉnh Phú Thọ", "Ghi chú mẫu"])
    ws1.append(["001234567891", "Trần Thị B", "15/05/1985", "Nữ",
                "Phú Thọ", "Phường Gia Cẩm", "Tự do",
                "Buôn bán tự do", ""])

    # Ghi chú
    ws1.cell(row=5, column=1,
             value="Lưu ý: (*) là trường bắt buộc. CCCD phải đủ 12 số.")
    
    # Apply style manually for sheet 1 since it's hardcoded here
    headers_1 = ["CCCD (*)", "Họ và tên (*)", "Ngày sinh (dd/mm/yyyy)",
                 "Giới tính", "Tỉnh/TP", "Xã/Phường",
                 "Phân loại nghề nghiệp", "Chi tiết nơi làm việc", "Ghi chú chung"]
    style_header_row(ws1, headers_1)


    # ========== SHEET 2: LIÊN HỆ ==========
    ws2 = wb.create_sheet("2. Liên hệ")
    headers_2 = [
        "CCCD (*)", "Loại liên hệ", "Giá trị (*)", "Ghi chú"
    ]
    style_header_row(ws2, headers_2)
    ws2.append(["001234567890", "Số điện thoại", "0912345678", "SĐT chính"])
    ws2.append(["001234567890", "Facebook", "facebook.com/nguyenvana", ""])
    ws2.append(["001234567891", "Số điện thoại", "0987654321", ""])
    ws2.cell(row=6, column=1,
             value="Loại liên hệ: Số điện thoại, Email, Facebook, Zalo, Telegram, Khác")

    # ========== SHEET 3: TÀI CHÍNH ==========
    ws3 = wb.create_sheet("3. Tài chính")
    headers_3 = [
        "CCCD (*)", "Ngân hàng", "Số tài khoản (*)", "Chủ tài khoản", "Ghi chú"
    ]
    style_header_row(ws3, headers_3)
    ws3.append(["001234567890", "Vietcombank",
               "1234567890123", "NGUYEN VAN A", "TK chính"])
    ws3.append(["001234567890", "Techcombank",
               "9876543210", "NGUYEN VAN A", "TK phụ"])

    # ========== SHEET 4: PHƯƠNG TIỆN ==========
    ws4 = wb.create_sheet("4. Phương tiện")
    headers_4 = [
        "CCCD (*)", "Loại xe", "Biển kiểm soát (*)", "Tên phương tiện", "Ghi chú"
    ]
    style_header_row(ws4, headers_4)
    ws4.append(["001234567890", "Ô tô", "19A-12345",
               "Toyota Vios 2022", "Xe cá nhân"])
    ws4.append(["001234567891", "Xe máy", "19B1-67890", "Honda Wave", ""])
    ws4.cell(row=5, column=1, value="Loại xe: Ô tô, Xe máy, Xe tải, Xe khách, Khác")

    # ========== SHEET 5: HỒ SƠ CSXH ==========
    if csxh_type and csxh_type in CSXH_TEMPLATES:
        # Tạo sheet theo loại cụ thể
        template = CSXH_TEMPLATES[csxh_type]
        ws5 = wb.create_sheet(f"5. {template['name']}")
        style_header_row(ws5, template['headers'])
        ws5.append(template['sample'])
        ws5.cell(row=4, column=1, value=f"Loại hình: {csxh_type}")
    else:
        create_csxh_general_sheet(wb)

def create_csxh_general_sheet(wb):
    ws5 = wb.create_sheet("5. Hồ sơ CSXH (Tổng hợp)")
    headers_5 = [
        "CCCD (*)", "Loại hình (*)",
        "Quốc tịch/Quốc gia", "Tên tổ chức/Người nước ngoài",
        "Thời gian (từ năm)", "Thời gian (đến năm)",
        "Nội dung chi tiết", "Cơ quan xác minh", "Kết quả", "Ghi chú"
    ]
    style_header_row(ws5, headers_5)

    # Mẫu cho từng loại
    ws5.append(["001234567890", "Hon_Nhan_NN", "Trung Quốc", "WANG Xiaoming",
                "2020", "", "Kết hôn với công dân TQ", "", "", ""])

    ws5.cell(row=4, column=1, value="--- HƯỚNG DẪN LOẠI HÌNH ---")
    ws5.cell(row=5, column=1,
             value="Hon_Nhan_NN | Lam_Viec_NN | Hoc_Tap_Cong_Tac_NN | Vi_Pham_NN | Xac_Minh")

```

## utils/bulk_import/validators.py
```py
# -*- coding: utf-8 -*-
import pandas as pd
import re
import logging
from datetime import datetime
from database import get_connection
from constants import (
    DANH_SACH_XA_PHU_THO, GIOI_TINH_OPTIONS, TINH_OPTIONS,
    PHAN_LOAI_NGHE_NGHIEP_OPTIONS, LOAI_LIEN_HE_OPTIONS, LOAI_XE_OPTIONS,
    DANH_SACH_NGAN_HANG
)

# Import Deduplication module
try:
    from utils.deduplication import find_duplicates_in_batch, generate_duplicate_report
    DEDUP_AVAILABLE = True
except ImportError:
    DEDUP_AVAILABLE = False

logger = logging.getLogger(__name__)

def normalize_cccd(value) -> str:
    """
    Chuẩn hóa CCCD: xử lý trường hợp Excel đọc như số (mất leading zeros).
    """
    if pd.isna(value):
        return ""
    s = str(value).strip()
    # Loại bỏ .0 nếu Excel đọc như số float
    if s.endswith('.0'):
        s = s[:-2]
    # Pad leading zeros nếu là số hợp lệ và thiếu chữ số
    if s.isdigit() and len(s) < 12:
        s = s.zfill(12)
    return s


def validate_excel_data(excel_file, import_type='all'):
    """
    Đọc và validate dữ liệu từ file Excel
    Args:
        excel_file: File object
        import_type: Loại import ('all', 'doi_tuong', 'lien_he'...)
    """
    results = {
        'doi_tuong': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'lien_he': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'than_nhan': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'tai_chinh': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'phuong_tien': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'ho_so_dac_thu': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
        'qua_trinh_hoat_dong': {'data': None, 'errors': [], 'valid_count': 0, 'error_rows': []},
    }

    try:
        # Đọc tất cả sheets
        xls = pd.ExcelFile(excel_file)
        sheet_names = xls.sheet_names

        # Lấy danh sách CCCD đã tồn tại trong DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cccd FROM doi_tuong")
        existing_cccds = set(row[0] for row in cursor.fetchall())
        conn.close()

        # Hàm helper để check xem nên đọc sheet nào
        def should_read(sheet_key, index):
            if import_type == 'all':
                return len(sheet_names) > index
            return import_type == sheet_key and len(sheet_names) > 0

        # ===== SHEET: ĐỐI TƯỢNG =====
        if should_read('doi_tuong', 0):
            target_sheet = 0 if import_type != 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]  # Bỏ dòng mẫu
            df = df.dropna(how='all')  # Bỏ dòng trống

            if len(df) > 0:
                # Chuẩn hóa tên cột
                df.columns = ['cccd', 'ho_ten', 'ngay_sinh', 'gioi_tinh',
                              'dia_chi_tinh', 'dia_chi_xa', 'phan_loai_nghe_nghiep',
                              'chi_tiet_nghe_nghiep', 'ghi_chu_chung']

                errors = []
                valid_rows = []
                new_cccds = set()

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])

                    # Validate CCCD (phải đủ 12 số)
                    if not cccd:
                        row_errors.append(f"Dòng {idx+1}: Thiếu CCCD")
                    elif not cccd.isdigit():
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD chỉ được chứa số")
                    elif len(cccd) != 12:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD phải đủ 12 số (hiện có {len(cccd)} số)")
                    elif cccd in existing_cccds:
                        # Cho phép tiếp tục để bổ sung dữ liệu (sẽ dùng INSERT OR IGNORE)
                        pass
                    elif cccd in new_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} bị trùng trong file")

                    # Validate Họ tên (bắt buộc)
                    ho_ten = str(row['ho_ten']).strip(
                    ) if pd.notna(row['ho_ten']) else ""
                    if not ho_ten:
                        row_errors.append(f"Dòng {idx+1}: Thiếu Họ và tên")

                    # Validate Ngày sinh (định dạng dd/mm/yyyy hoặc datetime)
                    ngay_sinh = row['ngay_sinh']
                    if pd.notna(ngay_sinh):
                        try:
                            if isinstance(ngay_sinh, str):
                                # Kiểm tra định dạng dd/mm/yyyy
                                if not re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', ngay_sinh.strip()):
                                    row_errors.append(
                                        f"Dòng {idx+1}: Ngày sinh sai định dạng (cần dd/mm/yyyy)")
                                else:
                                    datetime.strptime(
                                        ngay_sinh.strip(), '%d/%m/%Y')
                        except ValueError:
                            row_errors.append(
                                f"Dòng {idx+1}: Ngày sinh không hợp lệ")

                    # Validate Giới tính
                    gioi_tinh = str(row['gioi_tinh']).strip(
                    ) if pd.notna(row['gioi_tinh']) else ""
                    if gioi_tinh and gioi_tinh not in GIOI_TINH_OPTIONS:
                        row_errors.append(
                            f"Dòng {idx+1}: Giới tính '{gioi_tinh}' không hợp lệ (chỉ: {', '.join(GIOI_TINH_OPTIONS)})")

                    # Validate Tỉnh/TP
                    dia_chi_tinh = str(row['dia_chi_tinh']).strip(
                    ) if pd.notna(row['dia_chi_tinh']) else ""
                    if dia_chi_tinh and dia_chi_tinh not in TINH_OPTIONS:
                        row_errors.append(
                            f"Dòng {idx+1}: Tỉnh/TP '{dia_chi_tinh}' không hợp lệ (chỉ: {', '.join(TINH_OPTIONS)})")

                    # Validate Xã/Phường (phải nằm trong danh sách 105 nếu tỉnh là Phú Thọ)
                    dia_chi_xa = str(row['dia_chi_xa']).strip(
                    ) if pd.notna(row['dia_chi_xa']) else ""
                    if dia_chi_tinh == "Phú Thọ" and dia_chi_xa:
                        if dia_chi_xa not in DANH_SACH_XA_PHU_THO:
                            row_errors.append(
                                f"Dòng {idx+1}: Xã/Phường '{dia_chi_xa}' không nằm trong danh sách 105 xã/phường Phú Thọ")

                    # Validate Phân loại nghề nghiệp
                    phan_loai = str(row['phan_loai_nghe_nghiep']).strip(
                    ) if pd.notna(row['phan_loai_nghe_nghiep']) else ""
                    if phan_loai and phan_loai not in PHAN_LOAI_NGHE_NGHIEP_OPTIONS:
                        row_errors.append(
                            f"Dòng {idx+1}: Phân loại nghề nghiệp '{phan_loai}' không hợp lệ")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(
                            [e.split(': ', 1)[1] if ': ' in e else e for e in row_errors])
                        results['doi_tuong']['error_rows'].append(error_row)
                    else:
                        new_cccds.add(cccd)
                        valid_rows.append(row)

                results['doi_tuong']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['doi_tuong']['errors'] = errors
                results['doi_tuong']['valid_count'] = len(valid_rows)
                results['doi_tuong']['new_cccds'] = new_cccds

                # ===== DEDUPLICATION CHECK =====
                if DEDUP_AVAILABLE and valid_rows:
                    try:
                        records = [row.to_dict() for row in valid_rows]
                        duplicates = find_duplicates_in_batch(records)

                        if duplicates:
                            results['doi_tuong']['duplicates'] = duplicates
                            results['doi_tuong']['duplicate_count'] = len(
                                duplicates)
                            results['doi_tuong']['duplicate_report'] = generate_duplicate_report(
                                [{'kept_record': records[d[0]], 'removed_records': [
                                    records[d[1]]], 'cluster_size': 2} for d in duplicates]
                            )
                    except Exception as e:
                        logger.warning(f"Dedup detection failed: {e}")

        # ===== SHEET: LIÊN HỆ =====
        if should_read('lien_he', 1):
            valid_cccds = existing_cccds.union(
                results['doi_tuong'].get('new_cccds', set()))
            target_sheet = 0 if import_type != 'all' else 1
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            if len(df) > 0:
                df.columns = ['cccd', 'loai_lien_he', 'gia_tri', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    loai_lien_he = str(row['loai_lien_he']).strip(
                    ) if pd.notna(row['loai_lien_he']) else ""
                    gia_tri = str(row['gia_tri']).strip(
                    ) if pd.notna(row['gia_tri']) else ""

                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not gia_tri:
                        row_errors.append(
                            f"Dòng {idx+1}: Thiếu giá trị liên hệ")
                    if loai_lien_he and loai_lien_he not in LOAI_LIEN_HE_OPTIONS + ["Khác", "Số điện thoại", "Facebook", "Zalo", "Telegram", "Email"]:
                        row_errors.append(
                            f"Dòng {idx+1}: Loại liên hệ '{loai_lien_he}' không hợp lệ")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(
                            [e.split(': ', 1)[1] if ': ' in e else e for e in row_errors])
                        results['lien_he']['error_rows'].append(error_row)
                    else:
                        valid_rows.append(row)

                results['lien_he']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['lien_he']['errors'] = errors
                results['lien_he']['valid_count'] = len(valid_rows)

        # ===== SHEET: THÂN NHÂN (New) =====
        if should_read('than_nhan', 99):  
            target_sheet = 0
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            if len(df) > 0:
                df.columns = ['cccd', 'ho_ten', 'quan_he',
                              'nam_sinh', 'nghe_nghiep', 'dia_chi', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    ho_ten = str(row['ho_ten']).strip(
                    ) if pd.notna(row['ho_ten']) else ""
                    
                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not ho_ten:
                        row_errors.append(
                            f"Dòng {idx+1}: Thiếu họ tên thân nhân")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(row_errors)
                        results['than_nhan']['error_rows'].append(error_row)
                    else:
                        valid_rows.append(row)

                results['than_nhan']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['than_nhan']['errors'] = errors
                results['than_nhan']['valid_count'] = len(valid_rows)

        # ===== SHEET: TÀI CHÍNH =====
        if should_read('tai_chinh', 2):
            target_sheet = 0 if import_type != 'all' else 2
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            if len(df) > 0:
                df.columns = ['cccd', 'ngan_hang',
                              'so_tai_khoan', 'chu_tai_khoan', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    ngan_hang = str(row['ngan_hang']).strip(
                    ) if pd.notna(row['ngan_hang']) else ""
                    so_tai_khoan = str(row['so_tai_khoan']).strip(
                    ) if pd.notna(row['so_tai_khoan']) else ""

                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not so_tai_khoan:
                        row_errors.append(f"Dòng {idx+1}: Thiếu số tài khoản")
                    if ngan_hang and ngan_hang not in DANH_SACH_NGAN_HANG:
                        row_errors.append(
                            f"Dòng {idx+1}: Ngân hàng '{ngan_hang}' không nằm trong danh sách chuẩn")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(
                            [e.split(': ', 1)[1] if ': ' in e else e for e in row_errors])
                        results['tai_chinh']['error_rows'].append(error_row)
                    else:
                        valid_rows.append(row)

                results['tai_chinh']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['tai_chinh']['errors'] = errors
                results['tai_chinh']['valid_count'] = len(valid_rows)

        # ===== SHEET: PHƯƠNG TIỆN =====
        if should_read('phuong_tien', 3):
            target_sheet = 0 if import_type != 'all' else 3
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            if len(df) > 0:
                df.columns = ['cccd', 'loai_xe',
                              'bien_kiem_soat', 'ten_phuong_tien', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    loai_xe = str(row['loai_xe']).strip(
                    ) if pd.notna(row['loai_xe']) else ""
                    bien_kiem_soat = str(row['bien_kiem_soat']).strip(
                    ) if pd.notna(row['bien_kiem_soat']) else ""

                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not bien_kiem_soat:
                        row_errors.append(
                            f"Dòng {idx+1}: Thiếu biển kiểm soát")
                    if loai_xe and loai_xe not in LOAI_XE_OPTIONS + ["Xe tải", "Xe khách", "Khác"]:
                        row_errors.append(
                            f"Dòng {idx+1}: Loại xe '{loai_xe}' không hợp lệ")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(
                            [e.split(': ', 1)[1] if ': ' in e else e for e in row_errors])
                        results['phuong_tien']['error_rows'].append(error_row)
                    else:
                        valid_rows.append(row)

                results['phuong_tien']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['phuong_tien']['errors'] = errors
                results['phuong_tien']['valid_count'] = len(valid_rows)

        if should_read('ho_so_dac_thu', 4):
            target_sheet = 0 if import_type != 'all' else 4
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            valid_loai_hinh = ['Hon_Nhan_NN', 'Lam_Viec_NN',
                               'Hoc_Tap_Cong_Tac_NN', 'Vi_Pham_NN', 'Xac_Minh']
            if len(df) > 0:
                # Filter headers
                df = df[~df.iloc[:, 0].astype(str).str.startswith('---')]
                df = df[~df.iloc[:, 0].astype(str).str.startswith('-')]

            if len(df) > 0:
                df.columns = ['cccd', 'loai_hinh', 'quoc_tich', 'ten_to_chuc',
                              'thoi_gian_tu', 'thoi_gian_den', 'noi_dung_chi_tiet',
                              'co_quan_xm', 'ket_qua', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    loai_hinh = str(row['loai_hinh']).strip(
                    ) if pd.notna(row['loai_hinh']) else ""
                    
                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not loai_hinh:
                        row_errors.append(f"Dòng {idx+1}: Thiếu loại hình")
                    elif loai_hinh not in valid_loai_hinh:
                        row_errors.append(
                            f"Dòng {idx+1}: Loại hình '{loai_hinh}' không hợp lệ")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(row_errors)
                        results['ho_so_dac_thu']['error_rows'].append(
                            error_row)
                    else:
                        valid_rows.append(row)

                results['ho_so_dac_thu']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['ho_so_dac_thu']['errors'] = errors
                results['ho_so_dac_thu']['valid_count'] = len(valid_rows)

        # ===== SHEET: QUÁ TRÌNH HOẠT ĐỘNG (New) =====
        if should_read('qua_trinh_hoat_dong', 99):
            target_sheet = 0
            df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=0)
            df = df.iloc[1:]
            df = df.dropna(how='all')

            if len(df) > 0:
                df.columns = ['cccd', 'thoi_gian', 'noi_dung', 'ghi_chu']
                errors = []
                valid_rows = []

                for idx, row in df.iterrows():
                    row_errors = []
                    cccd = normalize_cccd(row['cccd'])
                    noi_dung = str(row['noi_dung']).strip(
                    ) if pd.notna(row['noi_dung']) else ""

                    if cccd not in valid_cccds:
                        row_errors.append(
                            f"Dòng {idx+1}: CCCD {cccd} không tồn tại")
                    if not noi_dung:
                        row_errors.append(
                            f"Dòng {idx+1}: Thiếu nội dung hoạt động")

                    if row_errors:
                        errors.extend(row_errors)
                        error_row = row.to_dict()
                        error_row['LY_DO_LOI'] = '; '.join(row_errors)
                        results['qua_trinh_hoat_dong']['error_rows'].append(
                            error_row)
                    else:
                        valid_rows.append(row)

                results['qua_trinh_hoat_dong']['data'] = pd.DataFrame(
                    valid_rows) if valid_rows else None
                results['qua_trinh_hoat_dong']['errors'] = errors
                results['qua_trinh_hoat_dong']['valid_count'] = len(valid_rows)

    except Exception as e:
        results['doi_tuong']['errors'].append(f"Lỗi đọc file: {str(e)}")

    return results

```

## utils/bulk_import/__init__.py
```py
# -*- coding: utf-8 -*-
from .constants import CSXH_TEMPLATES, TEMPLATE_DEFINITIONS
from .templates import create_excel_template
from .validators import validate_excel_data
from .importers import bulk_import_all
from .exporters import export_error_excel

__all__ = [
    'CSXH_TEMPLATES',
    'TEMPLATE_DEFINITIONS',
    'create_excel_template',
    'validate_excel_data',
    'bulk_import_all',
    'export_error_excel'
]

```

## views/audit_log.py
```py
# -*- coding: utf-8 -*-
"""
Audit Log Viewer - Security Profile 360
Xem lịch sử thay đổi dữ liệu
"""
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_connection
from app.services.auth_service import is_super_admin
from utils.security_utils import sanitize_dataframe_for_csv

logger = logging.getLogger(__name__)


def get_audit_logs(limit=100, table_filter=None, action_filter=None, date_from=None, date_to=None):
    """Lấy audit logs với các bộ lọc."""
    conn = get_connection()
    try:
        query = """
            SELECT id, bang, hanh_dong, khoa_chinh, 
                   du_lieu_cu, du_lieu_moi, 
                   nguoi_thuc_hien, ip_address, created_at
            FROM audit_log
            WHERE 1=1
        """
        params = []

        if table_filter and table_filter != "Tất cả":
            query += " AND bang = ?"
            params.append(table_filter)

        if action_filter and action_filter != "Tất cả":
            query += " AND hanh_dong = ?"
            params.append(action_filter)

        if date_from:
            query += " AND DATE(created_at) >= ?"
            params.append(date_from.strftime('%Y-%m-%d'))

        if date_to:
            query += " AND DATE(created_at) <= ?"
            params.append(date_to.strftime('%Y-%m-%d'))

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Lỗi truy vấn: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_table_list():
    """Lấy danh sách các bảng có trong audit log."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bang FROM audit_log")
        tables = [row[0] for row in cursor.fetchall()]
        return ["Tất cả"] + tables
    except Exception as e:
        logger.warning(f"Lỗi lấy danh sách bảng audit: {e}")
        return ["Tất cả"]
    finally:
        conn.close()


def get_action_list():
    """Lấy danh sách các loại hành động."""
    return ["Tất cả", "INSERT", "UPDATE", "DELETE", "VIEW"]


def add_audit_log(bang, hanh_dong, khoa_chinh, du_lieu_cu=None, du_lieu_moi=None, nguoi_thuc_hien=None):
    """Thêm một entry vào audit log."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (bang, hanh_dong, khoa_chinh, du_lieu_cu, du_lieu_moi, nguoi_thuc_hien)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bang, hanh_dong, khoa_chinh, du_lieu_cu, du_lieu_moi, nguoi_thuc_hien))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi audit log: {e}")
        return False
    finally:
        conn.close()


def page_audit_log():
    """Trang xem lịch sử thay đổi."""

    user = st.session_state.get('user', {})

    # Chỉ Super Admin
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 📜 Lịch sử thay đổi")
    st.markdown("### Audit Log - Theo dõi mọi thay đổi trong hệ thống")

    st.markdown("---")

    # Filters
    st.markdown("#### 🔍 Bộ lọc")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        table_filter = st.selectbox(
            "Bảng",
            options=get_table_list()
        )

    with col2:
        action_filter = st.selectbox(
            "Hành động",
            options=get_action_list()
        )

    with col3:
        date_from = st.date_input(
            "Từ ngày",
            value=datetime.now() - timedelta(days=30)
        )

    with col4:
        date_to = st.date_input(
            "Đến ngày",
            value=datetime.now()
        )

    limit = st.slider("Số bản ghi tối đa", 50, 500, 100, 50)

    st.markdown("---")

    # Load data
    df = get_audit_logs(
        limit=limit,
        table_filter=table_filter,
        action_filter=action_filter,
        date_from=date_from,
        date_to=date_to
    )

    if df.empty:
        st.info("💡 Chưa có log nào trong khoảng thời gian này.")
        st.caption("Audit log sẽ được ghi khi có thao tác thay đổi dữ liệu.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Tổng bản ghi", len(df))

    if 'hanh_dong' in df.columns:
        insert_count = len(df[df['hanh_dong'] == 'INSERT'])
        update_count = len(df[df['hanh_dong'] == 'UPDATE'])
        delete_count = len(df[df['hanh_dong'] == 'DELETE'])

        col2.metric("➕ INSERT", insert_count)
        col3.metric("✏️ UPDATE", update_count)
        col4.metric("🗑️ DELETE", delete_count)

    st.markdown("---")

    # Format display
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(
            df['created_at']).dt.strftime('%d/%m/%Y %H:%M:%S')

    # Rename columns
    df_display = df.rename(columns={
        'id': 'ID',
        'bang': 'Bảng',
        'hanh_dong': 'Hành động',
        'khoa_chinh': 'Khóa chính',
        'du_lieu_cu': 'Dữ liệu cũ',
        'du_lieu_moi': 'Dữ liệu mới',
        'nguoi_thuc_hien': 'Người thực hiện',
        'ip_address': 'IP',
        'created_at': 'Thời gian'
    })

    # Color-code by action
    st.markdown("#### 📋 Chi tiết Audit Log")

    # Tabs by action type
    tab_all, tab_insert, tab_update, tab_delete = st.tabs([
        f"📋 Tất cả ({len(df)})",
        f"➕ INSERT ({len(df[df['hanh_dong'] == 'INSERT']) if 'hanh_dong' in df.columns else 0})",
        f"✏️ UPDATE ({len(df[df['hanh_dong'] == 'UPDATE']) if 'hanh_dong' in df.columns else 0})",
        f"🗑️ DELETE ({len(df[df['hanh_dong'] == 'DELETE']) if 'hanh_dong' in df.columns else 0})"
    ])

    with tab_all:
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab_insert:
        df_insert = df_display[df_display['Hành động'] ==
                               'INSERT'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_insert.empty:
            st.dataframe(df_insert, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi INSERT trong khoảng thời gian này.")

    with tab_update:
        df_update = df_display[df_display['Hành động'] ==
                               'UPDATE'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_update.empty:
            st.dataframe(df_update, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi UPDATE trong khoảng thời gian này.")

    with tab_delete:
        df_delete = df_display[df_display['Hành động'] ==
                               'DELETE'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_delete.empty:
            st.dataframe(df_delete, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi DELETE trong khoảng thời gian này.")

    # Export
    st.markdown("---")
    st.download_button(
        label="📥 Xuất Audit Log (CSV)",
        data=sanitize_dataframe_for_csv(df).to_csv(index=False).encode('utf-8-sig'),
        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

```

## views/dashboard.py
```py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from database import get_connection
from constants import (
    LOAI_HINH_DAC_THU,
)

# ECharts (primary) - với fallback Plotly
try:
    from streamlit_echarts import st_echarts
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================
# HELPER FUNCTIONS
# ============================================


@st.cache_data(ttl=300)
def get_statistics():
    """Lấy thống kê tổng quan (cached)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Tổng số đối tượng
        cursor.execute("SELECT COUNT(*) FROM doi_tuong")
        total_doi_tuong = cursor.fetchone()[0]

        # Số theo giới tính
        cursor.execute(
            "SELECT gioi_tinh, COUNT(*) FROM doi_tuong GROUP BY gioi_tinh")
        gioi_tinh_stats = dict(cursor.fetchall())

        # Số theo phân loại nghề nghiệp
        cursor.execute(
            "SELECT phan_loai_nghe_nghiep, COUNT(*) FROM doi_tuong GROUP BY phan_loai_nghe_nghiep")
        nghe_nghiep_stats = dict(cursor.fetchall())

        # Số hồ sơ đặc thù theo loại hình
        cursor.execute(
            "SELECT loai_hinh, COUNT(*) FROM ho_so_dac_thu GROUP BY loai_hinh")
        dac_thu_stats = dict(cursor.fetchall())

        return {
            "total": total_doi_tuong,
            "gioi_tinh": gioi_tinh_stats,
            "nghe_nghiep": nghe_nghiep_stats,
            "dac_thu": dac_thu_stats,
        }
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_recent_records(limit=10):
    """Lấy các bản ghi gần đây"""
    conn = get_connection()
    try:
        query = """
            SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, phan_loai_nghe_nghiep
            FROM doi_tuong
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_xa_phuong_stats():
    """Lấy thống kê theo xã/phường"""
    conn = get_connection()
    try:
        query = """
            SELECT dia_chi_xa, COUNT(*) as so_luong 
            FROM doi_tuong 
            WHERE dia_chi_xa IS NOT NULL AND dia_chi_xa != ''
            GROUP BY dia_chi_xa 
            ORDER BY so_luong DESC 
            LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

# ... (Previous code remains same, skipping to page_dashboard updates)

# ============================================
# CHART RENDERING FUNCTIONS
# ============================================

def render_pie_echarts(data_dict, title):
    """Render Pie Chart using ECharts"""
    data_entries = [
        {"value": v, "name": k} 
        for k, v in data_dict.items()
    ]
    
    option = {
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": "#fff"}
        },
        "tooltip": {
            "trigger": "item"
        },
        "legend": {
            "orient": "vertical",
            "left": "left",
            "textStyle": {"color": "#fff"}
        },
        "series": [
            {
                "name": title,
                "type": "pie",
                "radius": "50%",
                "data": data_entries,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    st_echarts(options=option, height="300px")


def render_bar_echarts(data_dict, title, horizontal=True):
    """Render Bar Chart using ECharts"""
    keys = list(data_dict.keys())
    values = list(data_dict.values())
    
    if horizontal:
        option = {
            "title": {"text": title, "textStyle": {"color": "#fff"}},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "value", "axisLabel": {"color": "#fff"}},
            "yAxis": {"type": "category", "data": keys, "axisLabel": {"color": "#fff"}},
            "series": [{"type": "bar", "data": values}]
        }
    else:
        option = {
            "title": {"text": title, "textStyle": {"color": "#fff"}},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": keys, "axisLabel": {"color": "#fff"}},
            "yAxis": {"type": "value", "axisLabel": {"color": "#fff"}},
            "series": [{"type": "bar", "data": values}]
        }
        
    st_echarts(options=option, height="300px")


def render_pie_plotly(data_dict, title):
    """Render Pie Chart using Plotly"""
    df = pd.DataFrame(list(data_dict.items()), columns=['Category', 'Value'])
    fig = px.pie(df, values='Value', names='Category', title=title)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bar_plotly(data_dict, title, horizontal=True):
    """Render Bar Chart using Plotly"""
    df = pd.DataFrame(list(data_dict.items()), columns=['Category', 'Value'])
    if horizontal:
        fig = px.bar(df, x='Value', y='Category', title=title, orientation='h')
    else:
        fig = px.bar(df, x='Category', y='Value', title=title)
        
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================
# DASHBOARD PAGE
# ============================================
def page_dashboard():
    """Trang Dashboard - Tổng quan hệ thống với ECharts tương tác"""

    st.markdown("# 🏠 Dashboard")
    st.markdown("### Tổng quan hệ thống quản lý hồ sơ an ninh")

    # Check ECharts availability
    if not ECHARTS_AVAILABLE:
        st.warning(
            "⚠️ Để có biểu đồ tương tác, hãy cài: `pip install streamlit-echarts`")
        st.info("Đang sử dụng Plotly fallback...")

    st.markdown("---")

    # Thống kê chính
    with st.spinner("Đang tải thống kê hệ thống..."):
        stats = get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📋 Tổng đối tượng",
            value=stats["total"],
        )

    with col2:
        nam_count = stats["gioi_tinh"].get("Nam", 0)
        st.metric(
            label="👨 Nam giới",
            value=nam_count,
        )

    with col3:
        nu_count = stats["gioi_tinh"].get("Nữ", 0)
        st.metric(
            label="👩 Nữ giới",
            value=nu_count,
        )

    with col4:
        dac_thu_total = sum(stats["dac_thu"].values()
                            ) if stats["dac_thu"] else 0
        st.metric(
            label="🌐 Yếu tố nước ngoài",
            value=dac_thu_total,
        )

    st.markdown("---")

    # Row 1: Pie Chart giới tính + Bar chart nghề nghiệp
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 👥 Phân bố giới tính")
        if stats["gioi_tinh"] and sum(stats["gioi_tinh"].values()) > 0:
            if ECHARTS_AVAILABLE:
                render_pie_echarts(stats["gioi_tinh"], "Giới tính")
            else:
                render_pie_plotly(stats["gioi_tinh"], "Giới tính")
        else:
            st.info("💡 Chưa có dữ liệu giới tính.")

    with col_right:
        st.markdown("### 📊 Phân loại nghề nghiệp")
        if stats["nghe_nghiep"] and sum(stats["nghe_nghiep"].values()) > 0:
            if ECHARTS_AVAILABLE:
                render_bar_echarts(stats["nghe_nghiep"], "Nghề nghiệp")
            else:
                render_bar_plotly(stats["nghe_nghiep"], "Nghề nghiệp")
        else:
            st.info("💡 Chưa có dữ liệu nghề nghiệp.")

    st.markdown("---")

    # Row 2: Hồ sơ đặc thù + Top xã/phường
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("### 🌐 Hồ sơ đặc thù CSXH")
        if stats["dac_thu"] and sum(stats["dac_thu"].values()) > 0:
            # Convert keys to readable names
            readable_dac_thu = {
                LOAI_HINH_DAC_THU.get(k, k): v
                for k, v in stats["dac_thu"].items()
            }
            if ECHARTS_AVAILABLE:
                render_bar_echarts(
                    readable_dac_thu, "Hồ sơ đặc thù", horizontal=False)
            else:
                render_bar_plotly(readable_dac_thu, "Hồ sơ đặc thù")
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào.")

    with col_right2:
        st.markdown("### 🏘️ Top 10 xã/phường")
        # Load data with spinner
        with st.spinner("Đang tải dữ liệu địa bàn..."):
            df_xa = get_xa_phuong_stats()

        if not df_xa.empty:
            if ECHARTS_AVAILABLE:
                # Convert DataFrame to dict for vertical bar chart
                xa_data = dict(
                    zip(df_xa['dia_chi_xa'].tolist(), df_xa['so_luong'].tolist()))
                render_bar_echarts(xa_data, "Top xã/phường", horizontal=False)
            else:
                fig_xa = px.bar(df_xa, y='dia_chi_xa', x='so_luong', orientation='h',
                                color='so_luong', color_continuous_scale='Viridis')
                fig_xa.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False, coloraxis_showscale=False
                )
                st.plotly_chart(fig_xa, use_container_width=True)
        else:
            st.info("💡 Chưa có dữ liệu phân bố theo xã/phường.")

    st.markdown("---")

    # Bản ghi gần đây
    st.markdown("### 📋 Hồ sơ được thêm gần đây")
    with st.spinner("Đang tải hồ sơ gần đây..."):
        recent_df = get_recent_records(10)
        
    if not recent_df.empty:
        # Đổi tên cột cho dễ đọc
        recent_df.columns = ["CCCD", "Họ tên", "Ngày sinh",
                             "Giới tính", "Xã/Phường", "Phân loại"]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("💡 Chưa có hồ sơ nào. Bấm vào **📝 Nhập liệu** để thêm mới.")

```

## views/login.py
```py
# -*- coding: utf-8 -*-
"""
Login Page - Security Profile 360
Giao diện đăng nhập và đổi mật khẩu
"""
import streamlit as st
from app.services.auth_service import authenticate, change_password, is_super_admin


def show_login_form():
    """Hiển thị form đăng nhập."""

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1>🔐 Security Profile 360</h1>
            <p style="color: #aaa;">Hệ thống quản lý hồ sơ an ninh</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        with st.form("login_form"):
            st.markdown("### Đăng nhập")

            username = st.text_input(
                "👤 Tên đăng nhập",
                placeholder="Nhập username"
            )

            password = st.text_input(
                "🔑 Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu"
            )

            submitted = st.form_submit_button(
                "🔓 Đăng nhập", type="primary", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                else:
                    user = authenticate(username, password)

                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"✅ Chào mừng, {user['ho_ten']}!")
                        st.rerun()
                    else:
                        st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")


def show_change_password_form():
    """Hiển thị form bắt buộc đổi mật khẩu (lần đầu đăng nhập)."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1>🔐 Đổi mật khẩu</h1>
            <p style="color: #ffc107;">⚠️ Bạn cần đổi mật khẩu trước khi tiếp tục</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        with st.form("change_password_form"):
            new_password = st.text_input(
                "🔑 Mật khẩu mới",
                type="password",
                placeholder="Ít nhất 6 ký tự"
            )

            confirm_password = st.text_input(
                "🔑 Xác nhận mật khẩu mới",
                type="password",
                placeholder="Nhập lại mật khẩu"
            )

            submitted = st.form_submit_button(
                "✅ Đổi mật khẩu", type="primary", use_container_width=True)

            if submitted:
                if not new_password or not confirm_password:
                    st.error("⚠️ Vui lòng nhập đầy đủ!")
                elif new_password != confirm_password:
                    st.error("❌ Mật khẩu không khớp!")
                elif len(new_password) < 6:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    user = st.session_state.user
                    success, msg = change_password(user['id'], new_password)

                    if success:
                        st.session_state.user['must_change_password'] = False
                        st.success("✅ Đổi mật khẩu thành công!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


def show_user_menu():
    """Hiển thị menu user ở sidebar."""
    user = st.session_state.get('user', {})

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **{user.get('ho_ten', 'User')}**")

    role_display = "🔑 Super Admin" if is_super_admin(user) else "👤 User"
    st.sidebar.caption(role_display)

    # Nút đổi mật khẩu
    if st.sidebar.button("🔐 Đổi mật khẩu", use_container_width=True):
        st.session_state.show_change_password = True
        st.rerun()

    # Nút đăng xuất
    if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
        logout()
        st.rerun()


def show_self_change_password():
    """Form đổi mật khẩu tự nguyện (không bắt buộc)."""
    st.markdown("### 🔐 Đổi mật khẩu")

    with st.form("self_change_password"):
        current_password = st.text_input(
            "Mật khẩu hiện tại",
            type="password"
        )

        new_password = st.text_input(
            "Mật khẩu mới",
            type="password",
            placeholder="Ít nhất 6 ký tự"
        )

        confirm_password = st.text_input(
            "Xác nhận mật khẩu mới",
            type="password"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("✅ Đổi mật khẩu", type="primary"):
                # Verify current password
                user = st.session_state.user
                check_user = authenticate(user['username'], current_password)

                if not check_user:
                    st.error("❌ Mật khẩu hiện tại không đúng!")
                elif new_password != confirm_password:
                    st.error("❌ Mật khẩu mới không khớp!")
                elif len(new_password) < 6:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    success, msg = change_password(user['id'], new_password)
                    if success:
                        st.success("✅ Đổi mật khẩu thành công!")
                        st.session_state.show_change_password = False
                    else:
                        st.error(f"❌ {msg}")

        with col2:
            if st.form_submit_button("❌ Hủy"):
                st.session_state.show_change_password = False
                st.rerun()


def logout():
    """Đăng xuất."""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.show_change_password = False


def is_logged_in() -> bool:
    """Kiểm tra đã đăng nhập chưa."""
    return st.session_state.get('logged_in', False)


def get_current_user():
    """Lấy thông tin user hiện tại."""
    return st.session_state.get('user', None)


def require_login():
    """
    Decorator/helper để yêu cầu đăng nhập.
    Trả về True nếu đã đăng nhập, False nếu chưa (và hiện form login).
    """
    if not is_logged_in():
        show_login_form()
        return False

    # Kiểm tra phải đổi mật khẩu không
    user = st.session_state.user
    if user.get('must_change_password'):
        show_change_password_form()
        return False

    return True

```

## views/nguon_du_lieu.py
```py
# -*- coding: utf-8 -*-
"""
Quản lý Nguồn dữ liệu - Security Profile 360
Theo dõi provenance của dữ liệu (OSINT Pattern)
"""
import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from app.services.auth_service import is_super_admin

logger = logging.getLogger(__name__)


def get_all_nguon_du_lieu():
    """Lấy danh sách tất cả nguồn dữ liệu."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, ten_nguon, loai_nguon, thoi_gian_import, 
                   nguoi_import, file_goc, ghi_chu
            FROM nguon_du_lieu
            ORDER BY thoi_gian_import DESC
        """, conn)
        return df
    except Exception as e:
        logger.warning(f"Lỗi lấy nguồn dữ liệu: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def add_nguon_du_lieu(ten_nguon, loai_nguon, nguoi_import, file_goc="", ghi_chu=""):
    """Thêm nguồn dữ liệu mới."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nguon_du_lieu (ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu))
        conn.commit()
        return True, "Đã thêm nguồn dữ liệu thành công"
    except Exception as e:
        return False, f"Lỗi: {e}"
    finally:
        conn.close()


def delete_nguon_du_lieu(nguon_id):
    """Xóa nguồn dữ liệu."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM nguon_du_lieu WHERE id = ?", (nguon_id,))
        conn.commit()
        return True, "Đã xóa nguồn dữ liệu"
    except Exception as e:
        return False, f"Lỗi: {e}"
    finally:
        conn.close()


def page_nguon_du_lieu():
    """Trang quản lý nguồn dữ liệu."""

    user = st.session_state.get('user', {})

    # Chỉ Super Admin mới có quyền
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 📦 Quản lý Nguồn dữ liệu")
    st.markdown("### Theo dõi nguồn gốc và provenance của dữ liệu")

    st.markdown("---")

    # Tabs
    tab_list, tab_add = st.tabs(["📋 Danh sách nguồn", "➕ Thêm nguồn mới"])

    with tab_list:
        df = get_all_nguon_du_lieu()

        if df.empty:
            st.info("💡 Chưa có nguồn dữ liệu nào được ghi nhận.")
        else:
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số nguồn", len(df))

            loai_counts = df['loai_nguon'].value_counts()
            if len(loai_counts) > 0:
                col2.metric("Loại phổ biến", loai_counts.index[0])

            # Display table
            st.markdown("#### 📋 Danh sách nguồn dữ liệu")

            # Format datetime
            if 'thoi_gian_import' in df.columns:
                df['thoi_gian_import'] = pd.to_datetime(
                    df['thoi_gian_import']).dt.strftime('%d/%m/%Y %H:%M')

            # Rename columns for display
            df_display = df.rename(columns={
                'id': 'ID',
                'ten_nguon': 'Tên nguồn',
                'loai_nguon': 'Loại nguồn',
                'thoi_gian_import': 'Thời gian import',
                'nguoi_import': 'Người import',
                'file_goc': 'File gốc',
                'ghi_chu': 'Ghi chú'
            })

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Delete section
            st.markdown("---")
            st.markdown("#### 🗑️ Xóa nguồn dữ liệu")

            nguon_options = {row['id']: f"{row['ten_nguon']} ({row['thoi_gian_import']})"
                             for _, row in df.iterrows()}

            if nguon_options:
                selected_id = st.selectbox(
                    "Chọn nguồn để xóa",
                    options=list(nguon_options.keys()),
                    format_func=lambda x: nguon_options[x]
                )

                if st.button("🗑️ Xóa nguồn đã chọn", type="secondary"):
                    success, msg = delete_nguon_du_lieu(selected_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with tab_add:
        st.markdown("#### ➕ Thêm nguồn dữ liệu mới")

        with st.form("add_nguon_form"):
            ten_nguon = st.text_input(
                "Tên nguồn dữ liệu *",
                placeholder="VD: Import Excel từ CA huyện Thanh Ba"
            )

            loai_nguon = st.selectbox(
                "Loại nguồn",
                options=["Excel Import", "Nhập tay",
                         "Từ đơn vị khác", "Xác minh", "Khác"]
            )

            col1, col2 = st.columns(2)

            with col1:
                nguoi_import = st.text_input(
                    "Người import",
                    value=user.get('ho_ten', '')
                )

            with col2:
                file_goc = st.text_input(
                    "Tên file gốc (nếu có)",
                    placeholder="vd: danh_sach_2024.xlsx"
                )

            ghi_chu = st.text_area(
                "Ghi chú",
                placeholder="Thông tin bổ sung về nguồn dữ liệu..."
            )

            if st.form_submit_button("✅ Thêm nguồn", type="primary"):
                if not ten_nguon:
                    st.error("⚠️ Vui lòng nhập tên nguồn!")
                else:
                    success, msg = add_nguon_du_lieu(
                        ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                    else:
                        st.error(f"❌ {msg}")

```

## views/nhap_excel.py
```py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.bulk_import import (
    create_excel_template,
    validate_excel_data,
    export_error_excel,
    bulk_import_all,
    TEMPLATE_DEFINITIONS
)

# Map key to readable name
IMPORT_OPTIONS = {
    "all": "📦 Trọn bộ (File 5 Sheet)",
    "doi_tuong": "👤 Thông tin đối tượng",
    "than_nhan": "👨‍👩‍👧‍👦 Thân nhân",
    "qua_trinh_hoat_dong": "⏳ Quá trình hoạt động",
    "lien_he": "📞 Liên hệ",
    "tai_chinh": "💳 Tài chính & Ngân hàng",
    "phuong_tien": "🚗 Phương tiện đi lại",
    "ho_so_dac_thu": "🌐 Hồ sơ CSXH (Đặc thù)"
}

# ============================================
# NHAP EXCEL PAGE
# ============================================


def page_nhap_excel():
    """Trang Nhập Excel - Import dữ liệu hàng loạt"""
    st.markdown("# 📥 Nhập Excel")
    st.markdown("### Import dữ liệu hàng loạt từ file Excel")

    st.markdown("---")

    # Select Import Mode
    col_mode, col_info = st.columns([1, 2])
    with col_mode:
        selected_mode_key = st.radio(
            "Chọn loại dữ liệu muốn nhập:",
            list(IMPORT_OPTIONS.keys()),
            format_func=lambda x: IMPORT_OPTIONS[x],
            help="Chọn 'Trọn bộ' để nhập file 5 sheet cũ, hoặc chọn từng mục để nhập file lẻ."
        )

    with col_info:
        st.info(f"""
        **Bạn đang chọn:** {IMPORT_OPTIONS[selected_mode_key]}
        
        *Hệ thống sẽ tạo file mẫu tương ứng với lựa chọn này. Vui lòng tải file mẫu, điền dữ liệu và upload lại.*
        """)

    # Option cho CSXH đặc thù
    csxh_type = None
    if selected_mode_key in ["all", "ho_so_dac_thu"]:
        with st.expander("Tùy chọn loại Hồ sơ CSXH (nếu có)", expanded=True):
            loai_csxh_options = {
                "Tổng hợp (tất cả loại)": None,
                "🤵 Hôn nhân với người nước ngoài": "Hon_Nhan_NN",
                "🏢 Làm việc cho tổ chức nước ngoài": "Lam_Viec_NN",
                "🎓 Du học/Công tác nước ngoài": "Hoc_Tap_Cong_Tac_NN",
                "⚠️ Vi phạm pháp luật ở nước ngoài": "Vi_Pham_NN",
                "🔍 Đã từng được xác minh": "Xac_Minh",
            }
            selected_csxh_label = st.selectbox(
                "Chọn loại hình đặc thù chi tiết:", list(loai_csxh_options.keys()))
            csxh_type = loai_csxh_options[selected_csxh_label]

    st.markdown("---")

    # ===== BƯỚC 1: TẢI FILE MẪU =====
    st.markdown("#### 📄 Bước 1: Tải file mẫu")

    # Generate template
    template_data = create_excel_template(
        import_type=selected_mode_key, csxh_type=csxh_type)
    file_name = f"mau_{selected_mode_key}.xlsx"
    if csxh_type:
        file_name = f"mau_{selected_mode_key}_{csxh_type}.xlsx"

    st.download_button(
        label=f"📥 Tải file mẫu: {IMPORT_OPTIONS[selected_mode_key]}",
        data=template_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        key=f"dl_btn_{selected_mode_key}"
    )

    st.markdown("---")

    # ===== BƯỚC 2: UPLOAD FILE =====
    st.markdown("#### 📤 Bước 2: Upload file Excel đã điền")

    uploaded_file = st.file_uploader(
        "Chọn file Excel",
        type=["xlsx", "xls"],
        key=f"uploader_{selected_mode_key}"
    )

    if uploaded_file is not None:
        st.success(f"✅ Đã tải lên: **{uploaded_file.name}**")

        st.markdown("---")

        # ===== BƯỚC 3: VALIDATE & PREVIEW =====
        st.markdown(
            f"#### 🔍 Bước 3: Kiểm tra dữ liệu ({IMPORT_OPTIONS[selected_mode_key]})")

        with st.spinner("Đang đọc và kiểm tra dữ liệu..."):
            # Validate with specific context
            validation_results = validate_excel_data(
                uploaded_file, import_type=selected_mode_key)

        # Calculate stats
        total_valid = sum(r['valid_count']
                          for r in validation_results.values())
        total_errors = sum(len(r['errors'])
                           for r in validation_results.values())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Bản ghi hợp lệ", total_valid)
        with col2:
            st.metric("❌ Lỗi phát hiện", total_errors)

        # Error file download
        if total_errors > 0:
            error_excel = export_error_excel(validation_results)
            if error_excel:
                st.download_button(
                    "📥 Tải file báo lỗi chi tiết",
                    data=error_excel,
                    file_name="baocao_loi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary"
                )

        # Show details based on mode
        st.markdown("##### 📋 Chi tiết dữ liệu:")

        # Helper to render tab content
        def render_tab_content(key_name, label):
            res = validation_results[key_name]
            st.caption(
                f"**{label}**: {res['valid_count']} hợp lệ | {len(res['errors'])} lỗi")

            if res['errors']:
                with st.expander(f"⚠️ Xem {len(res['errors'])} lỗi", expanded=True):
                    for err in res['errors'][:10]:
                        st.error(err)
                    if len(res['errors']) > 10:
                        st.warning(
                            f"... và {len(res['errors']) - 10} lỗi khác")

            if res['data'] is not None and not res['data'].empty:
                st.dataframe(res['data'].head(), use_container_width=True)
            elif res['valid_count'] == 0 and not res['errors']:
                st.info("Không có dữ liệu.")

        # If ALL, show Tabs. If Single, show just that section.
        if selected_mode_key == 'all':
            tabs = st.tabs([
                "👤 Đối tượng", "📞 Liên hệ", "👨‍👩‍👧‍👦 Thân nhân",
                "💳 Tài chính", "🚗 Phương tiện", "🌐 CSXH", "⏳ Quá trình"
            ])
            with tabs[0]:
                render_tab_content('doi_tuong', "Đối tượng")
            with tabs[1]:
                render_tab_content('lien_he', "Liên hệ")
            with tabs[2]:
                render_tab_content('than_nhan', "Thân nhân")
            with tabs[3]:
                render_tab_content('tai_chinh', "Tài chính")
            with tabs[4]:
                render_tab_content('phuong_tien', "Phương tiện")
            with tabs[5]:
                render_tab_content('ho_so_dac_thu', "Hồ sơ CSXH")
            with tabs[6]:
                render_tab_content('qua_trinh_hoat_dong', "Quá trình HĐ")

        else:
            # Single mode
            render_tab_content(selected_mode_key,
                               IMPORT_OPTIONS[selected_mode_key])

        # ===== BƯỚC 4: IMPORT =====
        st.markdown("---")
        st.markdown("#### 💾 Bước 4: Lưu vào cơ sở dữ liệu")

        if total_valid > 0:
            if total_errors > 0:
                st.warning(
                    f"⚠️ Đang có {total_errors} dòng lỗi. Hệ thống sẽ CHỈ LƯU {total_valid} dòng hợp lệ.")

            if st.button("🚀 Thực hiện Import", type="primary"):
                with st.spinner("Đang lưu vào database..."):
                    success, msg, stats = bulk_import_all(validation_results)

                    if success:
                        st.success(msg)
                        # Display detailed stats
                        cols = st.columns(
                            len([k for k, v in stats.items() if v > 0]) or 1)
                        idx = 0
                        for k, v in stats.items():
                            if v > 0:
                                with cols[idx]:
                                    st.metric(
                                        k.replace('_', ' ').title(), f"+{v}")
                                idx += 1
                        st.balloons()
                    else:
                        st.error(msg)
        else:
            st.error("🚫 Không có dữ liệu hợp lệ nào để import.")

```

## views/quan_ly_user.py
```py
# -*- coding: utf-8 -*-
"""
User Management Page - Security Profile 360
Quản lý tài khoản (chỉ Super Admin)
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.auth_service import (
    create_user,
    delete_user,
    change_password,
    get_all_users,
    is_super_admin,
    ROLE_SUPER_ADMIN,
    ROLE_USER
)


def page_quan_ly_user():
    """Trang quản lý tài khoản - Chỉ Super Admin."""

    user = st.session_state.get('user', {})

    # Kiểm tra quyền
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 👥 Quản lý tài khoản")
    st.markdown("### Tạo, xóa và quản lý người dùng hệ thống")

    st.markdown("---")

    # Tabs
    tab_list, tab_create = st.tabs(
        ["📋 Danh sách tài khoản", "➕ Tạo tài khoản mới"])

    with tab_list:
        show_user_list()

    with tab_create:
        show_create_user_form()


def show_user_list():
    """Hiển thị danh sách users."""
    users = get_all_users()

    if not users:
        st.info("💡 Chưa có tài khoản nào.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(users)

    # Format columns
    df['role_display'] = df['role'].apply(
        lambda x: '🔑 Super Admin' if x == ROLE_SUPER_ADMIN else '👤 User'
    )

    df['created_at'] = pd.to_datetime(
        df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    df['last_login'] = pd.to_datetime(
        df['last_login']).dt.strftime('%d/%m/%Y %H:%M')
    df['last_login'] = df['last_login'].fillna('Chưa đăng nhập')

    # Display table
    st.markdown("#### 📋 Danh sách tài khoản")

    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng tài khoản", len(users))
    col2.metric("Super Admin", len(
        [u for u in users if u['role'] == ROLE_SUPER_ADMIN]))
    col3.metric("User thường", len(
        [u for u in users if u['role'] == ROLE_USER]))

    st.markdown("---")

    # Interactive table with actions
    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

            with col1:
                role_icon = '🔑' if user['role'] == ROLE_SUPER_ADMIN else '👤'
                st.write(f"{role_icon} **{user['username']}**")

            with col2:
                st.write(user['ho_ten'] or '-')

            with col3:
                last_login = user.get('last_login')
                if last_login:
                    # Handle both datetime objects and strings
                    if isinstance(last_login, datetime):
                        login_str = last_login.strftime('%d/%m/%Y')
                    else:
                        login_str = str(last_login)[:10]
                    st.caption(f"Đăng nhập: {login_str}")
                else:
                    st.caption("Chưa đăng nhập")

            with col4:
                # Reset password button
                if st.button("🔐", key=f"reset_{user['id']}", help="Reset mật khẩu"):
                    st.session_state.reset_user_id = user['id']
                    st.session_state.reset_username = user['username']

            with col5:
                # Don't allow deleting self
                current_user = st.session_state.get('user', {})
                if user['id'] != current_user.get('id'):
                    if st.button("🗑️", key=f"del_{user['id']}", help="Xóa tài khoản"):
                        st.session_state.delete_user_id = user['id']
                        st.session_state.delete_username = user['username']

            st.markdown("---")

    # Reset password dialog
    if st.session_state.get('reset_user_id'):
        show_reset_password_dialog()

    # Delete confirmation dialog
    if st.session_state.get('delete_user_id'):
        show_delete_confirmation_dialog()


def show_reset_password_dialog():
    """Dialog reset mật khẩu."""
    user_id = st.session_state.reset_user_id
    username = st.session_state.reset_username

    st.warning(f"⚠️ Reset mật khẩu cho **{username}**")

    with st.form("reset_password_form"):
        new_password = st.text_input(
            "Mật khẩu mới",
            type="password",
            placeholder="Ít nhất 6 ký tự"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("✅ Reset", type="primary"):
                if len(new_password) >= 6:
                    success, msg = change_password(user_id, new_password)
                    if success:
                        st.success(f"✅ Đã reset mật khẩu cho {username}")
                        st.session_state.reset_user_id = None
                        st.session_state.reset_username = None
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")

        with col2:
            if st.form_submit_button("❌ Hủy"):
                st.session_state.reset_user_id = None
                st.session_state.reset_username = None
                st.rerun()


def show_delete_confirmation_dialog():
    """Dialog xác nhận xóa."""
    user_id = st.session_state.delete_user_id
    username = st.session_state.delete_username

    st.error(f"⚠️ Bạn có chắc muốn xóa tài khoản **{username}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Xóa", type="primary"):
            success, msg = delete_user(user_id)
            if success:
                st.success(f"✅ {msg}")
                st.session_state.delete_user_id = None
                st.session_state.delete_username = None
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Hủy"):
            st.session_state.delete_user_id = None
            st.session_state.delete_username = None
            st.rerun()


def show_create_user_form():
    """Form tạo tài khoản mới."""
    st.markdown("#### ➕ Tạo tài khoản mới")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "👤 Username *",
                placeholder="vd: nguyenvana"
            )

            password = st.text_input(
                "🔑 Mật khẩu *",
                type="password",
                placeholder="Ít nhất 6 ký tự"
            )

        with col2:
            ho_ten = st.text_input(
                "📝 Họ tên",
                placeholder="vd: Nguyễn Văn A"
            )

            role = st.selectbox(
                "🎭 Phân quyền",
                options=[ROLE_USER, ROLE_SUPER_ADMIN],
                format_func=lambda x: '👤 User thường' if x == ROLE_USER else '🔑 Super Admin'
            )

        must_change = st.checkbox(
            "Yêu cầu đổi mật khẩu khi đăng nhập lần đầu", value=True)

        submitted = st.form_submit_button("✅ Tạo tài khoản", type="primary")

        if submitted:
            if not username:
                st.error("⚠️ Username không được trống!")
            elif not password:
                st.error("⚠️ Mật khẩu không được trống!")
            elif len(password) < 6:
                st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
            else:
                success, msg = create_user(
                    username=username,
                    password=password,
                    ho_ten=ho_ten,
                    role=role,
                    must_change_password=must_change
                )

                if success:
                    st.success(f"✅ {msg}")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")

```

## views/ra_soat.py
```py
# -*- coding: utf-8 -*-
"""
Rà soát hàng loạt - Sử dụng Fuzzy Matching với ngưỡng 80%
Pattern từ thefuzz/rapidfuzz
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

# Import fuzzy matching module
try:
    from utils.fuzzy_matching import (
        batch_screen,
        classify_match,
        compare_names,
        THRESHOLD_SUSPECT,
        THRESHOLD_EXACT
    )
    FUZZY_MODULE_AVAILABLE = True
except ImportError:
    FUZZY_MODULE_AVAILABLE = False

# Fallback to rapidfuzz directly
try:
    from rapidfuzz import process as fuzz_process
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from utils.security_utils import sanitize_dataframe_for_csv

# ============================================
# CORE SCREENING FUNCTIONS
# ============================================

@st.cache_data(ttl=300)
def get_database_names():
    """Lấy danh sách họ tên từ database (Cached 5 min)"""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT cccd, ho_ten, ngay_sinh FROM doi_tuong", conn)
        return df
    finally:
        conn.close()


def process_batch_screening_v2(df_input):
    """
    Xử lý rà soát với fuzzy matching module mới.
    Sử dụng ngưỡng 80% đã được user phê duyệt.
    """
    if not FUZZY_MODULE_AVAILABLE and not RAPIDFUZZ_AVAILABLE:
        return [{
            "input": "Lỗi",
            "matched": "",
            "cccd": "",
            "status": "⚠️ Cần cài rapidfuzz: pip install rapidfuzz",
            "score": 0
        }]

    # Lấy danh sách đối tượng từ database
    df_db = get_database_names()

    if df_db.empty:
        return [{
            "input": "Lỗi",
            "matched": "",
            "cccd": "",
            "status": "❌ Database trống",
            "score": 0
        }]

    results = []

    # Xác định cột input
    if 'CCCD' in df_input.columns or 'cccd' in df_input.columns:
        col_name = 'CCCD' if 'CCCD' in df_input.columns else 'cccd'
        search_by = 'cccd'
    elif 'Họ tên' in df_input.columns or 'ho_ten' in df_input.columns:
        col_name = 'Họ tên' if 'Họ tên' in df_input.columns else 'ho_ten'
        search_by = 'ho_ten'
    elif 'input' in df_input.columns:
        col_name = 'input'
        search_by = 'auto'
    else:
        col_name = df_input.columns[0]
        search_by = 'auto'

    # Pre-process database for fast lookup
    db_names = df_db['ho_ten'].tolist()
    # Create Name -> CCCD mapping for O(1) lookup
    # Note: If duplicate names exist, this takes the last one. 
    # To match original logic (finding *a* match), this is acceptable or we use first.
    # Original logic: match.iloc[0] -> first match.
    # So we should build dict in reverse order or drop duplicates keeping first.
    df_unique = df_db.drop_duplicates(subset=['ho_ten'], keep='first')
    name_to_cccd = dict(zip(df_unique['ho_ten'], df_unique['cccd']))
    
    # CCCD set for O(1) exact check
    db_cccd_set = set(df_db['cccd'].astype(str))
    # Map cccd -> ho_ten
    cccd_to_name = dict(zip(df_db['cccd'].astype(str), df_db['ho_ten']))

    for idx, row in df_input.iterrows():
        input_value = str(row[col_name]).strip()

        if not input_value:
            continue

        # Xác định loại search
        if search_by == 'auto':
            if input_value.isdigit() and len(input_value) == 12:
                current_search = 'cccd'
            else:
                current_search = 'ho_ten'
        else:
            current_search = search_by

        # Tìm kiếm
        if current_search == 'cccd':
            # Tìm chính xác CCCD - O(1) lookup
            if input_value in db_cccd_set:
                results.append({
                    'input': input_value,
                    'matched': cccd_to_name.get(input_value, ''),
                    'cccd': input_value,
                    'status': '✅ Khớp chính xác',
                    'score': 100,
                    'alternatives': []
                })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Không tìm thấy',
                    'score': 0,
                    'alternatives': []
                })
        else:
            # Fuzzy matching họ tên - sử dụng module mới
            if FUZZY_MODULE_AVAILABLE:
                # Sử dụng batch_screen từ fuzzy_matching module
                # Pass pre-converted list to avoid overhead
                screen_results = batch_screen(
                    [input_value],
                    db_names,
                    threshold=THRESHOLD_SUSPECT  # 80%
                )

                if screen_results and screen_results[0]['matched']:
                    result = screen_results[0]
                    # Tìm CCCD tương ứng - O(1) lookup
                    cccd = name_to_cccd.get(result['matched'], '')

                    results.append({
                        'input': input_value,
                        'matched': result['matched'],
                        'cccd': cccd,
                        'status': result['status'],
                        'score': result['score'],
                        'alternatives': result.get('alternatives', [])
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': 0,
                        'alternatives': []
                    })
            else:
                # Fallback to rapidfuzz directly
                match_result = fuzz_process.extractOne(
                    input_value,
                    db_names,
                    scorer=fuzz.token_set_ratio
                )

                if match_result and match_result[1] >= 80:  # 80% threshold
                    matched_name = match_result[0]
                    cccd = name_to_cccd.get(matched_name, '')

                    if match_result[1] >= 95:
                        status = '✅ Khớp chính xác'
                    else:
                        status = '⚠️ Nghi vấn - cần kiểm tra'

                    results.append({
                        'input': input_value,
                        'matched': matched_name,
                        'cccd': cccd,
                        'status': status,
                        'score': match_result[1],
                        'alternatives': []
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': match_result[0] if match_result else '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': match_result[1] if match_result else 0,
                        'alternatives': []
                    })

    return results


def display_screening_results(results):
    """Hiển thị kết quả rà soát với chi tiết đầy đủ"""
    if not results:
        st.warning("Không có kết quả")
        return

    df_results = pd.DataFrame(results)

    # Thống kê
    st.markdown("---")
    st.markdown("### 📊 Kết quả rà soát")

    col1, col2, col3, col4 = st.columns(4)

    exact_match = len([r for r in results if '✅' in r['status']])
    suspicious = len([r for r in results if '⚠️' in r['status']])
    not_found = len([r for r in results if '❌' in r['status']])
    total = len(results)

    col1.metric("📋 Tổng số", total)
    col2.metric("✅ Khớp chính xác", exact_match)
    col3.metric("⚠️ Nghi vấn (≥80%)", suspicious)
    col4.metric("❌ Không tìm thấy", not_found)

    st.markdown("---")

    # Tabs cho các loại kết quả
    tab_all, tab_suspect, tab_exact, tab_notfound = st.tabs([
        f"📋 Tất cả ({total})",
        f"⚠️ Nghi vấn ({suspicious})",
        f"✅ Khớp ({exact_match})",
        f"❌ Không tìm thấy ({not_found})"
    ])

    def render_table(data):
        if not data:
            st.info("Không có dữ liệu")
            return
        df = pd.DataFrame(data)
        # Remove alternatives column for display
        if 'alternatives' in df.columns:
            df = df.drop(columns=['alternatives'])
        df_display = df.rename(columns={
            'input': 'Đầu vào',
            'matched': 'Kết quả khớp',
            'cccd': 'CCCD',
            'status': 'Trạng thái',
            'score': 'Độ tương đồng (%)'
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab_all:
        render_table(results)

    with tab_suspect:
        suspect_results = [r for r in results if '⚠️' in r['status']]
        render_table(suspect_results)

        # Hiển thị chi tiết alternatives nếu có
        if suspect_results:
            st.markdown("#### 🔍 Chi tiết nghi vấn")
            for r in suspect_results:
                if r.get('alternatives'):
                    with st.expander(f"📌 {r['input']} → {r['matched']} ({r['score']}%)"):
                        st.write("**Các kết quả khớp khác:**")
                        for alt in r['alternatives']:
                            st.write(f"  - {alt['name']} ({alt['score']}%)")

    with tab_exact:
        exact_results = [r for r in results if '✅' in r['status']]
        render_table(exact_results)

    with tab_notfound:
        notfound_results = [r for r in results if '❌' in r['status']]
        render_table(notfound_results)

    st.markdown("---")

    # Export
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        # Export all
        export_df = pd.DataFrame(results)
        if 'alternatives' in export_df.columns:
            export_df = export_df.drop(columns=['alternatives'])
        st.download_button(
            label="📥 Xuất toàn bộ kết quả (CSV)",
            data=sanitize_dataframe_for_csv(export_df).to_csv(index=False).encode('utf-8-sig'),
            file_name=f"ket_qua_ra_soat_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    with col_exp2:
        # Export only suspicious
        suspect_results = [r for r in results if '⚠️' in r['status']]
        if suspect_results:
            suspect_df = pd.DataFrame(suspect_results)
            if 'alternatives' in suspect_df.columns:
                suspect_df = suspect_df.drop(columns=['alternatives'])
            st.download_button(
                label="⚠️ Xuất chỉ các nghi vấn (CSV)",
                data=sanitize_dataframe_for_csv(suspect_df).to_csv(index=False).encode('utf-8-sig'),
                file_name=f"nghi_van_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )


# ============================================
# COMPARE TWO NAMES TOOL
# ============================================

def show_compare_tool():
    """Tool so sánh 2 tên trực tiếp"""
    st.markdown("### 🔬 So sánh 2 tên")
    st.caption("Công cụ đánh giá độ tương đồng giữa 2 tên (Pattern: thefuzz)")

    col1, col2 = st.columns(2)

    with col1:
        name1 = st.text_input("Tên thứ nhất", placeholder="Nguyễn Văn An")

    with col2:
        name2 = st.text_input("Tên thứ hai", placeholder="Nguyễn Văn Ân")

    if st.button("🔍 So sánh", type="primary"):
        if name1 and name2:
            if FUZZY_MODULE_AVAILABLE:
                scores = compare_names(name1, name2)

                st.markdown("---")
                st.markdown("#### 📊 Kết quả so sánh")

                cols = st.columns(5)
                cols[0].metric("Ratio", f"{scores['ratio']}%")
                cols[1].metric("Partial", f"{scores['partial_ratio']}%")
                cols[2].metric("Token Sort", f"{scores['token_sort']}%")
                cols[3].metric("Token Set", f"{scores['token_set']}%")
                cols[4].metric("Weighted", f"{scores['weighted']}%")

                best = scores['best']
                status, _ = classify_match(best)

                st.markdown("---")
                st.markdown(f"### Kết luận: {status}")
                st.progress(best / 100)

                if best >= 80:
                    st.success(
                        f"✅ Độ tương đồng {best}% ≥ 80% → Có thể là cùng 1 người")
                else:
                    st.warning(f"⚠️ Độ tương đồng {best}% < 80% → Khác người")
            else:
                # Fallback
                score = fuzz.token_set_ratio(name1.lower(), name2.lower())
                st.metric("Độ tương đồng", f"{score}%")
        else:
            st.warning("Vui lòng nhập cả 2 tên")


# ============================================
# RA SOAT PAGE
# ============================================

def page_ra_soat():
    """Trang Rà soát - Kiểm tra danh sách hàng loạt với fuzzy matching 80%"""
    st.markdown("# 🔎 Rà soát hàng loạt")
    st.markdown("### Kiểm tra danh sách nhân sự với cơ sở dữ liệu")

    st.markdown("---")

    st.info("""
    **Tính năng rà soát sử dụng Fuzzy Matching (ngưỡng 80%):**
    - ✅ **Khớp chính xác** (≥95%): Tên hoàn toàn giống nhau
    - ⚠️ **Nghi vấn** (≥80%): Tên tương tự, cần kiểm tra thủ công (ví dụ: "Văn An" vs "Văn Ân")
    - ❌ **Không tìm thấy** (<80%): Không có trong database hoặc khác biệt lớn
    """)

    # Tab cho các cách nhập
    tab_upload, tab_paste, tab_compare = st.tabs([
        "📥 Upload Excel",
        "📝 Nhập trực tiếp",
        "🔬 So sánh 2 tên"
    ])

    with tab_upload:
        st.markdown("#### 📥 Upload file Excel")
        uploaded_file = st.file_uploader(
            "Chọn file Excel (cần có cột CCCD hoặc Họ tên)",
            type=["xlsx", "xls"],
            key="ra_soat_upload"
        )

        if uploaded_file:
            try:
                df_input = pd.read_excel(uploaded_file)
                st.success(f"✅ Đã đọc {len(df_input)} dòng từ file")
                st.dataframe(df_input.head(10), use_container_width=True)

                # Xử lý rà soát
                if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_excel"):
                    with st.spinner("Đang rà soát với ngưỡng 80%..."):
                        try:
                            results = process_batch_screening_v2(df_input)
                            display_screening_results(results)
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error(f"Lỗi rà soát batch: {e}")
                            st.error("❌ Đã xảy ra lỗi trong quá trình rà soát. Vui lòng thử lại.")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Lỗi đọc file Excel: {e}")
                st.error("❌ Lỗi đọc file Excel. Vui lòng đảm bảo file đúng định dạng và có cột CCCD hoặc Họ tên.")

    with tab_paste:
        st.markdown("#### 📝 Nhập danh sách trực tiếp")
        st.caption("Mỗi dòng là một CCCD hoặc Họ tên")

        input_text = st.text_area(
            "Danh sách",
            placeholder="001234567890\nNguyễn Văn A\n002345678901\n...",
            height=200
        )

        if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_paste"):
            if input_text.strip():
                lines = [line.strip()
                         for line in input_text.strip().split('\n') if line.strip()]
                df_input = pd.DataFrame({'input': lines})

                with st.spinner("Đang rà soát với ngưỡng 80%..."):
                    results = process_batch_screening_v2(df_input)
                    display_screening_results(results)
            else:
                st.warning("⚠️ Vui lòng nhập danh sách!")

    with tab_compare:
        show_compare_tool()

```

## views/tra_cuu.py
```py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from constants import (
    TINH_OPTIONS, GIOI_TINH_OPTIONS, LOAI_HINH_DAC_THU
)
from utils.text_utils import normalize_string
from utils.security_utils import sanitize_dataframe_for_csv


def is_fuzzy_match(query, text):
    """
    Kiểm tra query có phải là match của text không.
    Hỗ trợ:
    1. Containment (sau khi chuẩn hóa)
    2. Subsequence (các ký tự của query xuất hiện thứ tự trong text)
       - VIPHUONG -> Vi Ngoc Phuong
    """
    if not query or not text:
        return False

    n_query = normalize_string(query)
    n_text = normalize_string(text)

    # 1. Exact contains (relaxed)
    if n_query in n_text:
        return True

    # 2. Subsequence match (cho trường hợp viết tắt hoặc bỏ qua tên đệm)
    # Ví dụ: "viphuong" -> "Vi Ngoc Phuong" (v...i...p...h...u...o...n...g)
    # Chỉ áp dụng nếu query đủ dài để tránh nhiễu
    if len(n_query) >= 3:
        it = iter(n_text)
        if all(char in it for char in n_query):
            return True

    return False


def get_search_candidates(conn, search_query, search_type,
                          filter_tinh, filter_gioi_tinh):
    """
    Thực hiện tìm kiếm đối tượng và trả về danh sách CCCD phù hợp.
    Chiến lược Column Pruning:
    1. Lấy index (cccd, ho_ten)
    2. Lọc bằng Python (fuzzy match)
    3. Trả về danh sách CCCD
    """
    # 1. Fetch lightweight index
    sql_index = "SELECT cccd, ho_ten FROM doi_tuong WHERE 1=1"
    params = []

    # Apply filters to SQL index query to reduce initial load
    if filter_tinh != "Tất cả":
        sql_index += " AND dia_chi_tinh = ?"
        params.append(filter_tinh)

    if filter_gioi_tinh != "Tất cả":
        sql_index += " AND gioi_tinh = ?"
        params.append(filter_gioi_tinh)

    df_index = pd.read_sql_query(sql_index, conn, params=params)

    if df_index.empty:
        return []

    # Pre-compute normalization
    query_norm = normalize_string(search_query)
    query_lower = search_query.lower()

    # 2. Apply Text Filters (Vectorized + Subsequence)

    # 2.1 CCCD Match (Vectorized)
    mask_cccd = pd.Series(False, index=df_index.index)
    if search_type in ["Tất cả", "CCCD"]:
        mask_cccd = df_index['cccd'].astype(str).str.contains(
            query_lower, case=False, na=False)

    # 2.2 Ho ten Match (Vectorized + Subsequence)
    mask_hoten = pd.Series(False, index=df_index.index)
    if search_type in ["Tất cả", "Họ tên"]:
        # Normalize 'ho_ten' column
        normalized_hoten = df_index['ho_ten'].apply(
            lambda x: normalize_string(x) if x else "")

        # Check containment (Fast)
        mask_hoten_contains = normalized_hoten.str.contains(
            query_norm,
            na=False,
            regex=False
        )
        mask_hoten = mask_hoten_contains

        # Check subsequence (Slower, only if query >= 3 chars)
        if len(query_norm) >= 3:
            def check_subsequence(text_norm):
                it = iter(text_norm)
                return all(char in it for char in query_norm)

            # Only check rows that failed containment
            remaining_indices = ~mask_hoten_contains
            if remaining_indices.any():
                subsequence_matches = normalized_hoten[
                    remaining_indices].apply(check_subsequence)
                mask_hoten = mask_hoten | subsequence_matches.reindex(
                    df_index.index, fill_value=False)

    # Combine masks
    final_mask = mask_cccd | mask_hoten
    matching_cccds = df_index[final_mask]['cccd'].tolist()

    return matching_cccds


def fetch_doi_tuong_details(conn, cccd_list):
    """Lấy thông tin chi tiết cho danh sách CCCD"""
    if not cccd_list:
        return pd.DataFrame()
        
    placeholders = ','.join(['?'] * len(cccd_list))
    sql_details = f"SELECT * FROM doi_tuong WHERE cccd IN ({placeholders})"
    
    # We want to preserve order of cccd_list if possible, but IN clause doesn't guarantee order.
    # However, for display purposes, we might want to sort by created_at DESC or relevance.
    # Let's sort by created_at DESC to match default view.
    sql_details += " ORDER BY created_at DESC"
    
    return pd.read_sql_query(sql_details, conn, params=cccd_list)


# ============================================
# TRA CUU PAGE
# ============================================


def page_tra_cuu():
    """Trang Tra cứu - Tìm kiếm đối tượng"""
    st.markdown("# 🔍 Tra cứu")
    st.markdown("### Tìm kiếm và tra cứu hồ sơ đối tượng")

    st.markdown("---")

    # Thanh tìm kiếm
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search_query = st.text_input(
            "Tìm kiếm",
            placeholder="Nhập CCCD, họ tên (có thể viết tắt, vd: viphuong)...",
            label_visibility="collapsed",
            help="Hỗ trợ tìm kiếm theo CCCD hoặc Họ tên "
                 "(bao gồm tìm kiếm không dấu và viết tắt)"
        )

    with col2:
        search_type = st.selectbox(
            "Loại",
            ["Tất cả", "CCCD", "Họ tên"],
            label_visibility="collapsed"
        )

    with col3:
        # Assign to _ to avoid flake8 F841
        _ = st.button(
            "🔍 Tìm kiếm", type="primary", use_container_width=True)

    st.markdown("---")

    # Bộ lọc nâng cao
    with st.expander("🎛️ Bộ lọc nâng cao", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_tinh = st.selectbox(
                "Tỉnh/TP",
                ["Tất cả"] + TINH_OPTIONS,
                help="Lọc danh sách theo Tỉnh/Thành phố thường trú"
            )
        with col2:
            filter_gioi_tinh = st.selectbox(
                "Giới tính",
                ["Tất cả"] + GIOI_TINH_OPTIONS,
                help="Lọc danh sách theo Giới tính"
            )
        with col3:
            # Assign to _ to avoid flake8 F841
            _ = st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values()),
                help="Lọc theo các loại hồ sơ chính sách xã hội "
                     "(kết hôn nước ngoài, xuất cảnh, v.v.)"
            )

    st.markdown("---")

    # Pagination settings
    ITEMS_PER_PAGE = 50

    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")

    conn = get_connection()
    try:
        if search_query:
            # SEARCH MODE with Pagination
            # 1. Get candidates (List of CCCDs)
            candidates = get_search_candidates(
                conn, search_query, search_type, filter_tinh, filter_gioi_tinh)
            
            total_count = len(candidates)
            st.info(
                f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'")
            
            if total_count > 0:
                # 2. Pagination UI
                total_pages = max(
                    1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

                col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
                with col_page2:
                    current_page = st.number_input(
                        f"Trang (tổng {total_pages} trang, {total_count} hồ sơ)",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key="search_page_query"
                    )
                
                # 3. Slice candidates for current page
                offset = (current_page - 1) * ITEMS_PER_PAGE
                page_cccds = candidates[offset : offset + ITEMS_PER_PAGE]
                
                # 4. Fetch details for current page
                df = fetch_doi_tuong_details(conn, page_cccds)
            else:
                df = pd.DataFrame()

        else:
            # NO SEARCH MODE (Default View)
            # Đếm tổng số records với filter
            count_query = "SELECT COUNT(*) as total FROM doi_tuong WHERE 1=1"
            count_params = []
            
            if filter_tinh != "Tất cả":
                count_query += " AND dia_chi_tinh = ?"
                count_params.append(filter_tinh)
            
            if filter_gioi_tinh != "Tất cả":
                count_query += " AND gioi_tinh = ?"
                count_params.append(filter_gioi_tinh)

            total_count = pd.read_sql_query(count_query, conn, params=count_params).iloc[0, 0]

            # Pagination UI
            total_pages = max(
                1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page2:
                current_page = st.number_input(
                    f"Trang (tổng {total_pages} trang, {total_count} hồ sơ)",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    key="search_page_default"
                )

            offset = (current_page - 1) * ITEMS_PER_PAGE

            # Hiển thị với pagination và filter SQL
            query = """
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                WHERE 1=1
            """
            params = []
            
            if filter_tinh != "Tất cả":
                query += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)
            
            if filter_gioi_tinh != "Tất cả":
                query += " AND gioi_tinh = ?"
                params.append(filter_gioi_tinh)
                
            query += """
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([ITEMS_PER_PAGE, offset])
            
            df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

    if not df.empty:
        # Đổi tên cột
        display_df = df.copy()
        if 'cccd' in display_df.columns:
            col_map = {
                'cccd': 'CCCD',
                'ho_ten': 'Họ tên',
                'ngay_sinh': 'Ngày sinh',
                'gioi_tinh': 'Giới tính',
                'dia_chi_xa': 'Xã/Phường',
                'phan_loai_nghe_nghiep': 'Phân loại',
                'dia_chi_tinh': 'Tỉnh/TP',
                'chi_tiet_nghe_nghiep': 'Nơi làm việc',
                'ghi_chu_chung': 'Ghi chú'
            }
            display_df = display_df.rename(
                columns={k: v for k, v in col_map.items()
                         if k in display_df.columns})

        st.caption("💡 Chọn một dòng trong bảng để xem chi tiết hồ sơ.")
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="search_result_table"
        )

        if event.selection.rows:
            selected_index = event.selection.rows[0]
            # Use original df to get CCCD safely (indices align with display_df)
            selected_cccd = str(df.iloc[selected_index]['cccd'])
            st.session_state.view_profile_cccd = selected_cccd
            st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=sanitize_dataframe_for_csv(df).to_csv(
                index=False).encode('utf-8-sig'),
            file_name=f"danh_sach_doi_tuong_"
            f"{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("💡 Không có dữ liệu.")
        if search_query:
            if st.button(f"➕ Thêm mới hồ sơ: {search_query}",
                         type="secondary", use_container_width=True):
                # Determine if numeric (CCCD) or text (Name)
                if search_query.isdigit() and len(search_query) == 12:
                    st.session_state.nl_cccd = search_query
                    st.session_state.nl_ho_ten = ""
                else:
                    st.session_state.nl_cccd = ""
                    st.session_state.nl_ho_ten = search_query

                # Navigate to Nhap lieu
                st.session_state.main_menu = "Nhập liệu"
                st.rerun()
        else:
            st.info("Hãy thêm đối tượng mới trong phần **📝 Nhập liệu**.")

```

## views/__init__.py
```py
from .dashboard import page_dashboard
from .nhap_lieu import page_nhap_lieu
from .tra_cuu import page_tra_cuu
from .profile import page_profile_view
from .ra_soat import page_ra_soat
from .nhap_excel import page_nhap_excel

__all__ = [
    'page_dashboard',
    'page_nhap_lieu',
    'page_tra_cuu',
    'page_profile_view',
    'page_ra_soat',
    'page_nhap_excel'
]

```

## views/nhap_lieu/ui.py
```py
# -*- coding: utf-8 -*-
import streamlit as st
import json
import logging
from datetime import datetime, date

from constants import (
    GIOI_TINH_OPTIONS, TINH_OPTIONS, DANH_SACH_XA_PHU_THO,
    PHAN_LOAI_NGHE_NGHIEP_OPTIONS, LOAI_LIEN_HE_OPTIONS,
    DANH_SACH_NGAN_HANG, LOAI_XE_OPTIONS, LOAI_HINH_DAC_THU,
    DANH_SACH_QUOC_GIA, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB,
    LOAI_TAI_LIEU_OPTIONS, Messages
)
from services import (
    check_cccd_exists, save_doi_tuong, save_lien_he,
    save_tai_chinh, save_phuong_tien, save_nhan_than,
    save_ho_so_dac_thu, save_tai_lieu
)
from database import (
    get_qua_trinh_hoat_dong, delete_qua_trinh_hoat_dong,
    save_qua_trinh_hoat_dong
)
from views.profile import (
    get_nhan_than_by_cccd, get_lien_he_by_cccd,
    get_tai_chinh_by_cccd, get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd, get_tai_lieu_by_cccd,
    get_file_path, delete_nhan_than, delete_lien_he,
    delete_tai_chinh, delete_phuong_tien, delete_ho_so_dac_thu,
    delete_tai_lieu
)
from .utils import validate_cccd_for_action

logger = logging.getLogger(__name__)

# ===================================================================
# Helper: khởi tạo staging state
# ===================================================================
def _init_staging():
    """Khởi tạo các key staging trong session_state nếu chưa có."""
    defaults = {
        "nl_staging_nhan_than": [],   # list[dict]
        "nl_staging_qt": [],           # list[dict]
        "nl_staging_lien_he": [],      # list[dict]
        "nl_staging_tai_chinh": [],    # list[dict]
        "nl_staging_phuong_tien": [],  # list[dict]
        "nl_staging_dac_thu": [],      # list[dict]  {loai_hinh, noi_dung, ghi_chu}
        "nl_staging_tai_lieu": [],     # list[dict]  {file, loai, mo_ta}
        "nl_them_bo_sung": False,      # True khi CCCD đã có → chỉ thêm satellite
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_form():
    """Xoá toàn bộ staging và reset form."""
    staging_keys = [
        "nl_staging_nhan_than", "nl_staging_qt", "nl_staging_lien_he",
        "nl_staging_tai_chinh", "nl_staging_phuong_tien",
        "nl_staging_dac_thu", "nl_staging_tai_lieu", "nl_them_bo_sung",
        "nl_cccd", "nl_ho_ten",
    ]
    for k in staging_keys:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.current_cccd = None


# ===================================================================
# Helper: preview staging list trong từng tab
# ===================================================================
def _render_staging_list(key: str, label_fn, empty_msg: str):
    """
    Hiển thị danh sách items đang chờ lưu từ staging.
    label_fn(item) -> str nhãn hiển thị cho mỗi item.
    Trả về True nếu list không rỗng.
    """
    items = st.session_state.get(key, [])
    if not items:
        return False
    st.markdown(f"**📋 Danh sách chờ lưu ({len(items)} mục):**")
    for i, item in enumerate(items):
        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(f"↳ {label_fn(item)}")
        with col_del:
            if st.button("🗑️", key=f"del_{key}_{i}", help="Xoá khỏi danh sách"):
                st.session_state[key].pop(i)
                st.rerun()
    return True


# ===================================================================
# Main page
# ===================================================================
def page_nhap_lieu():
    """Trang Nhập liệu - Form thêm mới / bổ sung hồ sơ đối tượng"""
    _init_staging()

    st.markdown("# 📝 Nhập liệu")
    st.markdown("### Thêm mới / bổ sung hồ sơ đối tượng")

    # ------------------------------------------------------------------
    # Banner hướng dẫn
    # ------------------------------------------------------------------
    st.info(
        "💡 **Hướng dẫn:** Nhập thông tin tự do ở tất cả các tab, "
        "sau đó nhấn **✅ Lưu toàn bộ hồ sơ** một lần ở cuối trang.",
        icon=None
    )
    st.markdown("---")

    # Tabs cho các phần nhập liệu
    tab1, tab_nhan_than, tab_qt, tab2, tab3, tab_tai_lieu = st.tabs([
        "👤 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
        "⏳ Quá trình hoạt động",
        "📞 Liên hệ & Tài sản",
        "🌐 Yếu tố nước ngoài",
        "📎 Tài liệu đính kèm"
    ])

    # ==================================================================
    # TAB 1 – THÔNG TIN CÁ NHÂN
    # ==================================================================
    with tab1:
        st.markdown("#### 📋 Thông tin cơ bản")
        st.caption("🔑 CCCD và Họ tên là bắt buộc để lưu hồ sơ.")

        col1, col2 = st.columns(2)

        with col1:
            cccd = st.text_input(
                "Số CCCD *",
                placeholder="Nhập 12 số CCCD",
                max_chars=12,
                help="Số căn cước công dân 12 số",
                key="nl_cccd"
            )

            ho_ten = st.text_input(
                "Họ và tên *",
                placeholder="Nguyễn Văn A",
                help="Họ tên đầy đủ theo giấy tờ",
                key="nl_ho_ten"
            )

            # Avatar Upload
            st.markdown("##### 📸 Ảnh đại diện")
            avatar_file = st.file_uploader(
                "Tải lên ảnh chân dung", type=['png', 'jpg', 'jpeg'],
                key="main_avatar_uploader"
            )

            ngay_sinh = st.date_input(
                "Ngày sinh",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=datetime.now().date(),
                format="DD/MM/YYYY",
                help="Chọn ngày sinh",
                key="main_ngay_sinh"
            )

            gioi_tinh = st.selectbox(
                "Giới tính",
                GIOI_TINH_OPTIONS,
                help="Giới tính theo CCCD"
            )

        with col2:
            dia_chi_tinh = st.selectbox(
                "Tỉnh/TP",
                TINH_OPTIONS,
                help="Tỉnh/Thành phố thường trú"
            )

            if dia_chi_tinh == "Phú Thọ":
                dia_chi_xa = st.selectbox(
                    "Xã/Phường",
                    ["-- Chọn xã/phường --"] + DANH_SACH_XA_PHU_THO,
                    key="xa_phuong_select",
                    help="Chọn xã/phường từ danh sách"
                )
                if dia_chi_xa == "-- Chọn xã/phường --":
                    dia_chi_xa = ""
            else:
                dia_chi_xa = st.text_input(
                    "Địa chỉ chi tiết",
                    placeholder="Số nhà, đường, xã/phường, quận/huyện, tỉnh/TP"
                )

            phan_loai = st.selectbox(
                "Phân loại nghề nghiệp",
                PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
                help="Phân loại công việc hiện tại"
            )

            chi_tiet_nghe = st.text_input(
                "Chi tiết nơi làm việc",
                placeholder="Ví dụ: Công an tỉnh Phú Thọ",
                help="Tên cơ quan, tổ chức đang làm việc"
            )

        st.markdown("---")
        ghi_chu = st.text_area(
            "Ghi chú chung",
            placeholder="Các thông tin ghi chú khác...",
            height=100,
            help="Ghi chú thêm về đối tượng"
        )

        # Cảnh báo khi CCCD đã tồn tại
        if cccd and len(cccd) == 12:
            if check_cccd_exists(cccd):
                st.warning(
                    f"⚠️ CCCD **{cccd}** đã có trong hệ thống. "
                    "Chỉ dữ liệu **thân nhân / liên hệ / tài sản / văn bản** "
                    "sẽ được bổ sung thêm — thông tin cá nhân cơ bản sẽ không bị ghi đè."
                )
                st.session_state.nl_them_bo_sung = True
            else:
                st.session_state.nl_them_bo_sung = False

    # ==================================================================
    # TAB THÂN NHÂN
    # ==================================================================
    with tab_nhan_than:
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin thân nhân")

        # Hiển thị danh sách đã có trong DB (nếu CCCD đã tồn tại)
        cccd_now = st.session_state.get("nl_cccd", "")
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_nt_db = get_nhan_than_by_cccd(cccd_now)
            if not df_nt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_nt_db)} thân nhân)", expanded=False):
                    for _, row in df_nt_db.iterrows():
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            st.markdown(
                                f"**{row['loai_quan_he']}**: {row['ho_ten']} | "
                                f"📅 {row['ngay_sinh'] or 'N/A'} | "
                                f"💼 {row['nghe_nghiep'] or 'N/A'}"
                            )
                        with col_del:
                            with st.popover("🗑️", help=f"Xóa {row['ho_ten']}"):
                                st.markdown(f"Bạn có chắc muốn xóa **{row['ho_ten']}**?")
                                if st.button("Xác nhận xóa", key=f"del_nt_db_{row['id']}", type="primary"):
                                    delete_nhan_than(row['id'])
                                    st.toast(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}")
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_nhan_than",
            lambda x: f"**{x['loai_quan_he']}**: {x['ho_ten']} | {x['nghe_nghiep'] or ''}",
            "Chưa có thân nhân nào trong danh sách chờ."
        )

        st.markdown("##### ➕ Thêm thân nhân mới")

        loai_quan_he = st.selectbox(
            "Loại quan hệ",
            ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ",
             "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
            key="nt_loai_quan_he"
        )

        col1, col2 = st.columns(2)
        with col1:
            nt_ho_ten = st.text_input("Họ và tên *", placeholder="Nguyễn Văn A", key="nt_ho_ten")
            nt_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD (nếu có)", key="nt_cccd")
            nt_ngay_sinh = st.date_input(
                "Ngày sinh", value=None, key="nt_ngay_sinh", format="DD/MM/YYYY",
                min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)
            )
        with col2:
            nt_phan_loai_nghe = st.selectbox("Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="nt_phan_loai_nghe")
            nt_nghe_nghiep = st.text_input("Chi tiết nghề nghiệp", placeholder="Giáo viên THPT...", key="nt_nghe_nghiep")
            nt_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="nt_noi_o")

        nt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="nt_ghi_chu")

        if st.button("➕ Thêm vào danh sách", key="btn_add_nhan_than", use_container_width=True):
            if nt_ho_ten:
                nghe_nghiep_full = f"{nt_phan_loai_nghe}: {nt_nghe_nghiep}" if nt_nghe_nghiep else nt_phan_loai_nghe
                st.session_state.nl_staging_nhan_than.append({
                    "loai_quan_he": loai_quan_he,
                    "ho_ten": nt_ho_ten,
                    "cccd_nhan_than": nt_cccd,
                    "ngay_sinh": nt_ngay_sinh.strftime('%Y-%m-%d') if nt_ngay_sinh else None,
                    "nghe_nghiep": nghe_nghiep_full,
                    "noi_o": nt_noi_o,
                    "ghi_chu": nt_ghi_chu,
                })
                st.toast(f"✅ Đã thêm {loai_quan_he}: {nt_ho_ten} vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập họ tên thân nhân!")

    # ==================================================================
    # TAB QUÁ TRÌNH HOẠT ĐỘNG
    # ==================================================================
    with tab_qt:
        st.markdown("#### ⏳ Quá trình hoạt động (Lịch sử nhân thân)")

        # Hiển thị dữ liệu đã có trong DB
        cccd_now = st.session_state.get("nl_cccd", "")
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            qt_list_db = get_qua_trinh_hoat_dong(cccd_now)
            if qt_list_db:
                with st.expander(f"📂 Đã có trong hệ thống ({len(qt_list_db)} mục)", expanded=False):
                    for item in qt_list_db:
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            st.markdown(f"**{item['thoi_gian']}**: {item['noi_dung']}")
                        with col_del:
                            with st.popover("🗑️", help="Xóa quá trình này"):
                                st.markdown(f"Xóa hoạt động: **{item['thoi_gian']}**?")
                                if st.button("Xác nhận", key=f"del_qt_db_{item['id']}", type="primary"):
                                    delete_qua_trinh_hoat_dong(item['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_qt",
            lambda x: f"**{x['thoi_gian']}**: {x['noi_dung']}",
            ""
        )

        st.markdown("##### ➕ Thêm quá trình hoạt động")

        col_qt_time, col_qt_content = st.columns([1, 2])
        with col_qt_time:
            c1, c2 = st.columns(2)
            with c1:
                qt_tu_nam = st.text_input("Từ năm", placeholder="2010", key="qt_tu_nam")
            with c2:
                qt_den_nam = st.text_input("Đến năm", placeholder="2015", key="qt_den_nam")
        with col_qt_content:
            qt_noi_dung = st.text_area(
                "Nội dung hoạt động", placeholder="Mô tả hoạt động...",
                height=100, key="qt_noi_dung"
            )

        qt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="qt_ghi_chu")

        if st.button("➕ Thêm vào danh sách", key="btn_add_qt", use_container_width=True):
            if qt_noi_dung:
                if qt_tu_nam and qt_den_nam:
                    qt_thoi_gian = f"{qt_tu_nam} - {qt_den_nam}"
                elif qt_tu_nam:
                    qt_thoi_gian = f"Từ {qt_tu_nam}"
                elif qt_den_nam:
                    qt_thoi_gian = f"Đến {qt_den_nam}"
                else:
                    qt_thoi_gian = "Không xác định"

                st.session_state.nl_staging_qt.append({
                    "thoi_gian": qt_thoi_gian,
                    "noi_dung": qt_noi_dung,
                    "ghi_chu": qt_ghi_chu,
                })
                st.toast("✅ Đã thêm quá trình vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập nội dung hoạt động!")

    # ==================================================================
    # TAB LIÊN HỆ & TÀI SẢN
    # ==================================================================
    with tab2:
        st.markdown("#### 📞 Thông tin liên hệ & Tài sản")

        cccd_now = st.session_state.get("nl_cccd", "")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📱 Số điện thoại / Mạng xã hội")

            # Dữ liệu đã có trong DB
            if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
                df_lh_db = get_lien_he_by_cccd(cccd_now)
                if not df_lh_db.empty:
                    with st.expander(f"📂 Đã có trong hệ thống ({len(df_lh_db)})", expanded=False):
                        for _, row in df_lh_db.iterrows():
                            col_i, col_d = st.columns([4, 1])
                            with col_i:
                                st.text(f"- {row['loai_lien_he']}: {row['gia_tri']}")
                            with col_d:
                                with st.popover("🗑️"):
                                    if st.button("Xóa", key=f"del_lh_db_{row['id']}", type="primary"):
                                        delete_lien_he(row['id'])
                                        st.rerun()

            # Preview staging
            _render_staging_list(
                "nl_staging_lien_he",
                lambda x: f"**{x['loai']}**: {x['gia_tri']}",
                ""
            )

            loai_lien_he = st.selectbox("Loại liên hệ", LOAI_LIEN_HE_OPTIONS, key="lh_loai")
            gia_tri_lien_he = st.text_input(
                "Giá trị", placeholder="0912345678 hoặc link FB/Zalo...", key="lien_he_value"
            )
            ghi_chu_lien_he = st.text_input("Ghi chú", key="lien_he_note", placeholder="Ghi chú thêm...")

            if st.button("➕ Thêm liên hệ", use_container_width=True, key="btn_add_lh"):
                if gia_tri_lien_he:
                    st.session_state.nl_staging_lien_he.append({
                        "loai": loai_lien_he,
                        "gia_tri": gia_tri_lien_he,
                        "ghi_chu": ghi_chu_lien_he,
                    })
                    st.toast(f"✅ Đã thêm {loai_lien_he}: {gia_tri_lien_he}", icon="📋")
                    st.rerun()
                else:
                    st.warning("⚠️ Vui lòng nhập giá trị liên hệ!")

        with col2:
            st.markdown("##### 🏦 Tài khoản ngân hàng")

            if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
                df_tc_db = get_tai_chinh_by_cccd(cccd_now)
                if not df_tc_db.empty:
                    with st.expander(f"📂 Đã có trong hệ thống ({len(df_tc_db)})", expanded=False):
                        for _, row in df_tc_db.iterrows():
                            col_i, col_d = st.columns([4, 1])
                            with col_i:
                                st.text(f"- {row['ngan_hang']}: {row['so_tai_khoan']}")
                            with col_d:
                                with st.popover("🗑️"):
                                    if st.button("Xóa", key=f"del_tc_db_{row['id']}", type="primary"):
                                        delete_tai_chinh(row['id'])
                                        st.rerun()

            # Preview staging
            _render_staging_list(
                "nl_staging_tai_chinh",
                lambda x: f"**{x['ngan_hang']}**: {x['so_tai_khoan']}",
                ""
            )

            ngan_hang = st.selectbox("Ngân hàng", DANH_SACH_NGAN_HANG, key="ngan_hang_tab2")
            so_tai_khoan = st.text_input("Số tài khoản", placeholder="1234567890", key="stk_tab2")
            chu_tai_khoan = st.text_input("Chủ tài khoản", placeholder="NGUYEN VAN A", key="ctk_tab2")

            if st.button("➕ Thêm tài khoản", use_container_width=True, key="btn_add_tc"):
                if so_tai_khoan:
                    st.session_state.nl_staging_tai_chinh.append({
                        "ngan_hang": ngan_hang,
                        "so_tai_khoan": so_tai_khoan,
                        "chu_tai_khoan": chu_tai_khoan,
                    })
                    st.toast(f"✅ Đã thêm TK {ngan_hang}: {so_tai_khoan}", icon="📋")
                    st.rerun()
                else:
                    st.warning("⚠️ Vui lòng nhập số tài khoản!")

        st.markdown("---")
        st.markdown("##### 🚗 Phương tiện giao thông")

        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_pt_db = get_phuong_tien_by_cccd(cccd_now)
            if not df_pt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_pt_db)})", expanded=False):
                    for _, row in df_pt_db.iterrows():
                        col_i, col_d = st.columns([4, 1])
                        with col_i:
                            st.text(f"- {row['loai_xe']}: {row['bien_kiem_soat']}")
                        with col_d:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_pt_db_{row['id']}", type="primary"):
                                    delete_phuong_tien(row['id'])
                                    st.rerun()

        # Preview staging
        _render_staging_list(
            "nl_staging_phuong_tien",
            lambda x: f"**{x['loai_xe']}**: {x['bien_so']} — {x['ten_xe']}",
            ""
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            loai_xe = st.selectbox("Loại xe", LOAI_XE_OPTIONS, key="loai_xe_tab2")
        with col2:
            bien_so = st.text_input("Biển kiểm soát", placeholder="19A-12345", key="bien_so_tab2")
        with col3:
            ten_xe = st.text_input("Tên xe", placeholder="Honda Vision...", key="ten_xe_tab2")

        if st.button("➕ Thêm phương tiện", use_container_width=True, key="btn_add_pt"):
            if bien_so:
                st.session_state.nl_staging_phuong_tien.append({
                    "loai_xe": loai_xe,
                    "bien_so": bien_so,
                    "ten_xe": ten_xe,
                })
                st.toast(f"✅ Đã thêm xe {loai_xe}: {bien_so}", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập biển kiểm soát!")

    # ==================================================================
    # TAB YẾU TỐ NƯỚC NGOÀI
    # ==================================================================
    with tab3:
        st.markdown("#### 🌐 Yếu tố nước ngoài & Nghiệp vụ")

        cccd_now = st.session_state.get("nl_cccd", "")

        # Hiển thị dữ liệu đã có
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_dt_db = get_ho_so_dac_thu_by_cccd(cccd_now)
            if not df_dt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_dt_db)} hồ sơ)", expanded=False):
                    for _, row in df_dt_db.iterrows():
                        loai_text = LOAI_HINH_DAC_THU.get(row['loai_hinh'], row['loai_hinh'])
                        col_i, col_d = st.columns([5, 1])
                        with col_i:
                            try:
                                nd = json.loads(row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                                preview = " | ".join([str(v) for v in list(nd.values())[:2] if v])
                            except Exception:
                                preview = ""
                            st.markdown(f"**📌 {loai_text}**: {preview}")
                        with col_d:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_dt_db_{row['id']}", type="primary"):
                                    delete_ho_so_dac_thu(row['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_dac_thu",
            lambda x: f"**📌 {LOAI_HINH_DAC_THU.get(x['loai_hinh'], x['loai_hinh'])}**",
            ""
        )

        loai_hinh = st.selectbox(
            "Loại hình hồ sơ đặc thù",
            options=list(LOAI_HINH_DAC_THU.keys()),
            format_func=lambda x: f"📌 {LOAI_HINH_DAC_THU[x]}",
            key="dt_loai_hinh"
        )

        st.markdown("---")

        noi_dung_dict = {}

        if loai_hinh == "Hon_Nhan_NN":
            st.markdown("##### 💑 Thông tin đối tác nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["ten_doi_tac"] = st.text_input("Họ tên đối tác", key="hn_ten")
                noi_dung_dict["quoc_tich"] = st.selectbox("Quốc tịch", DANH_SACH_QUOC_GIA, key="hn_qt")
            with col2:
                noi_dung_dict["so_ho_chieu"] = st.text_input("Số hộ chiếu", key="hn_hc")
                noi_dung_dict["tinh_trang"] = st.selectbox(
                    "Tình trạng",
                    ["Kết hôn hợp pháp", "Sinh sống như vợ chồng", "Đã ly hôn", "Đã qua đời"],
                    key="hn_tt"
                )

        elif loai_hinh == "Lam_Viec_NN":
            st.markdown("##### 🏢 Thông tin tổ chức nước ngoài")
            noi_dung_dict["ten_to_chuc"] = st.text_input("Tên tổ chức NGO/FDI", key="lv_tc")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["chuc_vu"] = st.text_input("Chức vụ", key="lv_cv")
            with col2:
                noi_dung_dict["thoi_gian"] = st.text_input("Thời gian làm việc", key="lv_tg")
            noi_dung_dict["dia_diem"] = st.text_input("Địa điểm làm việc", key="lv_dd")

        elif loai_hinh == "Hoc_Tap_Cong_Tac_NN":
            st.markdown("##### 🎓 Thông tin du học/công tác nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["dien_di"] = st.selectbox(
                    "Diện đi",
                    ["Du học tự túc", "Du học ngân sách", "Công tác", "Xuất khẩu lao động", "Khác"],
                    key="ht_dien"
                )
                noi_dung_dict["quoc_gia"] = st.selectbox("Quốc gia", DANH_SACH_QUOC_GIA, key="ht_qg")
            with col2:
                noi_dung_dict["thoi_gian_di"] = st.text_input("Thời gian đi", key="ht_tgd")
                noi_dung_dict["thoi_gian_ve"] = st.text_input("Thời gian về", key="ht_tgv")
            noi_dung_dict["nghe_sau_ve"] = st.text_input("Nghề nghiệp sau khi về", key="ht_nghe")

        elif loai_hinh == "Vi_Pham_NN":
            st.markdown("##### ⚠️ Vi phạm pháp luật ở nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["quoc_gia"] = st.selectbox("Quốc gia", DANH_SACH_QUOC_GIA, key="vp_qg")
                noi_dung_dict["co_quan_bat"] = st.text_input("Cơ quan bắt giữ", key="vp_cq")
            with col2:
                vp_ngay = st.date_input("Ngày vi phạm", value=None, format="DD/MM/YYYY", key="vp_tg")
                noi_dung_dict["thoi_gian"] = vp_ngay.strftime("%d/%m/%Y") if vp_ngay else ""
                noi_dung_dict["hinh_thuc_xu_ly"] = st.text_input("Hình thức xử lý", key="vp_ht")
            noi_dung_dict["noi_dung_vp"] = st.text_area("Nội dung vi phạm", key="vp_nd", height=100)

        elif loai_hinh == "Xac_Minh":
            st.markdown("##### 🔍 Thông tin xác minh")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["co_quan_xm"] = st.text_input("Cơ quan xác minh", key="xm_cq")
                xm_ngay = st.date_input("Ngày xác minh", value=None, format="DD/MM/YYYY", key="xm_tg")
                noi_dung_dict["thoi_gian"] = xm_ngay.strftime("%d/%m/%Y") if xm_ngay else ""
            with col2:
                noi_dung_dict["ket_qua"] = st.selectbox(
                    "Kết quả",
                    ["Đủ điều kiện", "Không đủ điều kiện", "Đang xác minh", "Khác"],
                    key="xm_kq"
                )
            noi_dung_dict["noi_dung_xm"] = st.text_area("Nội dung xác minh", key="xm_nd", height=100)

        ghi_chu_dac_thu = st.text_area(
            "Ghi chú thêm", placeholder="Ghi chú về hồ sơ đặc thù...", height=80, key="dt_ghi_chu"
        )

        if st.button("➕ Thêm hồ sơ đặc thù", use_container_width=True, key="btn_add_dt"):
            if any(noi_dung_dict.values()):
                st.session_state.nl_staging_dac_thu.append({
                    "loai_hinh": loai_hinh,
                    "noi_dung": noi_dung_dict.copy(),
                    "ghi_chu": ghi_chu_dac_thu,
                })
                st.toast(f"✅ Đã thêm {LOAI_HINH_DAC_THU[loai_hinh]} vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập ít nhất một thông tin!")

    # ==================================================================
    # TAB TÀI LIỆU ĐÍNH KÈM
    # ==================================================================
    with tab_tai_lieu:
        st.markdown("#### 📎 Tài liệu đính kèm")

        cccd_now = st.session_state.get("nl_cccd", "")

        # Hiển thị tài liệu đã có trong DB
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_tl_db = get_tai_lieu_by_cccd(cccd_now)
            if not df_tl_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_tl_db)} file)", expanded=False):
                    for _, row in df_tl_db.iterrows():
                        col_info, col_dl, col_del = st.columns([4, 1, 1])
                        with col_info:
                            kb = row['dung_luong'] / 1024
                            st.markdown(
                                f"**{row['loai_tai_lieu']}**: {row['ten_file_goc']} | "
                                f"📦 {kb:.1f} KB"
                            )
                        with col_dl:
                            fp, orig = get_file_path(row['id'])
                            if fp and fp.exists():
                                with open(fp, 'rb') as f:
                                    st.download_button("⬇️", data=f.read(), file_name=orig, key=f"dl_tl_{row['id']}")
                        with col_del:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_tl_db_{row['id']}", type="primary"):
                                    delete_tai_lieu(row['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        staged_files = st.session_state.get("nl_staging_tai_lieu", [])
        if staged_files:
            st.markdown(f"**📋 Danh sách file chờ upload ({len(staged_files)} file):**")
            for i, item in enumerate(staged_files):
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"↳ **{item['loai']}**: {item['file'].name} ({item['file'].size / 1024:.1f} KB)")
                with col_del:
                    if st.button("🗑️", key=f"del_tl_staging_{i}"):
                        st.session_state.nl_staging_tai_lieu.pop(i)
                        st.rerun()

        # Form upload mới
        st.markdown("##### ➕ Thêm tài liệu")
        st.caption(f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")

        uploaded_file = st.file_uploader(
            "Chọn file", type=ALLOWED_EXTENSIONS, key="upload_tai_lieu_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            loai_tai_lieu = st.selectbox("Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="tl_loai")
        with col2:
            mo_ta_tl = st.text_input("Mô tả (tùy chọn)", key="tl_mo_ta")

        if st.button("➕ Thêm vào danh sách", key="btn_add_tl", use_container_width=True):
            if uploaded_file:
                # Validate size
                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    st.error(f"❌ File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB")
                else:
                    st.session_state.nl_staging_tai_lieu.append({
                        "file": uploaded_file,
                        "loai": loai_tai_lieu,
                        "mo_ta": mo_ta_tl,
                    })
                    st.toast(f"✅ Đã thêm file: {uploaded_file.name}", icon="📋")
                    st.rerun()
            else:
                st.warning("⚠️ Vui lòng chọn file!")

    # ==================================================================
    # SECTION LƯU TOÀN BỘ HỒ SƠ (NGOÀI TABS)
    # ==================================================================
    st.markdown("---")
    st.markdown("### 💾 Lưu toàn bộ hồ sơ")

    # Tổng kết các mục chờ lưu
    cccd_val = st.session_state.get("nl_cccd", "")
    ho_ten_val = st.session_state.get("nl_ho_ten", "")
    them_bo_sung = st.session_state.get("nl_them_bo_sung", False)

    counts = {
        "Thân nhân": len(st.session_state.get("nl_staging_nhan_than", [])),
        "Quá trình": len(st.session_state.get("nl_staging_qt", [])),
        "Liên hệ": len(st.session_state.get("nl_staging_lien_he", [])),
        "Tài khoản NH": len(st.session_state.get("nl_staging_tai_chinh", [])),
        "Phương tiện": len(st.session_state.get("nl_staging_phuong_tien", [])),
        "Hồ sơ đặc thù": len(st.session_state.get("nl_staging_dac_thu", [])),
        "Tài liệu": len(st.session_state.get("nl_staging_tai_lieu", [])),
    }
    total_items = sum(counts.values())

    # Hiển thị tóm tắt
    summary_parts = [f"**{v}** {k}" for k, v in counts.items() if v > 0]
    if summary_parts or cccd_val:
        with st.container(border=True):
            st.markdown("**📊 Sẽ lưu:**")
            if not them_bo_sung:
                st.markdown(f"- 👤 Thông tin cá nhân: CCCD **{cccd_val or '—'}** | {ho_ten_val or '—'}")
            else:
                st.markdown(f"- 🔄 Bổ sung cho CCCD **{cccd_val}** (không ghi đè thông tin cá nhân)")
            if summary_parts:
                st.markdown("- " + " | ".join(summary_parts))
            else:
                st.caption("_(Chưa có dữ liệu vệ tinh nào được thêm)_")

    col_save, col_reset, _ = st.columns([2, 1, 3])

    with col_save:
        if st.button("✅ Lưu toàn bộ hồ sơ", type="primary", use_container_width=True, key="btn_save_all"):
            _do_save_all(
                cccd_val, ho_ten_val, them_bo_sung,
                st.session_state.get("main_ngay_sinh"),
                gioi_tinh if "gioi_tinh" in dir() else None,
                dia_chi_tinh if "dia_chi_tinh" in dir() else "Phú Thọ",
                dia_chi_xa if "dia_chi_xa" in dir() else "",
                phan_loai if "phan_loai" in dir() else "",
                chi_tiet_nghe if "chi_tiet_nghe" in dir() else "",
                ghi_chu if "ghi_chu" in dir() else "",
                avatar_file if "avatar_file" in dir() else None,
            )

    with col_reset:
        if st.button("🔄 Làm mới", use_container_width=True, key="btn_reset_all"):
            _reset_form()
            st.rerun()


# ===================================================================
# Batch save logic (tách ra để dễ test)
# ===================================================================
def _do_save_all(cccd, ho_ten, them_bo_sung,
                 ngay_sinh, gioi_tinh, dia_chi_tinh, dia_chi_xa,
                 phan_loai, chi_tiet_nghe, ghi_chu, avatar_file):
    """Thực hiện lưu toàn bộ hồ sơ. Gọi từ nút Lưu toàn bộ."""

    # --- Validate bắt buộc ---
    if not cccd or len(cccd) != 12:
        st.error("⚠️ Vui lòng nhập đúng 12 số CCCD (Tab 1)!")
        return
    if not cccd.isdigit():
        st.error("⚠️ CCCD chỉ gồm các chữ số!")
        return
    if not ho_ten:
        st.error("⚠️ Vui lòng nhập Họ tên (Tab 1)!")
        return

    errors = []
    saved_counts = {}

    # --- Lưu thông tin cá nhân chính ---
    if not them_bo_sung:
        if check_cccd_exists(cccd):
            st.error(f"⚠️ CCCD {cccd} đã tồn tại! Nếu muốn bổ sung, hãy refresh trang.")
            return

        data = {
            'cccd': cccd,
            'ho_ten': ho_ten,
            'ngay_sinh': ngay_sinh.strftime('%Y-%m-%d') if ngay_sinh else None,
            'gioi_tinh': gioi_tinh or '',
            'dia_chi_tinh': dia_chi_tinh or 'Phú Thọ',
            'dia_chi_xa': dia_chi_xa or '',
            'phan_loai_nghe_nghiep': phan_loai or '',
            'chi_tiet_nghe_nghiep': chi_tiet_nghe or '',
            'ghi_chu_chung': ghi_chu or '',
            'avatar_file': avatar_file,
        }
        ok, msg = save_doi_tuong(data)
        if not ok:
            st.error(f"❌ Lỗi lưu thông tin cá nhân: {msg}")
            return

    # Sau đây, CCCD chắc chắn tồn tại trong DB
    # --- Lưu thân nhân ---
    nt_list = st.session_state.get("nl_staging_nhan_than", [])
    nt_ok = 0
    for item in nt_list:
        if save_nhan_than(
            cccd=cccd,
            loai_quan_he=item["loai_quan_he"],
            ho_ten=item["ho_ten"],
            cccd_nhan_than=item.get("cccd_nhan_than", ""),
            ngay_sinh=item.get("ngay_sinh"),
            nghe_nghiep=item.get("nghe_nghiep", ""),
            noi_o=item.get("noi_o", ""),
            ghi_chu=item.get("ghi_chu", ""),
        ):
            nt_ok += 1
        else:
            errors.append(f"Lỗi lưu thân nhân: {item['ho_ten']}")
    if nt_ok:
        saved_counts["thân nhân"] = nt_ok

    # --- Lưu quá trình hoạt động ---
    qt_list = st.session_state.get("nl_staging_qt", [])
    qt_ok = 0
    for item in qt_list:
        try:
            save_qua_trinh_hoat_dong(cccd, item["thoi_gian"], item["noi_dung"], item.get("ghi_chu", ""))
            qt_ok += 1
        except Exception as e:
            errors.append(f"Lỗi lưu quá trình: {e}")
    if qt_ok:
        saved_counts["quá trình hoạt động"] = qt_ok

    # --- Lưu liên hệ ---
    lh_list = st.session_state.get("nl_staging_lien_he", [])
    lh_ok = 0
    for item in lh_list:
        if save_lien_he(cccd, item["loai"], item["gia_tri"], item.get("ghi_chu", "")):
            lh_ok += 1
        else:
            errors.append(f"Lỗi lưu liên hệ: {item['gia_tri']}")
    if lh_ok:
        saved_counts["liên hệ"] = lh_ok

    # --- Lưu tài chính ---
    tc_list = st.session_state.get("nl_staging_tai_chinh", [])
    tc_ok = 0
    for item in tc_list:
        if save_tai_chinh(cccd, item["ngan_hang"], item["so_tai_khoan"], item.get("chu_tai_khoan", "")):
            tc_ok += 1
        else:
            errors.append(f"Lỗi lưu tài khoản: {item['so_tai_khoan']}")
    if tc_ok:
        saved_counts["tài khoản NH"] = tc_ok

    # --- Lưu phương tiện ---
    pt_list = st.session_state.get("nl_staging_phuong_tien", [])
    pt_ok = 0
    for item in pt_list:
        if save_phuong_tien(cccd, item["loai_xe"], item["bien_so"], item.get("ten_xe", "")):
            pt_ok += 1
        else:
            errors.append(f"Lỗi lưu phương tiện: {item['bien_so']}")
    if pt_ok:
        saved_counts["phương tiện"] = pt_ok

    # --- Lưu hồ sơ đặc thù ---
    dt_list = st.session_state.get("nl_staging_dac_thu", [])
    dt_ok = 0
    for item in dt_list:
        if save_ho_so_dac_thu(cccd, item["loai_hinh"], item["noi_dung"], item.get("ghi_chu", "")):
            dt_ok += 1
        else:
            errors.append(f"Lỗi lưu hồ sơ đặc thù: {item['loai_hinh']}")
    if dt_ok:
        saved_counts["hồ sơ đặc thù"] = dt_ok

    # --- Lưu tài liệu ---
    tl_list = st.session_state.get("nl_staging_tai_lieu", [])
    tl_ok = 0
    for item in tl_list:
        ok, msg = save_tai_lieu(cccd, item["file"], item["loai"], item.get("mo_ta", ""))
        if ok:
            tl_ok += 1
        else:
            errors.append(f"Lỗi upload file {item['file'].name}: {msg}")
    if tl_ok:
        saved_counts["tài liệu"] = tl_ok

    # --- Kết quả ---
    if errors:
        for e in errors:
            st.warning(f"⚠️ {e}")

    if saved_counts or not them_bo_sung:
        summary_str = " | ".join([f"**{v}** {k}" for k, v in saved_counts.items()])
        action = "bổ sung" if them_bo_sung else "tạo mới"
        st.success(
            f"✅ Đã {action} hồ sơ **{ho_ten}** (CCCD: {cccd})"
            + (f"\n\n📊 {summary_str}" if summary_str else "")
        )
        st.session_state.current_cccd = cccd

        # Xóa staging sau khi lưu thành công
        for k in ["nl_staging_nhan_than", "nl_staging_qt", "nl_staging_lien_he",
                  "nl_staging_tai_chinh", "nl_staging_phuong_tien",
                  "nl_staging_dac_thu", "nl_staging_tai_lieu"]:
            st.session_state[k] = []

        if not errors:
            st.balloons()

```

## views/nhap_lieu/utils.py
```py
# -*- coding: utf-8 -*-
from services import check_cccd_exists
from constants import Messages

def validate_cccd_for_action(cccd: str, *required_fields) -> tuple[bool, str | None]:
    if not cccd:
        return False, Messages.MISSING_REQUIRED
    if not cccd.strip():
        return False, Messages.MISSING_REQUIRED
    for field in required_fields:
        if not field:
            return False, Messages.MISSING_REQUIRED
    if not check_cccd_exists(cccd):
        return False, Messages.CCCD_NOT_FOUND
    return True, None

```

## views/nhap_lieu/__init__.py
```py
from .ui import page_nhap_lieu

__all__ = ['page_nhap_lieu']

```

## views/profile/actions.py
```py
# -*- coding: utf-8 -*-
import logging
import shutil
from pathlib import Path
from database import get_connection

logger = logging.getLogger(__name__)

def delete_nhan_than(nhan_than_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nhan_than WHERE id = ?", (nhan_than_id,))
    conn.commit()
    conn.close()
    return True


def delete_lien_he(lien_he_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lien_he WHERE id = ?", (lien_he_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa liên hệ: {e}")
        return False
    finally:
        conn.close()


def delete_tai_chinh(tai_chinh_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tai_chinh WHERE id = ?", (tai_chinh_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa tài chính: {e}")
        return False
    finally:
        conn.close()


def delete_phuong_tien(phuong_tien_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phuong_tien WHERE id = ?",
                       (phuong_tien_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa phương tiện: {e}")
        return False
    finally:
        conn.close()


def delete_ho_so_dac_thu(ho_so_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ho_so_dac_thu WHERE id = ?", (ho_so_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa hồ sơ đặc thù: {e}")
        return False
    finally:
        conn.close()


def delete_tai_lieu(tai_lieu_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT duong_dan FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()

    if result:
        duong_dan = result[0]
        file_path = Path.cwd() / duong_dan
        if file_path.exists():
            file_path.unlink()

        cursor.execute("DELETE FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        conn.commit()

    conn.close()
    return True


def delete_doi_tuong(cccd):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doi_tuong WHERE cccd = ?", (cccd,))
        conn.commit()

        upload_folder = Path.cwd() / "uploads" / cccd
        if upload_folder.exists():
            shutil.rmtree(upload_folder)

        return True, "Đã xóa thành công!"
    except Exception as e:
        logger.exception(f"Lỗi xóa đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def update_doi_tuong(cccd, data):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE doi_tuong 
            SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, dia_chi_tinh = ?,
                dia_chi_xa = ?, phan_loai_nghe_nghiep = ?, chi_tiet_nghe_nghiep = ?,
                ghi_chu_chung = ?, anh_chan_dung = ?, updated_at = CURRENT_TIMESTAMP
            WHERE cccd = ?
        """, (
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung'],
            data.get('anh_chan_dung'),
            cccd
        ))
        conn.commit()
        return True, "Cập nhật thành công!"
    except Exception as e:
        logger.exception(f"Lỗi cập nhật đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()

```

## views/profile/getters.py
```py
# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
from database import get_connection

def get_doi_tuong_detail(cccd):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (cccd,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_nhan_than_by_cccd(cccd):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM nhan_than WHERE cccd = ?", conn, params=(cccd,))
    conn.close()
    return df


def get_lien_he_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_chinh_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_phuong_tien_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_ho_so_dac_thu_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_lieu_by_cccd(cccd):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
    conn.close()
    return df


def get_file_path(tai_lieu_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        # Resolve path relative to project root assuming app runs from root
        file_path = Path.cwd() / result[0]
        return file_path, result[1]
    return None, None

```

## views/profile/ui.py
```py
# -*- coding: utf-8 -*-
import streamlit as st
import json
import logging
from pathlib import Path
from datetime import datetime, date

from database import (
    get_connection, get_qua_trinh_hoat_dong,
    save_qua_trinh_hoat_dong, delete_qua_trinh_hoat_dong
)
from constants import (
    GIOI_TINH_OPTIONS, TINH_OPTIONS, PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
    LOAI_HINH_DAC_THU, LOAI_LIEN_HE_OPTIONS, DANH_SACH_NGAN_HANG,
    LOAI_XE_OPTIONS, DANH_SACH_QUOC_GIA, ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB, LOAI_TAI_LIEU_OPTIONS, KET_QUA_XAC_MINH,
    HINH_THUC_DU_HOC
)
from services import (
    save_nhan_than, save_lien_he, save_tai_chinh,
    save_phuong_tien, save_ho_so_dac_thu, save_tai_lieu,
    get_upload_folder
)
from .getters import (
    get_doi_tuong_detail, get_nhan_than_by_cccd, get_lien_he_by_cccd,
    get_tai_chinh_by_cccd, get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd, get_tai_lieu_by_cccd, get_file_path
)
from .actions import (
    delete_nhan_than, delete_lien_he, delete_tai_chinh,
    delete_phuong_tien, delete_ho_so_dac_thu, delete_tai_lieu,
    delete_doi_tuong, update_doi_tuong
)

logger = logging.getLogger(__name__)

CSXH_FIELD_LABELS = {
    'ten_doi_tac': 'Tên đối tác',
    'quoc_tich': 'Quốc tịch',
    'so_ho_chieu': 'Số hộ chiếu',
    'tinh_trang': 'Tình trạng',
    'ten_to_chuc': 'Tên tổ chức',
    'chuc_vu': 'Chức vụ',
    'thoi_gian': 'Thời gian',
    'dia_diem': 'Địa điểm',
    'dien_di': 'Diện đi',
    'quoc_gia': 'Quốc gia',
    'thoi_gian_di': 'Thời gian đi',
    'thoi_gian_ve': 'Thời gian về',
    'nghe_sau_ve': 'Nghề sau khi về',
    'co_quan_bat': 'Cơ quan bắt giữ',
    'hinh_thuc_xu_ly': 'Hình thức xử lý',
    'noi_dung_vp': 'Nội dung vi phạm',
    'co_quan_xm': 'Cơ quan xác minh',
    'ket_qua': 'Kết quả',
    'noi_dung_xm': 'Nội dung xác minh',
}

def page_profile_view(cccd):
    """Trang xem chi tiết hồ sơ đối tượng 360 độ"""
    # Lấy thông tin đối tượng
    doi_tuong = get_doi_tuong_detail(cccd)

    if not doi_tuong:
        st.error(f"❌ Không tìm thấy đối tượng với CCCD: {cccd}")
        if st.button("🔙 Quay lại Tra cứu"):
            st.session_state.view_profile_cccd = None
            st.rerun()
        return

    # Header với thông tin cơ bản
    st.markdown("# 👤 Hồ sơ Chi tiết")

    col_header1, col_header2, col_header3 = st.columns([1, 2, 1])

    with col_header1:
        # Avatar display logic
        avatar_path = doi_tuong.get('anh_chan_dung')
        has_avatar = False
        if avatar_path:
            # Check if file exists
            try:
                # Assuming path is relative to cwd
                full_avatar_path = Path.cwd() / avatar_path
                if full_avatar_path.exists():
                    st.image(str(full_avatar_path), width=150)
                    has_avatar = True
            except Exception:
                pass

        if not has_avatar:
            # Avatar placeholder
            st.markdown("""
            <div style="width: 120px; height: 120px; background: linear-gradient(135deg, #667eea, #764ba2); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        font-size: 48px; color: white; margin: 0 auto;">
                👤
            </div>
            """, unsafe_allow_html=True)

        # Quick avatar change expander
        with st.expander("📷 Thay ảnh đại diện", expanded=False):
            new_avatar_quick = st.file_uploader(
                "Chọn ảnh mới",
                type=['png', 'jpg', 'jpeg'],
                key="quick_avatar_uploader",
                label_visibility="collapsed"
            )
            if new_avatar_quick:
                if st.button("💾 Lưu ảnh", type="primary", use_container_width=True, key="save_quick_avatar"):
                    try:
                        import time
                        # Create user upload dir if not exists
                        upload_dir = get_upload_folder(cccd)
                        # Generate safe filename
                        file_ext = new_avatar_quick.name.split('.')[-1].lower()
                        safe_name = f"avatar_{int(time.time())}.{file_ext}"
                        save_path = upload_dir / safe_name

                        # Save file
                        with open(save_path, "wb") as f:
                            f.write(new_avatar_quick.getbuffer())

                        # Update database
                        new_avatar_path = f"uploads/{cccd}/{safe_name}"
                        conn = get_connection()
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE doi_tuong SET anh_chan_dung = ?, updated_at = CURRENT_TIMESTAMP WHERE cccd = ?",
                                (new_avatar_path, cccd)
                            )
                            conn.commit()
                            st.success("✅ Đã cập nhật ảnh đại diện!")
                            st.rerun()
                        finally:
                            conn.close()
                    except Exception as e:
                        logger.error(f"Error saving quick avatar: {e}")
                        st.error("❌ Lỗi khi lưu ảnh!")

    with col_header2:
        st.markdown(f"## {doi_tuong.get('ho_ten', 'N/A')}")
        st.markdown(f"**CCCD:** {cccd}")

        # Tính tuổi
        if doi_tuong.get('ngay_sinh'):
            try:
                ngay_sinh = datetime.strptime(
                    str(doi_tuong['ngay_sinh']), '%Y-%m-%d')
                tuoi = (datetime.now() - ngay_sinh).days // 365
                st.markdown(
                    f"**Ngày sinh:** {ngay_sinh.strftime('%d/%m/%Y')} ({tuoi} tuổi)")
            except (ValueError, TypeError):
                st.markdown(
                    f"**Ngày sinh:** {doi_tuong.get('ngay_sinh', 'N/A')}")

        st.markdown(f"**Giới tính:** {doi_tuong.get('gioi_tinh', 'N/A')}")

    with col_header3:
        # Action buttons
        if st.button("🔙 Quay lại", use_container_width=True):
            st.session_state.view_profile_cccd = None
            st.session_state.edit_mode = False
            st.rerun()

        if st.button("✏️ Sửa hồ sơ", type="primary", use_container_width=True):
            st.session_state.edit_mode = True
            st.rerun()

        if st.button("🗑️ Xóa hồ sơ", type="secondary", use_container_width=True):
            st.session_state.confirm_delete = True

    # Xác nhận xóa
    if st.session_state.get('confirm_delete'):
        st.warning(
            f"⚠️ Bạn có chắc muốn xóa hồ sơ **{doi_tuong.get('ho_ten')}** không? Hành động này không thể hoàn tác!")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("✅ Xác nhận xóa", type="primary"):
                success, msg = delete_doi_tuong(cccd)
                if success:
                    st.success(msg)
                    st.session_state.view_profile_cccd = None
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.error(msg)
        with col_del2:
            if st.button("❌ Hủy"):
                st.session_state.confirm_delete = False
                st.rerun()

    st.markdown("---")

    # Tabs chi tiết
    tab1, tab_nt, tab_qt, tab2, tab3, tab_tl = st.tabs([
        "📋 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
        "⏳ Quá trình hoạt động",
        "📞 Liên hệ & Tài sản",
        "🌐 Yếu tố CSXH",
        "📎 Tài liệu"
    ])

    with tab1:
        st.markdown("#### 📋 Thông tin cá nhân")

        # Chế độ chỉnh sửa
        if st.session_state.get('edit_mode'):
            st.info("📝 **Chế độ chỉnh sửa** - Thay đổi thông tin và nhấn Lưu")

            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    # Avatar Upload
                    st.markdown("##### 📸 Ảnh đại diện")
                    new_avatar = st.file_uploader("Tải lên ảnh mới", type=[
                                                  'png', 'jpg', 'jpeg'], key="edit_avatar_uploader")

                    edit_ho_ten = st.text_input(
                        "Họ và tên *",
                        value=doi_tuong.get('ho_ten', ''),
                        key="edit_ho_ten"
                    )

                    # Ngày sinh
                    current_ngay_sinh = doi_tuong.get('ngay_sinh')
                    ns_value = None
                    if current_ngay_sinh:
                        try:
                            ns_value = datetime.strptime(
                                str(current_ngay_sinh), '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            pass

                    edit_ngay_sinh_obj = st.date_input(
                        "Ngày sinh",
                        value=ns_value,
                        min_value=date(1900, 1, 1),
                        max_value=datetime.now().date(),
                        format="DD/MM/YYYY",
                        key="edit_ngay_sinh_picker"
                    )

                    edit_gioi_tinh = st.selectbox(
                        "Giới tính",
                        GIOI_TINH_OPTIONS,
                        index=GIOI_TINH_OPTIONS.index(doi_tuong.get('gioi_tinh', 'Nam')) if doi_tuong.get(
                            'gioi_tinh') in GIOI_TINH_OPTIONS else 0,
                        key="edit_gioi_tinh"
                    )

                with col2:
                    edit_dia_chi_tinh = st.selectbox(
                        "Tỉnh/TP",
                        TINH_OPTIONS,
                        index=TINH_OPTIONS.index(doi_tuong.get('dia_chi_tinh', 'Phú Thọ')) if doi_tuong.get(
                            'dia_chi_tinh') in TINH_OPTIONS else 0,
                        key="edit_dia_chi_tinh"
                    )

                    edit_dia_chi_xa = st.text_input(
                        "Xã/Phường",
                        value=doi_tuong.get('dia_chi_xa', ''),
                        key="edit_dia_chi_xa"
                    )

                    edit_phan_loai = st.selectbox(
                        "Phân loại nghề nghiệp",
                        PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
                        index=PHAN_LOAI_NGHE_NGHIEP_OPTIONS.index(doi_tuong.get('phan_loai_nghe_nghiep', 'Lao động tự do')) if doi_tuong.get(
                            'phan_loai_nghe_nghiep') in PHAN_LOAI_NGHE_NGHIEP_OPTIONS else 0,
                        key="edit_phan_loai"
                    )

                    edit_chi_tiet_nghe = st.text_input(
                        "Chi tiết nơi làm việc",
                        value=doi_tuong.get('chi_tiet_nghe_nghiep', ''),
                        key="edit_chi_tiet_nghe"
                    )

                edit_ghi_chu = st.text_area(
                    "Ghi chú chung",
                    value=doi_tuong.get('ghi_chu_chung', ''),
                    height=100,
                    key="edit_ghi_chu"
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button(
                        "💾 Lưu thay đổi", type="primary", use_container_width=True)
                with col_btn2:
                    cancel = st.form_submit_button(
                        "❌ Hủy", use_container_width=True)

                if submitted:
                    # Validate
                    if not edit_ho_ten:
                        st.error("⚠️ Vui lòng nhập họ tên!")
                    else:
                        # Parse ngày sinh
                        edit_ngay_sinh = edit_ngay_sinh_obj.strftime(
                            '%Y-%m-%d') if edit_ngay_sinh_obj else None

                        # Handle Avatar Upload
                        current_avatar_path = doi_tuong.get('anh_chan_dung')
                        if new_avatar:
                            try:
                                # Create user upload dir if not exists
                                upload_dir = get_upload_folder(cccd)
                                # Generate safe filename
                                import time
                                file_ext = new_avatar.name.split('.')[-1]
                                # Clean filename
                                safe_name = f"avatar_{int(time.time())}.{file_ext}"
                                save_path = upload_dir / safe_name

                                # Save file
                                with open(save_path, "wb") as f:
                                    f.write(new_avatar.getbuffer())

                                # Update path (relative)
                                current_avatar_path = f"uploads/{cccd}/{safe_name}"
                            except Exception as e:
                                logger.error(f"Error saving avatar: {e}")
                                st.error("❌ Lỗi khi lưu ảnh đại diện!")

                        update_data = {
                            'ho_ten': edit_ho_ten,
                            'ngay_sinh': edit_ngay_sinh,
                            'gioi_tinh': edit_gioi_tinh,
                            'dia_chi_tinh': edit_dia_chi_tinh,
                            'dia_chi_xa': edit_dia_chi_xa,
                            'phan_loai_nghe_nghiep': edit_phan_loai,
                            'chi_tiet_nghe_nghiep': edit_chi_tiet_nghe,
                            'ghi_chu_chung': edit_ghi_chu,
                            'anh_chan_dung': current_avatar_path
                        }

                        success, msg = update_doi_tuong(cccd, update_data)
                        if success:
                            st.success(msg)
                            st.session_state.edit_mode = False
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {msg}")

                if cancel:
                    st.session_state.edit_mode = False
                    st.rerun()
        else:
            # Chế độ xem
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"**Địa chỉ:** {doi_tuong.get('dia_chi_xa', '')} - {doi_tuong.get('dia_chi_tinh', '')}")
                st.markdown(
                    f"**Phân loại nghề nghiệp:** {doi_tuong.get('phan_loai_nghe_nghiep', 'N/A')}")

            with col2:
                st.markdown(
                    f"**Chi tiết nơi làm việc:** {doi_tuong.get('chi_tiet_nghe_nghiep', 'N/A')}")
                st.markdown(
                    f"**Ngày tạo:** {doi_tuong.get('created_at', 'N/A')}")

            if doi_tuong.get('ghi_chu_chung'):
                st.markdown("**Ghi chú:**")
                st.info(doi_tuong.get('ghi_chu_chung'))

    # ===== TAB THÂN NHÂN =====
    with tab_nt:
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin thân nhân")

        # Hiển thị danh sách thân nhân với nút xóa
        df_nhan_than = get_nhan_than_by_cccd(cccd)
        if not df_nhan_than.empty:
            st.markdown("##### 📋 Danh sách thân nhân")

            for idx, row in df_nhan_than.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"""
                    **{row['loai_quan_he']}**: {row['ho_ten']} | 
                    📅 {row['ngay_sinh'] if row['ngay_sinh'] else 'N/A'} | 
                    💼 {row['nghe_nghiep'] if row['nghe_nghiep'] else 'N/A'} | 
                    📍 {row['noi_o'] if row['noi_o'] else 'N/A'}
                    """)
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['ho_ten']}"):
                        st.markdown(f"Xóa **{row['ho_ten']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_nt_{row['id']}", type="primary"):
                            delete_nhan_than(row['id'])
                            st.toast(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}", icon="✅")
                            st.rerun()
            st.markdown("---")
        else:
            st.info(
                "💡 Chưa có thông tin thân nhân. Nhấn **➕ Thêm thân nhân mới** để thêm.")

        # Form thêm thân nhân mới
        with st.expander("➕ Thêm thân nhân mới", expanded=False):
            with st.form("add_nhan_than_profile_form"):
                nt_loai_quan_he = st.selectbox(
                    "Loại quan hệ",
                    ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ",
                        "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
                    key="pv_nt_loai"
                )

                col1, col2 = st.columns(2)
                with col1:
                    nt_ho_ten = st.text_input(
                        "Họ và tên *", key="pv_nt_ho_ten")
                    nt_cccd_nt = st.text_input(
                        "Số CCCD (nếu có)", key="pv_nt_cccd")
                    nt_ngay_sinh = st.date_input("Ngày sinh", value=None, key="pv_nt_ngay_sinh",
                                                 format="DD/MM/YYYY", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
                with col2:
                    nt_phan_loai_nghe = st.selectbox(
                        "Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="pv_nt_phan_loai")
                    nt_nghe_nghiep = st.text_input(
                        "Chi tiết nghề nghiệp", placeholder="Ví dụ: Giáo viên THPT, Nông dân...", key="pv_nt_nghe")
                    nt_noi_o = st.text_input(
                        "Nơi ở hiện nay", key="pv_nt_noi_o")

                nt_ghi_chu = st.text_input("Ghi chú", key="pv_nt_ghi_chu")

                if st.form_submit_button("💾 Lưu thân nhân", type="primary"):
                    if nt_ho_ten:
                        # Kết hợp phân loại và chi tiết nghề nghiệp
                        nghe_nghiep_full = f"{nt_phan_loai_nghe}: {nt_nghe_nghiep}" if nt_nghe_nghiep else nt_phan_loai_nghe
                        save_nhan_than(
                            cccd=cccd,
                            loai_quan_he=nt_loai_quan_he,
                            ho_ten=nt_ho_ten,
                            cccd_nhan_than=nt_cccd_nt,
                            ngay_sinh=nt_ngay_sinh.strftime(
                                '%Y-%m-%d') if nt_ngay_sinh else None,
                            nghe_nghiep=nghe_nghiep_full,
                            noi_o=nt_noi_o,
                            ghi_chu=nt_ghi_chu
                        )
                        st.success(f"✅ Đã thêm {nt_loai_quan_he}: {nt_ho_ten}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập họ tên!")

    # ===== TAB QUÁ TRÌNH HOẠT ĐỘNG =====
    with tab_qt:
        st.markdown("#### ⏳ Quá trình hoạt động & Lịch sử nhân thân")

        qt_list = get_qua_trinh_hoat_dong(cccd)

        if qt_list:
            # Hiển thị dạng Timeline đơn giản
            for item in qt_list:
                with st.container():
                    col_time, col_content, col_del = st.columns([1.5, 4, 0.5])
                    with col_time:
                        st.markdown(f"**{item['thoi_gian']}**")
                    with col_content:
                        st.markdown(item['noi_dung'])
                        if item['ghi_chu']:
                            st.caption(f"📝 {item['ghi_chu']}")
                    with col_del:
                        with st.popover("🗑️", help="Xóa mục này"):
                            st.markdown("Xóa quá trình này?")
                            if st.button("Xác nhận", key=f"confirm_del_qt_pv_{item['id']}", type="primary"):
                                if delete_qua_trinh_hoat_dong(item['id']):
                                    st.toast("✅ Đã xóa quá trình hoạt động", icon="✅")
                                    st.rerun()
                    st.divider()
        else:
            st.info("💡 Chưa có thông tin quá trình hoạt động")

        # Form thêm mới activity
        with st.expander("➕ Thêm hoạt động mới", expanded=False):
            with st.form("add_activity_profile_form"):
                col_qt_time, col_qt_content = st.columns([1, 3])
                with col_qt_time:
                    c1, c2 = st.columns(2)
                    with c1:
                        pv_qt_tu = st.text_input("Từ năm", key="pv_qt_tu")
                    with c2:
                        pv_qt_den = st.text_input("Đến năm", key="pv_qt_den")
                with col_qt_content:
                    qt_noi_dung = st.text_area(
                        "Nội dung", placeholder="Mô tả công việc, nơi ở...", key="pv_qt_nd")

                qt_ghi_chu = st.text_input("Ghi chú", key="pv_qt_gc")

                if st.form_submit_button("💾 Lưu hoạt động", type="primary"):
                    if qt_noi_dung:
                        # Combine time
                        if pv_qt_tu and pv_qt_den:
                            qt_thoi_gian = f"{pv_qt_tu} - {pv_qt_den}"
                        elif pv_qt_tu:
                            qt_thoi_gian = f"Từ {pv_qt_tu}"
                        elif pv_qt_den:
                            qt_thoi_gian = f"Đến {pv_qt_den}"
                        else:
                            qt_thoi_gian = ""

                        save_qua_trinh_hoat_dong(
                            cccd, qt_thoi_gian, qt_noi_dung, qt_ghi_chu)
                        st.success("✅ Đã thêm hoạt động!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập nội dung!")

    with tab2:
        st.markdown("#### 📞 Liên hệ & Tài sản")

        # ========== LIÊN HỆ ==========
        st.markdown("##### 📱 Thông tin liên hệ")
        df_lien_he = get_lien_he_by_cccd(cccd)
        if not df_lien_he.empty:
            for idx, row in df_lien_he.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['loai_lien_he']}**: {row['gia_tri']}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['loai_lien_he']}"):
                        st.markdown(f"Xóa **{row['loai_lien_he']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_lh_{row['id']}", type="primary"):
                            if delete_lien_he(row['id']):
                                st.toast("✅ Đã xóa liên hệ!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin liên hệ")

        # Form thêm liên hệ
        with st.expander("➕ Thêm liên hệ mới", expanded=False):
            with st.form("add_lien_he_form"):
                col1, col2 = st.columns(2)
                with col1:
                    lh_loai = st.selectbox(
                        "Loại liên hệ", LOAI_LIEN_HE_OPTIONS, key="add_lh_loai")
                    lh_gia_tri = st.text_input(
                        "Giá trị (SĐT/Email/Link...)", key="add_lh_gia_tri")
                with col2:
                    lh_ghi_chu = st.text_input("Ghi chú", key="add_lh_ghi_chu")

                if st.form_submit_button("💾 Lưu liên hệ", type="primary"):
                    if lh_gia_tri:
                        save_lien_he(cccd, lh_loai, lh_gia_tri, lh_ghi_chu)
                        st.success("✅ Đã thêm liên hệ!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập giá trị!")

        st.markdown("---")

        # ========== TÀI KHOẢN NGÂN HÀNG ==========
        st.markdown("##### 🏦 Tài khoản ngân hàng")
        df_tai_chinh = get_tai_chinh_by_cccd(cccd)
        if not df_tai_chinh.empty:
            for idx, row in df_tai_chinh.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    chu_tk = f" - {row['chu_tai_khoan']}" if row['chu_tai_khoan'] else ""
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['ngan_hang']}**: {row['so_tai_khoan']}{chu_tk}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa TK {row['ngan_hang']}"):
                        st.markdown(f"Xóa TK **{row['ngan_hang']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_tc_{row['id']}", type="primary"):
                            if delete_tai_chinh(row['id']):
                                st.toast("✅ Đã xóa tài khoản!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin tài khoản ngân hàng")

        # Form thêm tài khoản
        with st.expander("➕ Thêm tài khoản ngân hàng", expanded=False):
            with st.form("add_tai_chinh_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tc_ngan_hang = st.selectbox(
                        "Ngân hàng", DANH_SACH_NGAN_HANG, key="add_tc_ngan_hang")
                    tc_so_tk = st.text_input(
                        "Số tài khoản", key="add_tc_so_tk")
                with col2:
                    tc_chu_tk = st.text_input(
                        "Chủ tài khoản", key="add_tc_chu_tk")
                    tc_ghi_chu = st.text_input("Ghi chú", key="add_tc_ghi_chu")

                if st.form_submit_button("💾 Lưu tài khoản", type="primary"):
                    if tc_so_tk:
                        save_tai_chinh(cccd, tc_ngan_hang,
                                       tc_so_tk, tc_chu_tk, tc_ghi_chu)
                        st.success("✅ Đã thêm tài khoản!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập số tài khoản!")

        st.markdown("---")

        # ========== PHƯƠNG TIỆN ==========
        st.markdown("##### 🚗 Phương tiện")
        df_phuong_tien = get_phuong_tien_by_cccd(cccd)
        if not df_phuong_tien.empty:
            for idx, row in df_phuong_tien.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    ten_xe = f" - {row['ten_phuong_tien']}" if row['ten_phuong_tien'] else ""
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['loai_xe']}**: {row['bien_kiem_soat']}{ten_xe}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['bien_kiem_soat']}"):
                        st.markdown(f"Xóa xe **{row['bien_kiem_soat']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_pt_{row['id']}", type="primary"):
                            if delete_phuong_tien(row['id']):
                                st.toast("✅ Đã xóa phương tiện!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin phương tiện")

        # Form thêm phương tiện
        with st.expander("➕ Thêm phương tiện", expanded=False):
            with st.form("add_phuong_tien_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pt_loai = st.selectbox(
                        "Loại xe", LOAI_XE_OPTIONS, key="add_pt_loai")
                    pt_bien_so = st.text_input(
                        "Biển kiểm soát", key="add_pt_bien_so")
                with col2:
                    pt_ten = st.text_input("Tên phương tiện", key="add_pt_ten")
                    pt_ghi_chu = st.text_input("Ghi chú", key="add_pt_ghi_chu")

                if st.form_submit_button("💾 Lưu phương tiện", type="primary"):
                    if pt_bien_so:
                        save_phuong_tien(
                            cccd, pt_loai, pt_bien_so, pt_ten, pt_ghi_chu)
                        st.success("✅ Đã thêm phương tiện!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập biển kiểm soát!")

    with tab3:
        st.markdown("#### 🌐 Yếu tố CSXH (Đặc thù)")

        df_dac_thu = get_ho_so_dac_thu_by_cccd(cccd)

        if not df_dac_thu.empty:
            for idx, row in df_dac_thu.iterrows():
                loai_hinh = row['loai_hinh']
                loai_hinh_text = LOAI_HINH_DAC_THU.get(loai_hinh, loai_hinh)

                with st.expander(f"📌 {loai_hinh_text}", expanded=True):
                    # Parse JSON nội dung chi tiết
                    try:
                        noi_dung = json.loads(
                            row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                    except (json.JSONDecodeError, TypeError):
                        noi_dung = {}

                    col1, col2 = st.columns(2)
                    items = list(noi_dung.items())
                    mid = len(items) // 2 + len(items) % 2

                    with col1:
                        for key, value in items[:mid]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(
                                    key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")

                    with col2:
                        for key, value in items[mid:]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(
                                    key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")

                    if row.get('ghi_chu'):
                        st.markdown(f"**Ghi chú:** {row['ghi_chu']}")

                    col_date, col_del = st.columns([4, 1])
                    with col_date:
                        st.caption(
                            f"📅 Ngày tạo: {row.get('created_at', 'N/A')}")
                    with col_del:
                        with st.popover("🗑️ Xóa", help=f"Xóa hồ sơ {loai_hinh_text}"):
                            st.markdown(f"Xóa hồ sơ **{loai_hinh_text}**?")
                            if st.button("Xác nhận", key=f"confirm_del_csxh_{row['id']}", type="primary"):
                                if delete_ho_so_dac_thu(row['id']):
                                    st.toast(f"✅ Đã xóa: {loai_hinh_text}", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("❌ Lỗi khi xóa hồ sơ!")
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào")

        # Form thêm hồ sơ đặc thù mới - Dynamic fields based on type
        st.markdown("---")
        with st.expander("➕ Thêm hồ sơ đặc thù mới", expanded=False):
            # Chọn loại hình trước (ngoài form để có thể reactive)
            csxh_loai = st.selectbox(
                "Loại hình CSXH",
                list(LOAI_HINH_DAC_THU.keys()),
                format_func=lambda x: LOAI_HINH_DAC_THU.get(x, x),
                key="pv_csxh_loai_select"
            )

            with st.form("add_csxh_profile_form"):
                st.markdown("**Nội dung chi tiết:**")

                noi_dung = {}

                # Dynamic fields based on csxh_loai
                if csxh_loai == "Hon_Nhan_NN":
                    st.markdown("##### 💑 Thông tin đối tác nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["ten_doi_tac"] = st.text_input(
                            "Họ tên đối tác", key="csxh_hn_ten")
                        noi_dung["quoc_tich"] = st.selectbox(
                            "Quốc tịch", DANH_SACH_QUOC_GIA, key="csxh_hn_qt")
                    with col2:
                        noi_dung["so_ho_chieu"] = st.text_input(
                            "Số hộ chiếu", key="csxh_hn_hc")
                        noi_dung["tinh_trang"] = st.selectbox(
                            "Tình trạng",
                            ["Kết hôn hợp pháp", "Sinh sống như vợ chồng",
                                "Đã ly hôn", "Đã qua đời"],
                            key="csxh_hn_tt"
                        )

                elif csxh_loai == "Lam_Viec_NN":
                    st.markdown("##### 🏢 Thông tin tổ chức nước ngoài")
                    noi_dung["ten_to_chuc"] = st.text_input(
                        "Tên tổ chức NGO/FDI", key="csxh_lv_tc")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["chuc_vu"] = st.text_input(
                            "Chức vụ", key="csxh_lv_cv")
                    with col2:
                        noi_dung["thoi_gian"] = st.text_input(
                            "Thời gian làm việc", key="csxh_lv_tg")
                    noi_dung["dia_diem"] = st.text_input(
                        "Địa điểm làm việc", key="csxh_lv_dd")

                elif csxh_loai == "Hoc_Tap_Cong_Tac_NN":
                    st.markdown("##### 🎓 Thông tin du học/công tác nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["dien_di"] = st.selectbox(
                            "Diện đi",
                            ["Du học tự túc", "Du học ngân sách",
                                "Công tác", "Xuất khẩu lao động", "Khác"],
                            key="csxh_ht_dien"
                        )
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_ht_qg")
                    with col2:
                        noi_dung["thoi_gian_di"] = st.text_input(
                            "Thời gian đi", key="csxh_ht_tgd")
                        noi_dung["thoi_gian_ve"] = st.text_input(
                            "Thời gian về", key="csxh_ht_tgv")
                    noi_dung["nghe_sau_ve"] = st.text_input(
                        "Nghề nghiệp sau khi về", key="csxh_ht_nghe")

                elif csxh_loai == "Vi_Pham_NN":
                    st.markdown(
                        "##### ⚠️ Thông tin vi phạm pháp luật ở nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_vp_qg")
                        noi_dung["co_quan_bat"] = st.text_input(
                            "Cơ quan bắt giữ", key="csxh_vp_cq")
                    with col2:
                        vp_ngay = st.date_input(
                            "Ngày vi phạm", value=None, format="DD/MM/YYYY", key="csxh_vp_tg")
                        noi_dung["thoi_gian"] = vp_ngay.strftime(
                            "%d/%m/%Y") if vp_ngay else ""
                        noi_dung["hinh_thuc_xu_ly"] = st.text_input(
                            "Hình thức xử lý", key="csxh_vp_ht")
                    noi_dung["noi_dung_vp"] = st.text_area(
                        "Nội dung vi phạm", key="csxh_vp_nd", height=100)

                elif csxh_loai == "Xac_Minh":
                    st.markdown("##### 🔍 Thông tin xác minh")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["co_quan_xm"] = st.text_input(
                            "Cơ quan xác minh", key="csxh_xm_cq")
                        xm_ngay = st.date_input(
                            "Ngày xác minh", value=None, format="DD/MM/YYYY", key="csxh_xm_tg")
                        noi_dung["thoi_gian"] = xm_ngay.strftime(
                            "%d/%m/%Y") if xm_ngay else ""
                    with col2:
                        noi_dung["ket_qua"] = st.selectbox(
                            "Kết quả",
                            ["Đủ điều kiện", "Không đủ điều kiện",
                                "Đang xác minh", "Khác"],
                            key="csxh_xm_kq"
                        )
                    noi_dung["noi_dung_xm"] = st.text_area(
                        "Nội dung xác minh", key="csxh_xm_nd", height=100)

                else:
                    # Default: generic fields
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["ten_doi_tac"] = st.text_input(
                            "Tên đối tác/Tổ chức", key="csxh_def_ten")
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_def_qg")
                    with col2:
                        noi_dung["thoi_gian"] = st.text_input(
                            "Thời gian", key="csxh_def_tg")
                        noi_dung["tinh_trang"] = st.text_input(
                            "Tình trạng", key="csxh_def_tt")

                csxh_ghi_chu = st.text_area(
                    "Ghi chú", key="pv_csxh_ghi_chu", height=80)

                if st.form_submit_button("💾 Lưu hồ sơ đặc thù", type="primary"):
                    # Kiểm tra có dữ liệu hợp lệ
                    has_data = any(v for v in noi_dung.values()
                                   if v) or csxh_ghi_chu
                    if has_data:
                        save_ho_so_dac_thu(
                            cccd, csxh_loai, noi_dung, csxh_ghi_chu)
                        st.success(
                            f"✅ Đã thêm hồ sơ: {LOAI_HINH_DAC_THU.get(csxh_loai, csxh_loai)}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập thông tin!")

    # ===== TAB TÀI LIỆU =====
    with tab_tl:
        st.markdown("#### 📎 Tài liệu đính kèm")

        # Hiển thị danh sách tài liệu
        df_tai_lieu = get_tai_lieu_by_cccd(cccd)
        if not df_tai_lieu.empty:
            st.markdown("##### 📂 Danh sách tài liệu")

            for idx, row in df_tai_lieu.iterrows():
                col_info, col_download, col_del = st.columns([4, 1, 1])
                with col_info:
                    file_size_kb = row['dung_luong'] / 1024
                    # Preview ảnh nếu là file ảnh
                    if row['dinh_dang'] in ['jpg', 'jpeg', 'png', 'gif']:
                        file_path, _ = get_file_path(row['id'])
                        if file_path and file_path.exists():
                            st.image(str(file_path), width=200)
                    st.markdown(f"""
                    **{row['loai_tai_lieu']}**: {row['ten_file_goc']} | 
                    📦 {file_size_kb:.1f} KB | 
                    📅 {row['created_at']}
                    """)
                    if row['mo_ta']:
                        st.caption(f"📝 {row['mo_ta']}")
                with col_download:
                    file_path, original_name = get_file_path(row['id'])
                    if file_path and file_path.exists():
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                "⬇️",
                                data=f.read(),
                                file_name=original_name,
                                key=f"pv_dl_tl_{row['id']}",
                                help="Tải xuống"
                            )
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['ten_file_goc']}"):
                        st.markdown(f"Xóa file **{row['ten_file_goc']}**?")
                        if st.button("Xác nhận", key=f"confirm_pv_del_tl_{row['id']}", type="primary"):
                            delete_tai_lieu(row['id'])
                            st.toast(f"✅ Đã xóa: {row['ten_file_goc']}", icon="✅")
                            st.rerun()
            st.markdown("---")
        else:
            st.info("💡 Chưa có tài liệu đính kèm")

        # Form upload tài liệu mới
        with st.expander("➕ Upload tài liệu mới", expanded=False):
            st.caption(
                f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")

            with st.form("pv_upload_tai_lieu_form"):
                uploaded_file = st.file_uploader(
                    "Chọn file",
                    type=ALLOWED_EXTENSIONS,
                    key="pv_upload_tai_lieu"
                )

                col1, col2 = st.columns(2)
                with col1:
                    loai_tai_lieu = st.selectbox(
                        "Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="pv_tl_loai")
                with col2:
                    mo_ta_tl = st.text_input(
                        "Mô tả (tùy chọn)", key="pv_tl_mo_ta")

                if st.form_submit_button("💾 Upload", type="primary"):
                    if uploaded_file:
                        success, message = save_tai_lieu(
                            cccd, uploaded_file, loai_tai_lieu, mo_ta_tl)
                        if success:
                            st.success(f"✅ {message}: {uploaded_file.name}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Vui lòng chọn file để upload!")

```

## views/profile/__init__.py
```py
from .ui import page_profile_view
from .getters import (
    get_doi_tuong_detail,
    get_nhan_than_by_cccd,
    get_lien_he_by_cccd,
    get_tai_chinh_by_cccd,
    get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd,
    get_tai_lieu_by_cccd,
    get_file_path
)
from .actions import (
    delete_nhan_than,
    delete_lien_he,
    delete_tai_chinh,
    delete_phuong_tien,
    delete_ho_so_dac_thu,
    delete_tai_lieu,
    delete_doi_tuong
)

__all__ = [
    'page_profile_view',
    'get_doi_tuong_detail',
    'get_nhan_than_by_cccd',
    'get_lien_he_by_cccd',
    'get_tai_chinh_by_cccd',
    'get_phuong_tien_by_cccd',
    'get_ho_so_dac_thu_by_cccd',
    'get_tai_lieu_by_cccd',
    'get_file_path',
    'delete_nhan_than',
    'delete_lien_he',
    'delete_tai_chinh',
    'delete_phuong_tien',
    'delete_ho_so_dac_thu',
    'delete_tai_lieu',
    'delete_doi_tuong'
]

```

