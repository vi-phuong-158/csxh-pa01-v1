# -*- coding: utf-8 -*-
import pandas as pd
import json
from datetime import datetime
from database import get_connection
from constants import _LOAI_QUAN_HE_DOI_XUNG

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
        'quan_he_graph': 0,
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

            for row in df.to_dict('records'):
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
            for row in df.to_dict('records'):
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'loai_lien_he'),
                    str(row.get('gia_tri')).strip() if pd.notna(row.get('gia_tri')) else None,
                    get_val(row, 'ghi_chu')
                ))

            if data_list:
                cursor.executemany("""
                    INSERT INTO lien_he (cccd, loai_lien_he, gia_tri, ghi_chu)
                    VALUES (?, ?, ?, ?)
                """, data_list)
                stats['lien_he'] = len(data_list)

        # ===== INSERT QUAN HỆ (Graph nếu có CCCD nhân thân, Satellite nếu không) =====
        if 'than_nhan' in validated_data and validated_data['than_nhan']['data'] is not None:
            df = validated_data['than_nhan']['data']
            graph_list = []       # (cccd_1, cccd_2, loai_quan_he, mo_ta)
            draft_upsert = []     # (cccd, ho_ten, is_draft) — hồ sơ nháp mới
            draft_fill_name = []  # (ho_ten, cccd) — fill tên nếu đã có hồ sơ nhưng chưa có tên
            satellite_list = []   # (cccd, ho_ten, loai_quan_he, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)

            for row in df.to_dict('records'):
                cccd_main = str(row['cccd']).strip()
                loai_qh = get_val(row, 'quan_he') or 'Khác'
                ho_ten = get_val(row, 'ho_ten')

                # Chuẩn hóa CCCD nhân thân (giống normalize_cccd trong validators)
                cccd_nt = ""
                cccd_nt_raw = row.get('cccd_nhan_than')
                if pd.notna(cccd_nt_raw) and str(cccd_nt_raw).strip():
                    s = str(cccd_nt_raw).strip()
                    if s.endswith('.0'):
                        s = s[:-2]
                    if s.isdigit() and len(s) < 12:
                        s = s.zfill(12)
                    cccd_nt = s

                is_valid_nt = cccd_nt and cccd_nt.isdigit() and len(cccd_nt) in (9, 12) and cccd_nt != cccd_main

                if is_valid_nt:
                    # Graph path: chuẩn hóa cặp theo loại quan hệ
                    if loai_qh in _LOAI_QUAN_HE_DOI_XUNG:
                        cccd_1, cccd_2 = min(cccd_main, cccd_nt), max(cccd_main, cccd_nt)
                    else:
                        cccd_1, cccd_2 = cccd_main, cccd_nt
                    graph_list.append((cccd_1, cccd_2, loai_qh, get_val(row, 'ghi_chu')))
                    draft_upsert.append((cccd_nt, ho_ten, 0 if ho_ten else 1))
                    if ho_ten:
                        draft_fill_name.append((ho_ten, cccd_nt))
                else:
                    # Satellite path: ghi chú quan hệ không có CCCD
                    satellite_list.append((
                        cccd_main, ho_ten, loai_qh,
                        get_val(row, 'nam_sinh'),
                        get_val(row, 'nghe_nghiep'),
                        get_val(row, 'dia_chi'),
                        get_val(row, 'ghi_chu')
                    ))

            # 1. Tạo hồ sơ nháp cho cccd_nhan_than chưa tồn tại
            if draft_upsert:
                cursor.executemany("""
                    INSERT OR IGNORE INTO doi_tuong (cccd, ho_ten, is_draft)
                    VALUES (?, ?, ?)
                """, draft_upsert)
            # 2. Fill tên nếu hồ sơ đã có nhưng chưa có tên
            if draft_fill_name:
                cursor.executemany("""
                    UPDATE doi_tuong SET ho_ten=? WHERE cccd=? AND (ho_ten IS NULL OR ho_ten='')
                """, draft_fill_name)

            # 3. Insert graph edges (bỏ qua nếu cặp đã tồn tại)
            if graph_list:
                cursor.executemany("""
                    INSERT OR IGNORE INTO quan_he_doi_tuong (cccd_1, cccd_2, loai_quan_he, mo_ta)
                    VALUES (?, ?, ?, ?)
                """, graph_list)
                stats['quan_he_graph'] = len(graph_list)

            # 4. Insert satellite (ghi chú không có CCCD)
            if satellite_list:
                cursor.executemany("""
                    INSERT INTO nhan_than (cccd, ho_ten, loai_quan_he, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, satellite_list)
                stats['than_nhan'] = len(satellite_list)

        # ===== INSERT TÀI CHÍNH =====
        if validated_data['tai_chinh']['data'] is not None:
            df = validated_data['tai_chinh']['data']
            data_list = []
            for row in df.to_dict('records'):
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'ngan_hang'),
                    str(row.get('so_tai_khoan')).strip() if pd.notna(row.get('so_tai_khoan')) else None,
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
            for row in df.to_dict('records'):
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'loai_xe'),
                    str(row.get('bien_kiem_soat')).strip() if pd.notna(row.get('bien_kiem_soat')) else None,
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
            for row in df.to_dict('records'):
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
            for row in df.to_dict('records'):
                data_list.append((
                    str(row['cccd']).strip(),
                    get_val(row, 'thoi_gian'),
                    str(row.get('noi_dung')).strip() if pd.notna(row.get('noi_dung')) else None,
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
        graph_count = stats.get('quan_he_graph', 0)
        sat_count = stats.get('than_nhan', 0)
        qh_detail = ""
        if graph_count or sat_count:
            qh_detail = f" (quan hệ: {graph_count} hồ sơ liên kết, {sat_count} ghi chú)"
        return True, f"Import thành công {total} bản ghi!{qh_detail}", stats

    except Exception as e:
        # Rollback nếu có lỗi
        conn.rollback()
        conn.close()
        return False, f"Lỗi import tại bước SQL: {str(e)}", stats
