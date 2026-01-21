import pandas as pd
from database import get_connection
import time
import os
import unicodedata
import re

# Reuse logic from views/tra_cuu.py for baseline
def remove_accents(input_str):
    if not input_str:
        return ""
    s1 = u'Đ'.encode('utf-8')
    s2 = u'đ'.encode('utf-8')
    input_str = input_str.replace(s1.decode('utf-8'), 'D').replace(s2.decode('utf-8'), 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn')

def normalize_string(s):
    """Chuẩn hóa chuỗi: bỏ dấu, thường, bỏ khoảng trắng"""
    if not s:
        return ""
    s = remove_accents(s).lower()
    return re.sub(r'[^a-z0-9]', '', s)

def is_fuzzy_match(query, text):
    """
    Kiểm tra query có phải là match của text không.
    """
    if not query or not text:
        return False

    n_query = normalize_string(query)
    n_text = normalize_string(text)

    # 1. Exact contains (relaxed)
    if n_query in n_text:
        return True

    # 2. Subsequence match
    if len(n_query) >= 3:
        it = iter(n_text)
        if all(char in it for char in n_query):
            return True

    return False

def import_data(filename):
    """Quickly import data from Excel to DB for testing"""
    print(f"Importing {filename}...")
    try:
        # skiprows=1 is wrong because generate_1000_records.py output does NOT have the sample row like generate_test_data.py
        # Actually generate_1000_records.py output DOES have the sample row at row 2 (index 1), so header is row 1 (index 0).
        # Let's check the printed columns again.
        # The columns are ['CCCD (*)', 'Họ và tên (*)', ...], which means header is correct.

        df = pd.read_excel(filename, sheet_name="1. Đối tượng")
        # However, generate_1000_records.py says:
        # Row 1: Header
        # Row 2: Sample
        # Row 3+: Data
        # So we should skip the first row of data which corresponds to the sample row if pandas reads header=0

        # If I use pd.read_excel(..., header=0), row 1 is header. Row 2 becomes index 0.
        # Row 2 is sample data. So we need to drop index 0.

        df = df.iloc[1:].reset_index(drop=True)

        # Rename columns to match DB
        df = df.rename(columns={
            "CCCD (*)": "cccd",
            "Họ và tên (*)": "ho_ten",
            "Ngày sinh (dd/mm/yyyy)": "ngay_sinh",
            "Giới tính": "gioi_tinh",
            "Tỉnh/TP": "dia_chi_tinh",
            "Xã/Phường": "dia_chi_xa",
            "Phân loại nghề nghiệp": "phan_loai_nghe_nghiep",
            "Chi tiết nơi làm việc": "chi_tiet_nghe_nghiep",
            "Ghi chú chung": "ghi_chu_chung"
        })
        # Filter only columns in DB
        cols = ["cccd", "ho_ten", "ngay_sinh", "gioi_tinh", "dia_chi_tinh",
                "dia_chi_xa", "phan_loai_nghe_nghiep", "chi_tiet_nghe_nghiep", "ghi_chu_chung"]
        df = df[cols]
        # Add required columns
        df['anh_chan_dung'] = ''

        conn = get_connection()
        try:
            # Clean old data
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doi_tuong")
            conn.commit()

            # Insert new data
            df.to_sql('doi_tuong', conn, if_exists='append', index=False)
            print(f"Imported {len(df)} records.")
        finally:
            conn.close()
    except Exception as e:
        print(f"Import failed: {e}")

def benchmark_search(query, search_type="Tất cả", iterations=10):
    conn = get_connection()
    try:
        df_all = pd.read_sql_query("SELECT * FROM doi_tuong", conn)
        print(f"Benchmarking search for '{query}' on {len(df_all)} records ({iterations} iterations)...")

        start_time = time.time()

        for _ in range(iterations):
            filtered_rows = []
            for index, row in df_all.iterrows():
                match = False
                # Check CCCD (Exact/Contains)
                if search_type in ["Tất cả", "CCCD"]:
                    if query.lower() in str(row['cccd']).lower():
                        match = True

                # Check Họ tên (Fuzzy)
                if not match and search_type in ["Tất cả", "Họ tên"]:
                    if is_fuzzy_match(query, row['ho_ten']):
                        match = True

                if match:
                    filtered_rows.append(row)

            df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame(columns=df_all.columns)

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        print(f"Average time per search (Old): {avg_time:.4f} seconds")
        return avg_time, len(df)

    finally:
        conn.close()

if __name__ == "__main__":
    # Ensure DB is initialized
    import database
    # database.create_tables() # Already called if importing database

    # Check if data exists, if not import
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doi_tuong")
    count = cursor.fetchone()[0]
    conn.close()

    if count < 1000:
        if not os.path.exists("test_data_1000.xlsx"):
            print("Please run generate_1000_records.py first")
        else:
            import_data("test_data_1000.xlsx")

    # Run benchmark
    benchmark_search("Nguyễn")
