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

VALIDATOR_CONFIG = {
    "doi_tuong": {
        "index": 0,
        "required_cols": ["CCCD (*)"]
    },
    "lien_he": {
        "index": 1,
        "required_cols": ["CCCD (*)"]
    },
    "tai_chinh": {
        "index": 2,
        "required_cols": ["CCCD (*)"]
    },
    "phuong_tien": {
        "index": 3,
        "required_cols": ["CCCD (*)"]
    },
    "ho_so_dac_thu": {
        "index": 4,
        "required_cols": ["CCCD (*)"]
    },
    "than_nhan": {
        "index": 5,
        "required_cols": ["CCCD (*)"]
    },
    "qua_trinh_hoat_dong": {
        "index": 6,
        "required_cols": ["CCCD (*)"]
    }
}

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
        def should_read(sheet_key):
            if import_type == 'all':
                return sheet_key in VALIDATOR_CONFIG and VALIDATOR_CONFIG[sheet_key]['index'] < len(sheet_names)
            return import_type == sheet_key and sheet_key in VALIDATOR_CONFIG and VALIDATOR_CONFIG[sheet_key]['index'] < len(sheet_names)

        # ===== SHEET: ĐỐI TƯỢNG =====
        if should_read('doi_tuong'):
            config = VALIDATOR_CONFIG['doi_tuong']
            target_sheet_index = config['index'] if import_type == 'all' else 0 # If single import, it's always the first sheet
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
        if should_read('lien_he'):
            valid_cccds = existing_cccds.union(
                results['doi_tuong'].get('new_cccds', set()))
            config = VALIDATOR_CONFIG['lien_he']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
        if 'than_nhan' in VALIDATOR_CONFIG and should_read('than_nhan'):
            config = VALIDATOR_CONFIG['than_nhan']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
        if 'tai_chinh' in VALIDATOR_CONFIG and should_read('tai_chinh'):
            config = VALIDATOR_CONFIG['tai_chinh']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
        if 'phuong_tien' in VALIDATOR_CONFIG and should_read('phuong_tien'):
            config = VALIDATOR_CONFIG['phuong_tien']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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

        # ===== SHEET: HỒ SƠ ĐẶC THÙ =====
        if 'ho_so_dac_thu' in VALIDATOR_CONFIG and should_read('ho_so_dac_thu'):
            config = VALIDATOR_CONFIG['ho_so_dac_thu']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
        if 'qua_trinh_hoat_dong' in VALIDATOR_CONFIG and should_read('qua_trinh_hoat_dong'):
            config = VALIDATOR_CONFIG['qua_trinh_hoat_dong']
            target_sheet_index = config['index'] if import_type == 'all' else 0
            df = pd.read_excel(xls, sheet_name=target_sheet_index, skiprows=0)
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
