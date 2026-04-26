import sys
import random
from datetime import datetime, timedelta
from faker import Faker

sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from backend
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db.session import get_db
from backend.models.models import (
    DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan,
    HoSoDacThu, QuaTrinhHoatDong
)

fake = Faker('vi_VN')

def gen_cccd():
    # CCCD is 12 digits
    return f"{random.randint(100000000000, 999999999999)}"

PHAN_LOAI = ["Kỹ sư", "Công nhân", "Lao động tự do", "Giáo viên", "Bác sĩ", "Học sinh", "Doanh nhân", "Nhân viên văn phòng", "Khác"]
GIOI_TINH = ["Nam", "Nữ", "Khác"]
QUAN_HE = ["Bố", "Mẹ", "Vợ", "Chồng", "Con trai", "Con gái", "Anh", "Chị", "Em", "Khác"]
LOAI_LIEN_HE = ["SĐT", "Email", "Zalo", "Facebook", "Telegram"]
NGAN_HANG = ["Vietcombank", "Techcombank", "MBBank", "BIDV", "Agribank", "VietinBank", "VPBank"]
LOAI_XE = ["Ô tô con", "Xe máy", "Xe tải", "Xe khách"]
QUAN_HUYEN = ["Hoàn Kiếm", "Ba Đình", "Tây Hồ", "Cầu Giấy", "Đống Đa", "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Hà Đông", "Nam Từ Liêm", "Bắc Từ Liêm", "Long Biên", "Thanh Trì", "Gia Lâm", "Đông Anh"]
LOAI_DAC_THU = ["Tiền án", "Tiền sự", "Vi phạm hành chính", "Theo dõi đặc biệt", "Cảnh báo xuất nhập cảnh"]

def gen_dia_chi_xa():
    street = fake.street_address() if hasattr(fake, 'street_address') else fake.address().split(',')[0]
    phuong = f"Phường {random.randint(1, 20)}" if random.random() > 0.3 else f"Xã {fake.word().capitalize()}"
    quan = random.choice(QUAN_HUYEN)
    return f"{street}, {phuong}, Quận/Huyện {quan}"

def main():
    db = next(get_db())
    try:
        count = 1000
        print(f"Bắt đầu tạo {count} hồ sơ giả định...")
        
        for i in range(count):
            cccd = gen_cccd()
            ho_ten = fake.name()
            ngay_sinh = fake.date_of_birth(minimum_age=15, maximum_age=80)
            tinh = fake.city_name() if hasattr(fake, 'city_name') else fake.city()
            
            dt = DoiTuong(
                cccd=cccd,
                ho_ten=ho_ten,
                ngay_sinh=ngay_sinh,
                gioi_tinh=random.choice(GIOI_TINH),
                dia_chi_tinh=tinh,
                dia_chi_xa=gen_dia_chi_xa(),
                phan_loai_nghe_nghiep=random.choice(PHAN_LOAI),
                chi_tiet_nghe_nghiep=fake.job(),
                ghi_chu_chung=fake.sentence() if random.random() > 0.5 else "",
                is_draft=False
            )
            db.add(dt)
            
            # Liên hệ (1-3)
            for _ in range(random.randint(1, 3)):
                lh_loai = random.choice(LOAI_LIEN_HE)
                lh_val = fake.phone_number() if lh_loai in ("SĐT", "Zalo") else (fake.email() if lh_loai == "Email" else fake.user_name())
                db.add(LienHe(cccd=cccd, loai_lien_he=lh_loai, gia_tri=lh_val, ghi_chu=fake.sentence()[:50]))
            
            # Tài chính (0-2)
            for _ in range(random.randint(0, 2)):
                stk = f"{random.randint(10000000, 9999999999)}"
                db.add(TaiChinh(cccd=cccd, ngan_hang=random.choice(NGAN_HANG), so_tai_khoan=stk, chu_tai_khoan=ho_ten, ghi_chu="Thẻ chính"))
                
            # Phương tiện (0-2)
            for _ in range(random.randint(0, 2)):
                bien = getattr(fake, 'license_plate', lambda: f"{random.randint(10,99)}{random.choice(['A','B','C','D'])}-{random.randint(10000,99999)}")()
                db.add(PhuongTien(cccd=cccd, loai_xe=random.choice(LOAI_XE), bien_kiem_soat=bien, ten_phuong_tien=fake.word(), ghi_chu="Chính chủ"))
                
            # Nhân thân (1-4)
            for _ in range(random.randint(1, 4)):
                qh = random.choice(QUAN_HE)
                db.add(NhanThan(
                    cccd=cccd,
                    loai_quan_he=qh,
                    ho_ten=fake.name(),
                    cccd_nhan_than=gen_cccd() if random.random() > 0.3 else "",
                    ngay_sinh=fake.date_of_birth(minimum_age=1, maximum_age=90),
                    gioi_tinh="Nam" if qh in ("Bố", "Chồng", "Con trai", "Anh") else ("Nữ" if qh in ("Mẹ", "Vợ", "Con gái", "Chị") else random.choice(GIOI_TINH)),
                    dia_chi_tinh=tinh if random.random() > 0.2 else (fake.city_name() if hasattr(fake, 'city_name') else fake.city()),
                    dia_chi_xa=gen_dia_chi_xa(),
                    nghe_nghiep=fake.job(),
                    noi_o=fake.address(),
                    ghi_chu=fake.sentence()[:50]
                ))
                
            # Đặc thù (0-1)
            if random.random() > 0.8:
                db.add(HoSoDacThu(cccd=cccd, loai_hinh=random.choice(LOAI_DAC_THU), noi_dung_chi_tiet=fake.paragraph(), ghi_chu="Đáng chú ý"))
                
            # Quá trình (1-5)
            for _ in range(random.randint(1, 5)):
                start_date = fake.date_between(start_date='-5y', end_date='today')
                end_date = start_date + timedelta(days=random.randint(10, 300))
                
                # Để test chức năng lịch (đến hạn / sắp đến hạn)
                if random.random() > 0.7:
                    # Gán end_date vào trong khoảng -5 ngày tới +10 ngày so với hôm nay
                    end_date = datetime.now().date() + timedelta(days=random.randint(-5, 10))
                
                db.add(QuaTrinhHoatDong(
                    cccd=cccd,
                    thoi_gian=f"{start_date.month}/{start_date.year}",
                    ngay_bat_dau=start_date,
                    ngay_ket_thuc=end_date,
                    noi_dung=fake.sentence(),
                    ghi_chu=fake.sentence()[:50]
                ))
            
            if (i + 1) % 100 == 0:
                db.commit()
                print(f"Đã tạo {i + 1} hồ sơ...")
                
        db.commit()
        print("Tạo dữ liệu giả định THÀNH CÔNG!")
    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
