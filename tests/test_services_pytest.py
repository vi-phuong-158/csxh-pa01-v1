# -*- coding: utf-8 -*-
"""
Unit Tests cho services.py - VCFE Database
==================================================
Sử dụng pytest framework.

Tests bao gồm:
- validate_cccd: Kiểm tra CCCD hợp lệ / không hợp lệ
- sanitize_filename: Kiểm tra lọc tên file nguy hiểm
- save_doi_tuong: Lưu đối tượng chính
- save_lien_he: Lưu thông tin liên hệ (giá trị rỗng, hợp lệ)
- save_tai_chinh: Lưu thông tin tài chính
- save_phuong_tien: Lưu thông tin phương tiện
- save_nhan_than: Lưu thông tin nhân thân
- check_cccd_exists: Kiểm tra CCCD tồn tại
- save_ho_so_dac_thu: Lưu hồ sơ đặc thù (JSON content)

Chạy tests:
    pytest tests/test_services_pytest.py -v
"""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import (
    validate_cccd,
    sanitize_filename,
    save_doi_tuong,
    save_lien_he,
    save_tai_chinh,
    save_phuong_tien,
    save_nhan_than,
    save_ho_so_dac_thu,
    check_cccd_exists,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def in_memory_db():
    """
    Tạo database SQLite in-memory với schema tương tự production.
    Dùng cho tất cả các test cần truy cập database.
    """
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Tạo bảng doi_tuong
    cursor.execute("""
        CREATE TABLE doi_tuong (
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

    # Tạo bảng lien_he
    cursor.execute("""
        CREATE TABLE lien_he (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_lien_he TEXT,
            gia_tri TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tạo bảng tai_chinh
    cursor.execute("""
        CREATE TABLE tai_chinh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            ngan_hang TEXT,
            so_tai_khoan TEXT,
            chu_tai_khoan TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tạo bảng phuong_tien
    cursor.execute("""
        CREATE TABLE phuong_tien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_xe TEXT,
            bien_kiem_soat TEXT,
            ten_phuong_tien TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tạo bảng nhan_than
    cursor.execute("""
        CREATE TABLE nhan_than (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_quan_he TEXT NOT NULL,
            ho_ten TEXT,
            cccd_nhan_than TEXT,
            ngay_sinh DATE,
            nghe_nghiep TEXT,
            noi_o TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tạo bảng ho_so_dac_thu
    cursor.execute("""
        CREATE TABLE ho_so_dac_thu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cccd TEXT NOT NULL,
            loai_hinh TEXT NOT NULL,
            noi_dung_chi_tiet TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_conn(in_memory_db):
    """
    Tạo mock connection bọc quanh in-memory DB thật.
    Cho phép test thực thi SQL thật nhưng mock được get_connection().
    """
    mock = MagicMock()
    mock.cursor.side_effect = in_memory_db.cursor
    mock.commit.side_effect = in_memory_db.commit
    mock.rollback.side_effect = in_memory_db.rollback
    mock.close.return_value = None
    return mock


@pytest.fixture
def sample_doi_tuong():
    """Dữ liệu mẫu cho một đối tượng."""
    return {
        'cccd': '001099123456',
        'ho_ten': 'Nguyễn Văn Test',
        'ngay_sinh': '1990-01-15',
        'gioi_tinh': 'Nam',
        'dia_chi_tinh': 'Phú Thọ',
        'dia_chi_xa': 'Phường Việt Trì',
        'phan_loai_nghe_nghiep': 'Lao động tự do',
        'chi_tiet_nghe_nghiep': 'Thợ điện',
        'ghi_chu_chung': 'Đối tượng test',
    }


# ============================================
# TESTS: validate_cccd
# ============================================

class TestValidateCCCD:
    """Tests cho hàm validate_cccd."""

    def test_cccd_valid_numeric(self):
        """CCCD chỉ gồm 12 số phải hợp lệ."""
        assert validate_cccd("012345678901") is True

    def test_cccd_valid_alphanumeric(self):
        """CCCD chứa cả chữ và số phải hợp lệ."""
        assert validate_cccd("AbCd1234") is True

    def test_cccd_invalid_special_chars(self):
        """CCCD chứa ký tự đặc biệt phải bị từ chối."""
        assert validate_cccd("123-456-789") is False

    def test_cccd_path_traversal(self):
        """CCCD chứa path traversal phải bị từ chối."""
        assert validate_cccd("../etc/passwd") is False

    def test_cccd_empty_string(self):
        """CCCD rỗng phải bị từ chối."""
        assert validate_cccd("") is False

    def test_cccd_none(self):
        """CCCD None phải bị từ chối."""
        assert validate_cccd(None) is False

    def test_cccd_with_spaces(self):
        """CCCD chứa khoảng trắng phải bị từ chối."""
        assert validate_cccd("012 345 678") is False


# ============================================
# TESTS: sanitize_filename
# ============================================

class TestSanitizeFilename:
    """Tests cho hàm sanitize_filename."""

    def test_normal_filename(self):
        """Tên file bình thường giữ nguyên."""
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_path_traversal_removed(self):
        """Path traversal (../) phải bị loại bỏ."""
        result = sanitize_filename("../../etc/passwd.txt")
        assert ".." not in result
        assert "/" not in result

    def test_special_chars_removed(self):
        """Ký tự đặc biệt nguy hiểm phải bị xóa."""
        result = sanitize_filename("test@#$.jpg")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_unicode_preserved(self):
        """Tên file Unicode (tiếng Việt) phải được giữ lại."""
        assert sanitize_filename("tài liệu.pdf") == "tài liệu.pdf"

    def test_empty_filename(self):
        """Tên file rỗng phải trả về 'unnamed_file'."""
        assert sanitize_filename("") == "unnamed_file"

    def test_null_byte_removed(self):
        """Null byte injection phải bị xóa."""
        result = sanitize_filename("test\x00.jpg")
        assert "\x00" not in result


# ============================================
# TESTS: save_doi_tuong
# ============================================

class TestSaveDoiTuong:
    """Tests cho hàm save_doi_tuong."""

    @patch('services.get_connection')
    def test_save_doi_tuong_success(self, mock_get_conn, mock_conn, sample_doi_tuong):
        """Lưu đối tượng thành công."""
        mock_get_conn.return_value = mock_conn
        success, msg = save_doi_tuong(sample_doi_tuong)
        assert success is True
        assert "thành công" in msg

    @patch('services.get_connection')
    def test_save_doi_tuong_insert_data(self, mock_get_conn, mock_conn, in_memory_db, sample_doi_tuong):
        """Dữ liệu lưu đúng vào database."""
        mock_get_conn.return_value = mock_conn
        save_doi_tuong(sample_doi_tuong)

        cursor = in_memory_db.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (sample_doi_tuong['cccd'],))
        row = cursor.fetchone()

        assert row is not None
        assert row['ho_ten'] == 'Nguyễn Văn Test'
        assert row['gioi_tinh'] == 'Nam'

    @patch('services.get_connection')
    def test_save_doi_tuong_duplicate_cccd(self, mock_get_conn, mock_conn, in_memory_db, sample_doi_tuong):
        """Lưu trùng CCCD phải thất bại."""
        mock_get_conn.return_value = mock_conn
        # Lưu lần 1
        save_doi_tuong(sample_doi_tuong)
        
        # Lưu lần 2 (trùng CCCD) - mock lại connection
        mock_conn_2 = MagicMock()
        mock_conn_2.cursor.side_effect = in_memory_db.cursor
        mock_conn_2.commit.side_effect = in_memory_db.commit
        mock_conn_2.close.return_value = None
        mock_get_conn.return_value = mock_conn_2
        
        success, msg = save_doi_tuong(sample_doi_tuong)
        assert success is False


# ============================================
# TESTS: save_lien_he
# ============================================

class TestSaveLienHe:
    """Tests cho hàm save_lien_he."""

    @patch('services.get_connection')
    def test_save_lien_he_success(self, mock_get_conn, mock_conn, in_memory_db):
        """Lưu liên hệ thành công."""
        # Tạo đối tượng cha trước
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('111222333444',))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        result = save_lien_he('111222333444', 'SĐT', '0987654321', 'SĐT chính')
        assert result is True

    @patch('services.get_connection')
    def test_save_lien_he_empty_value(self, mock_get_conn, mock_conn):
        """Giá trị rỗng phải trả về False."""
        mock_get_conn.return_value = mock_conn
        result = save_lien_he('111222333444', 'SĐT', '', '')
        assert result is False

    @patch('services.get_connection')
    def test_save_lien_he_verify_data(self, mock_get_conn, mock_conn, in_memory_db):
        """Dữ liệu liên hệ lưu đúng."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('222333444555',))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        save_lien_he('222333444555', 'Email', 'test@example.com', 'Email công việc')

        cursor = in_memory_db.cursor()
        cursor.execute("SELECT * FROM lien_he WHERE cccd = ?", ('222333444555',))
        row = cursor.fetchone()
        assert row is not None
        assert row['loai_lien_he'] == 'Email'
        assert row['gia_tri'] == 'test@example.com'


# ============================================
# TESTS: save_tai_chinh
# ============================================

class TestSaveTaiChinh:
    """Tests cho hàm save_tai_chinh."""

    @patch('services.get_connection')
    def test_save_tai_chinh_success(self, mock_get_conn, mock_conn, in_memory_db):
        """Lưu tài khoản ngân hàng thành công."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('333444555666',))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        result = save_tai_chinh('333444555666', 'Vietcombank', '001100223344', 'Nguyễn Văn A')
        assert result is True

    @patch('services.get_connection')
    def test_save_tai_chinh_empty_account(self, mock_get_conn, mock_conn):
        """Số tài khoản rỗng phải trả về False."""
        mock_get_conn.return_value = mock_conn
        result = save_tai_chinh('333444555666', 'Vietcombank', '', '')
        assert result is False


# ============================================
# TESTS: save_phuong_tien
# ============================================

class TestSavePhuongTien:
    """Tests cho hàm save_phuong_tien."""

    @patch('services.get_connection')
    def test_save_phuong_tien_success(self, mock_get_conn, mock_conn, in_memory_db):
        """Lưu phương tiện thành công."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('444555666777',))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        result = save_phuong_tien('444555666777', 'Xe máy', '19A1-12345', 'Honda Wave')
        assert result is True

    @patch('services.get_connection')
    def test_save_phuong_tien_empty_plate(self, mock_get_conn, mock_conn):
        """Biển số rỗng phải trả về False."""
        mock_get_conn.return_value = mock_conn
        result = save_phuong_tien('444555666777', 'Ô tô', '', '')
        assert result is False


# ============================================
# TESTS: save_nhan_than
# ============================================

class TestSaveNhanThan:
    """Tests cho hàm save_nhan_than."""

    @patch('services.get_connection')
    def test_save_nhan_than_success(self, mock_get_conn, mock_conn, in_memory_db):
        """Lưu nhân thân thành công."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('555666777888',))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        result = save_nhan_than(
            '555666777888', 'Bố', 'Nguyễn Văn Cha',
            cccd_nhan_than='999888777666',
            ngay_sinh='1960-05-10',
            nghe_nghiep='Hưu trí',
            noi_o='Phú Thọ'
        )
        assert result is True

    @patch('services.get_connection')
    def test_save_nhan_than_empty_name(self, mock_get_conn, mock_conn):
        """Họ tên rỗng phải trả về False."""
        mock_get_conn.return_value = mock_conn
        result = save_nhan_than('555666777888', 'Mẹ', '')
        assert result is False


# ============================================
# TESTS: save_ho_so_dac_thu
# ============================================

class TestSaveHoSoDacThu:
    """Tests cho hàm save_ho_so_dac_thu."""

    @patch('services.get_connection')
    def test_save_ho_so_dac_thu_success(self, mock_get_conn, mock_conn, in_memory_db):
        """Lưu hồ sơ đặc thù thành công."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('666777888999',))
        in_memory_db.commit()

        noi_dung = {"quoc_gia": "Hàn Quốc", "thoi_gian": "2020-2023"}
        mock_get_conn.return_value = mock_conn
        result = save_ho_so_dac_thu('666777888999', 'Hoc_Tap_Cong_Tac_NN', noi_dung, 'Du học')
        assert result is True

    @patch('services.get_connection')
    def test_save_ho_so_dac_thu_json_stored(self, mock_get_conn, mock_conn, in_memory_db):
        """Nội dung dict phải được lưu dạng JSON."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd) VALUES (?)", ('777888999000',))
        in_memory_db.commit()

        noi_dung = {"ten_to_chuc": "Samsung", "vai_tro": "Kỹ sư"}
        mock_get_conn.return_value = mock_conn
        save_ho_so_dac_thu('777888999000', 'Lam_Viec_NN', noi_dung)

        cursor = in_memory_db.cursor()
        cursor.execute("SELECT * FROM ho_so_dac_thu WHERE cccd = ?", ('777888999000',))
        row = cursor.fetchone()
        assert row is not None
        stored_data = json.loads(row['noi_dung_chi_tiet'])
        assert stored_data['ten_to_chuc'] == 'Samsung'

    @patch('services.get_connection')
    def test_save_ho_so_dac_thu_empty_dict(self, mock_get_conn, mock_conn):
        """Dict rỗng phải trả về False."""
        mock_get_conn.return_value = mock_conn
        result = save_ho_so_dac_thu('777888999000', 'Xac_Minh', {})
        assert result is False


# ============================================
# TESTS: check_cccd_exists
# ============================================

class TestCheckCCCDExists:
    """Tests cho hàm check_cccd_exists."""

    @patch('services.get_connection')
    def test_cccd_exists(self, mock_get_conn, mock_conn, in_memory_db):
        """CCCD đã có trong DB phải trả về True."""
        cursor = in_memory_db.cursor()
        cursor.execute("INSERT INTO doi_tuong (cccd, ho_ten) VALUES (?, ?)", ('888999000111', 'Test'))
        in_memory_db.commit()

        mock_get_conn.return_value = mock_conn
        assert check_cccd_exists('888999000111') is True

    @patch('services.get_connection')
    def test_cccd_not_exists(self, mock_get_conn, mock_conn):
        """CCCD không có trong DB phải trả về False."""
        mock_get_conn.return_value = mock_conn
        assert check_cccd_exists('999999999999') is False
