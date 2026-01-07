# -*- coding: utf-8 -*-
"""
Constants cho hệ thống Security Profile 360
Danh sách 105 đơn vị hành chính cấp xã/phường tỉnh Phú Thọ
(Sau sáp nhập ngày 01/7/2025)
"""

# Danh sách 15 phường
DANH_SACH_PHUONG = [
    "Phường Âu Cơ",
    "Phường Dân Chủ",
    "Phường Hòa Bình",
    "Phường Kỳ Sơn",
    "Phường Nông Trang",
    "Phường Phong Châu",
    "Phường Phú Thọ",
    "Phường Thanh Miếu",
    "Phường Thống Nhất",
    "Phường Vân Phú",
    "Phường Việt Trì",
    "Phường Vĩnh Phúc",
    "Phường Vĩnh Yên",
    "Phường Phúc Yên",
    "Phường Thanh Sơn",
]

# Danh sách 90 xã
DANH_SACH_XA = [
    "Xã Bản Nguyên",
    "Xã Bình Phú",
    "Xã Bằng Luân",
    "Xã Cẩm Khê",
    "Xã Chân Mộng",
    "Xã Chí Đám",
    "Xã Chí Tiên",
    "Xã Cự Đồng",
    "Xã Đào Xá",
    "Xã Đoan Hùng",
    "Xã Đông Thành",
    "Xã Đồng Lương",
    "Xã Hạ Hòa",
    "Xã Hoàng An",
    "Xã Hoàng Cương",
    "Xã Hợp Kim",
    "Xã Hương Cần",
    "Xã Hy Cương",
    "Xã Khả Cửu",
    "Xã Kim Bôi",
    "Xã Lai Đồng",
    "Xã Lâm Thao",
    "Xã Lập Thạch",
    "Xã Liên Hòa",
    "Xã Liên Minh",
    "Xã Liên Sơn",
    "Xã Long Cốc",
    "Xã Mai Châu",
    "Xã Mai Hạ",
    "Xã Minh Đài",
    "Xã Minh Hòa",
    "Xã Mường Bi",
    "Xã Mường Động",
    "Xã Mường Hoa",
    "Xã Mường Thàng",
    "Xã Mường Vang",
    "Xã Ngọc Sơn",
    "Xã Nguyệt Đức",
    "Xã Nhân Nghĩa",
    "Xã Pà Cò",
    "Xã Phù Ninh",
    "Xã Phú Mỹ",
    "Xã Quảng Yên",
    "Xã Quy Đức",
    "Xã Quyết Thắng",
    "Xã Sông Lô",
    "Xã Sơn Đông",
    "Xã Sơn Lương",
    "Xã Tam Hồng",
    "Xã Tam Nông",
    "Xã Tam Sơn",
    "Xã Tân Lạc",
    "Xã Tân Mai",
    "Xã Tân Pheo",
    "Xã Tân Sơn",
    "Xã Tây Cốc",
    "Xã Thái Hòa",
    "Xã Thanh Ba",
    "Xã Thanh Thủy",
    "Xã Thịnh Minh",
    "Xã Thu Cúc",
    "Xã Thổ Tang",
    "Xã Tiên Lương",
    "Xã Tiên Lữ",
    "Xã Tiền Phong",
    "Xã Toàn Thắng",
    "Xã Trạm Thản",
    "Xã Trung Sơn",
    "Xã Tu Vũ",
    "Xã Vân Bán",
    "Xã Vân Sơn",
    "Xã Văn Lang",
    "Xã Văn Miếu",
    "Xã Vĩnh An",
    "Xã Vĩnh Chân",
    "Xã Vĩnh Hưng",
    "Xã Vĩnh Phú",
    "Xã Vĩnh Thành",
    "Xã Vĩnh Tường",
    "Xã Xuân Áng",
    "Xã Xuân Đài",
    "Xã Xuân Lãng",
    "Xã Xuân Lũng",
    "Xã Xuân Viên",
    "Xã Yên Kỳ",
    "Xã Yên Lạc",
    "Xã Yên Lãng",
    "Xã Yên Phú",
    "Xã Yên Sơn",
    "Xã Yên Trị",
]

# Danh sách đầy đủ 105 đơn vị hành chính cấp xã/phường (dùng cho dropdown)
DANH_SACH_XA_PHU_THO = DANH_SACH_PHUONG + DANH_SACH_XA

# Các lựa chọn cho trường giới tính
GIOI_TINH_OPTIONS = ["Nam", "Nữ"]

# Các lựa chọn cho trường tỉnh
TINH_OPTIONS = ["Phú Thọ", "Khác"]

# Các lựa chọn cho phân loại nghề nghiệp
PHAN_LOAI_NGHE_NGHIEP_OPTIONS = ["Cơ quan nhà nước", "Lao động tự do"]

# Các loại liên hệ
LOAI_LIEN_HE_OPTIONS = ["SĐT", "Email", "Facebook", "Zalo", "Telegram"]

# Các loại phương tiện
LOAI_XE_OPTIONS = ["Ô tô", "Xe máy"]

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
LOAI_HINH_TO_CHUC_NN = ["FDI", "NGO", "Đại sứ quán", "Lãnh sự quán", "Tổ chức quốc tế", "Khác"]

# Hình thức du học/công tác
HINH_THUC_DU_HOC = ["Du học", "Công tác", "Thuê lao động", "Thăm thân", "Khác"]

# Kết quả xác minh
KET_QUA_XAC_MINH = ["Đủ điều kiện", "Không đủ điều kiện", "Đang xác minh", "Chưa có kết quả", "Khác"]

# Ngân hàng phổ biến
DANH_SACH_NGAN_HANG = [
    "Vietcombank", "Vietinbank", "BIDV", "Agribank", "Techcombank", 
    "MB Bank", "ACB", "Sacombank", "VPBank", "TPBank", "HDBank",
    "SHB", "OCB", "VIB", "MSB", "Eximbank", "LienVietPostBank", "Khác"
]
