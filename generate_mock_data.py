# -*- coding: utf-8 -*-
"""
Script tạo 500 dữ liệu mẫu cho hệ thống VCFE Database.
Bám sát các trường dữ liệu và hằng số đã khai báo trong project.
"""

import json
import random
from datetime import datetime, timedelta
import os

# --- Cấu hình dữ liệu mẫu ---
HO_VN = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM_NAM = ["Văn", "Hữu", "Đức", "Thành", "Minh", "Hải", "Tuấn", "Thanh", "Quang", "Trọng", "Trung"]
DEM_NU = ["Thị", "Ngọc", "Thu", "Xuân", "Thanh", "Linh", "Mai", "Phương", "Hương"]
TEN_NAM = ["An", "Anh", "Bình", "Cường", "Dũng", "Dương", "Đạt", "Giang", "Hải", "Hào", "Hiếu", "Hòa", "Hùng", "Hưng", "Khang", "Khánh", "Khoa", "Kiên", "Lâm", "Long", "Nam", "Nghĩa", "Phong", "Phúc", "Quân", "Quang", "Quốc", "Sơn", "Thái", "Thành", "Thiên", "Thịnh", "Tiến", "Toàn", "Trí", "Trọng", "Trung", "Tuấn", "Tùng", "Vinh", "Việt"]
TEN_NU = ["Vy", "Yến", "Thảo", "Hương", "Trang", "Linh", "Nhung", "Mai", "Lan", "Hoa", "Nguyệt", "Nga", "Phương", "Chi", "Diệp", "Hà", "Hạnh", "Hiền"]

# Lấy từ constants.py
DAN_SACH_XA_PHU_THO = [
    "Phường Âu Cơ", "Phường Hòa Bình", "Phường Kỳ Sơn", "Phường Nông Trang", "Phường Phong Châu",
    "Phường Phú Thọ", "Phường Phúc Yên", "Phường Tân Hòa", "Phường Thanh Miếu", "Phường Thống Nhất",
    "Phường Vân Phú", "Phường Việt Trì", "Phường Vĩnh Phúc", "Phường Vĩnh Yên", "Phường Xuân Hòa",
    "Xã An Bình", "Xã An Nghĩa", "Xã Bản Nguyên", "Xã Bao La", "Xã Bằng Luân", "Xã Bình Nguyên"
    # ... rút gọn để script chạy nhanh, thực tế sẽ lấy từ constants
]

PHAN_LOAI_NGHE_NGHIEP = [
    "Cơ quan nhà nước", "Lao động tự do", "Doanh nghiệp tư nhân", "Nông nghiệp",
    "FDI", "NGO", "Học sinh/Sinh viên", "Hưu trí", "Thất nghiệp", "Khác"
]

LOAI_LIEN_HE = ["SĐT", "Email", "Facebook", "Zalo", "Telegram", "Instagram", "Tiktok", "Khác"]

LOAI_QUAN_HE = [
    "Bố", "Mẹ", "Vợ", "Chồng", "Con trai", "Con gái",
    "Anh", "Chị", "Em trai", "Em gái", "Bạn bè", "Đồng nghiệp", "Khác",
]

NGAN_HANG = [
    "Vietcombank", "Vietinbank", "BIDV", "Agribank", "Techcombank",
    "MB Bank", "ACB", "Sacombank", "VPBank", "TPBank", "HDBank"
]

LOAI_HINH_DAC_THU = {
    "Hon_Nhan_NN": "Kết hôn/sống chung với người nước ngoài",
    "Lam_Viec_NN": "Làm việc cho tổ chức nước ngoài (NGO/FDI)",
    "Hoc_Tap_Cong_Tac_NN": "Du học/Công tác nước ngoài",
    "Vi_Pham_NN": "Từng vi phạm pháp luật ở nước ngoài",
    "Xac_Minh": "Đã từng được xác minh",
}

# --- Helper functions ---
def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

def random_date(start_year=1960, end_year=2005):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%Y-%m-%d")

def generate_cccd():
    return f"025{random.randint(0, 9)}{random.randint(10000000, 99999999)}"

def generate_phone():
    prefixes = ["090", "091", "098", "097", "034", "035", "036", "037", "038", "039", "070", "076", "077", "078", "079", "081", "082", "083", "084", "085"]
    return f"{random.choice(prefixes)}{random.randint(1000000, 9999999)}"

def generate_account_number():
    return "".join([str(random.randint(0, 9)) for _ in range(random.randint(9, 14))])

def generate_data(num_records=500):
    # Cố gắng import danh sách xã thực tế từ project
    try:
        from backend.constants import DAN_SACH_XA_PHU_THO as REAL_XA
        xa_list = REAL_XA
    except ImportError:
        xa_list = DAN_SACH_XA_PHU_THO

    data = []
    cccd_list = [] # Để đảm bảo không trùng và dùng cho nhân thân
    
    # Bước 1: Tạo danh sách CCCD trước
    for _ in range(num_records * 2): # Tạo dư để làm nhân thân
        cccd_list.append(generate_cccd())
    
    for i in range(num_records):
        cccd = cccd_list[i]
        is_male = random.choice([True, False])
        ho = random.choice(HO_VN)
        dem = random.choice(DEM_NAM) if is_male else random.choice(DEM_NU)
        ten = random.choice(TEN_NAM) if is_male else random.choice(TEN_NU)
        ho_ten = f"{ho} {dem} {ten}"
        
        # 1. Đối tượng chính
        doi_tuong = {
            "cccd": cccd,
            "ho_ten": ho_ten,
            "ngay_sinh": random_date(),
            "gioi_tinh": "Nam" if is_male else "Nữ",
            "dia_chi_tinh": "Phú Thọ",
            "dia_chi_xa": random.choice(xa_list),
            "phan_loai_nghe_nghiep": random.choice(PHAN_LOAI_NGHE_NGHIEP),
            "chi_tiet_nghe_nghiep": "Mô tả công việc chi tiết tại đơn vị...",
            "ghi_chu_chung": "Dữ liệu giả định phục vụ thử nghiệm hệ thống.",
            "lien_he": [],
            "tai_chinh": [],
            "nhan_than": [],
            "ho_so_dac_thu": []
        }
        
        # 2. Liên hệ (SĐT, Zalo...)
        doi_tuong["lien_he"].append({
            "loai_lien_he": "SĐT",
            "gia_tri": generate_phone(),
            "ghi_chu": "Số chính"
        })
        if random.random() > 0.6:
            doi_tuong["lien_he"].append({
                "loai_lien_he": random.choice(["Facebook", "Zalo", "Email"]),
                "gia_tri": "contact_" + str(random.randint(1000, 9999)),
                "ghi_chu": ""
            })
            
        # 3. Tài chính
        for _ in range(random.randint(1, 2)):
            doi_tuong["tai_chinh"].append({
                "ngan_hang": random.choice(NGAN_HANG),
                "so_tai_khoan": generate_account_number(),
                "chu_tai_khoan": ho_ten.upper(),
                "ghi_chu": "Tài khoản cá nhân"
            })
            
        # 4. Nhân thân (1-3 người)
        for _ in range(random.randint(1, 3)):
            nt_is_male = random.choice([True, False])
            nt_ho = ho if random.random() > 0.3 else random.choice(HO_VN)
            nt_dem = random.choice(DEM_NAM) if nt_is_male else random.choice(DEM_NU)
            nt_ten = random.choice(TEN_NAM) if nt_is_male else random.choice(TEN_NU)
            
            doi_tuong["nhan_than"].append({
                "loai_quan_he": random.choice(LOAI_QUAN_HE),
                "ho_ten": f"{nt_ho} {nt_dem} {nt_ten}",
                "cccd_nhan_than": cccd_list[num_records + random.randint(0, num_records - 1)],
                "ngay_sinh": random_date(1950, 2010),
                "nghe_nghiep": random.choice(PHAN_LOAI_NGHE_NGHIEP),
                "noi_o": "Phú Thọ"
            })
            
        # 5. Hồ sơ đặc thù
        key_dt = random.choice(list(LOAI_HINH_DAC_THU.keys()))
        doi_tuong["ho_so_dac_thu"].append({
            "loai_hinh": key_dt,
            "noi_dung_chi_tiet": f"Thông tin chi tiết về: {LOAI_HINH_DAC_THU[key_dt]}",
            "ghi_chu": "Dữ liệu nghiệp vụ mẫu"
        })
        
        data.append(doi_tuong)
        
    return data

def import_to_db(mock_data):
    try:
        from backend.db.session import SessionLocal
        from backend.models.models import DoiTuong, LienHe, TaiChinh, NhanThan, HoSoDacThu
        
        db = SessionLocal()
        safe_print("Dang import du lieu vao database...")
        
        for item in mock_data:
            dt = DoiTuong(
                cccd=item["cccd"],
                ho_ten=item["ho_ten"],
                ngay_sinh=datetime.strptime(item["ngay_sinh"], "%Y-%m-%d").date(),
                gioi_tinh=item["gioi_tinh"],
                dia_chi_tinh=item["dia_chi_tinh"],
                dia_chi_xa=item["dia_chi_xa"],
                phan_loai_nghe_nghiep=item["phan_loai_nghe_nghiep"],
                chi_tiet_nghe_nghiep=item["chi_tiet_nghe_nghiep"],
                ghi_chu_chung=item["ghi_chu_chung"]
            )
            db.add(dt)
            
            for lh in item["lien_he"]:
                db.add(LienHe(cccd=dt.cccd, loai_lien_he=lh["loai_lien_he"], gia_tri=lh["gia_tri"], ghi_chu=lh["ghi_chu"]))
                
            for tc in item["tai_chinh"]:
                db.add(TaiChinh(cccd=dt.cccd, ngan_hang=tc["ngan_hang"], so_tai_khoan=tc["so_tai_khoan"], chu_tai_khoan=tc["chu_tai_khoan"], ghi_chu=tc["ghi_chu"]))
                
            for nt in item["nhan_than"]:
                db.add(NhanThan(
                    cccd=dt.cccd,
                    loai_quan_he=nt["loai_quan_he"],
                    ho_ten=nt["ho_ten"],
                    cccd_nhan_than=nt["cccd_nhan_than"],
                    ngay_sinh=datetime.strptime(nt["ngay_sinh"], "%Y-%m-%d").date(),
                    nghe_nghiep=nt["nghe_nghiep"],
                    noi_o=nt["noi_o"]
                ) )
                
            for hs in item["ho_so_dac_thu"]:
                db.add(HoSoDacThu(cccd=dt.cccd, loai_hinh=hs["loai_hinh"], noi_dung_chi_tiet=hs["noi_dung_chi_tiet"], ghi_chu=hs["ghi_chu"]))
        
        db.commit()
        db.close()
        safe_print("Import thanh cong!")
    except Exception as e:
        safe_print(f"Loi khi import: {e}")

if __name__ == "__main__":
    import sys
    
    safe_print("Dang tao 500 truong hop du lieu gia dinh...")
    mock_data = generate_data(500)
    
    output_file = "mock_data_500.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=4)
        
    safe_print(f"Hoan tat! Da luu 500 ban ghi vao file: {output_file}")
    
    if "--import" in sys.argv:
        import_to_db(mock_data)
    else:
        safe_print("Goi y: Chay 'python generate_mock_data.py --import' de nap vao DB (can set DB_PASSWORD).")
    
    safe_print("\nCau truc mot ban ghi mau:")
    sample = mock_data[0]
    safe_print(f"CCCD: {sample['cccd']}, Ho ten: {sample['ho_ten']}")


