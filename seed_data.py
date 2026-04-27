from backend.db.session import SessionLocal
from backend.models.models import DoiTuong, NhanThan, TaiChinh, PhuongTien
from datetime import datetime
import random

def seed_data():
    db = SessionLocal()
    try:
        # Xóa data cũ (nếu còn)
        db.query(DoiTuong).delete()
        
        ho_strs = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
        dem_strs = ["Văn", "Thị", "Ngọc", "Hữu", "Đức", "Thành", "Minh", "Thu", "Xuân", "Hải", "Tuấn", "Thanh"]
        ten_strs = ["An", "Anh", "Bình", "Cường", "Dũng", "Dương", "Đạt", "Giang", "Hải", "Hào", "Hiếu", "Hòa", "Hùng", "Hưng", "Khang", "Khánh", "Khoa", "Kiên", "Lâm", "Long", "Nam", "Nghĩa", "Ngọc", "Phong", "Phúc", "Quân", "Quang", "Quốc", "Sơn", "Thái", "Thành", "Thiên", "Thịnh", "Tiến", "Toàn", "Trí", "Trọng", "Trung", "Tuấn", "Tùng", "Vinh", "Việt", "Vy", "Yến", "Thảo", "Hương", "Trang", "Linh", "Nhung", "Mai", "Lan", "Hoa", "Nguyệt", "Nga"]
        
        xa_phuong = ["Phường Âu Cơ", "Phường Nông Trang", "Phường Tân Hòa", "Phường Gia Cẩm", "Phường Tiên Cát", "Phường Thanh Miếu", "Phường Dữu Lâu", "Phường Vân Phú"]
        nghe_nghiep = ["Cơ quan nhà nước", "Lao động tự do", "Doanh nghiệp tư nhân", "Nông nghiệp", "FDI", "Học sinh/Sinh viên"]
        gioi_tinh = ["Nam", "Nữ"]
        
        # Thêm 20 người giả lập
        for i in range(1, 21):
            cccd = f"0250{random.randint(10000000, 99999999)}"
            ho_ten = f"{random.choice(ho_strs)} {random.choice(dem_strs)} {random.choice(ten_strs)}"
            nam_sinh = random.randint(1970, 2005)
            thang_sinh = random.randint(1, 12)
            ngay_sinh = random.randint(1, 28)
            
            dt = DoiTuong(
                cccd=cccd,
                ho_ten=ho_ten,
                ngay_sinh=datetime(nam_sinh, thang_sinh, ngay_sinh).date(),
                gioi_tinh=random.choice(gioi_tinh),
                dia_chi_tinh="Phú Thọ",
                dia_chi_xa=random.choice(xa_phuong),
                phan_loai_nghe_nghiep=random.choice(nghe_nghiep),
                chi_tiet_nghe_nghiep="Chi tiết công việc...",
                is_draft=False
            )
            db.add(dt)
            
            # Thêm ngẫu nhiên nhân thân
            if random.random() > 0.5:
                nt = NhanThan(
                    cccd=cccd,
                    loai_quan_he="Vợ/Chồng" if nam_sinh < 2000 else "Bố/Mẹ",
                    ho_ten=f"{random.choice(ho_strs)} {random.choice(dem_strs)} {random.choice(ten_strs)}",
                    cccd_nhan_than=f"0250{random.randint(10000000, 99999999)}"
                )
                db.add(nt)
                
            # Thêm ngẫu nhiên phương tiện
            if random.random() > 0.3:
                xe = PhuongTien(
                    cccd=cccd,
                    loai_xe="Xe máy",
                    bien_kiem_soat=f"19{random.choice(['B1', 'F1', 'H1', 'K1'])}-{random.randint(10000, 99999)}",
                    ten_phuong_tien="Honda Wave" if random.random() > 0.5 else "Yamaha Sirius"
                )
                db.add(xe)
                
        db.commit()
        print("Đã tạo thành công 20 dữ liệu mẫu để test!")
        
    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
