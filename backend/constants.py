# -*- coding: utf-8 -*-
"""
Constants cho hệ thống VCFE Database
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

# Danh sách quốc gia chuẩn hóa (đầy đủ hơn)
DANH_SACH_QUOC_GIA = [
    "Việt Nam", "Trung Quốc", "Hàn Quốc", "Nhật Bản", "Đài Loan", "Mỹ", "Pháp", 
    "Anh", "Đức", "Nga", "Lào", "Campuchia", "Thái Lan", "Malaysia", 
    "Singapore", "Indonesia", "Philippines", "Úc", "Canada", "Ý", "Tây Ban Nha",
    "Hà Lan", "Bỉ", "Thụy Sĩ", "Áo", "Thụy Điển", "Na Uy", "Đan Mạch", "Phần Lan",
    "Ba Lan", "Séc", "Hungary", "Slovakia", "Hy Lạp", "Bồ Đào Nha", "Rumani",
    "Bungari", "Ukraine", "Belarus", "Thổ Nhĩ Kỳ", "Israel", "Ả Rập Xê Út",
    "UAE", "Qatar", "Kuwait", "Oman", "Ấn Độ", "Pakistan", "Bangladesh",
    "Sri Lanka", "Kazakhstan", "Uzbekistan", "Mông Cổ", "Triều Tiên",
    "Myanmar", "Brunei", "Đông Timor", "New Zealand", "Brazil", "Argentina",
    "Mexico", "Chile", "Colombia", "Peru", "Nam Phi", "Ai Cập", "Nigeria",
    "Kenya", "Ma-rốc", "Algeria", "Khác"
]

# 54 dân tộc Việt Nam (theo danh mục chính thức)
DANH_SACH_DAN_TOC = [
    "Kinh", "Tày", "Thái", "Mường", "Khmer", "Mông", "Nùng", "Hoa",
    "Dao", "Gia Rai", "Ê Đê", "Ba Na", "Xơ Đăng", "Sán Chay", "Cơ Ho",
    "Chăm", "Sán Dìu", "Hrê", "Ra Glai", "Mnông", "Thổ", "Xtiêng",
    "Khơ Mú", "Bru - Vân Kiều", "Cơ Tu", "Giáy", "Tà Ôi", "Mạ",
    "Giẻ - Triêng", "Co", "Chơ Ro", "Xinh Mun", "Hà Nhì", "Chu Ru",
    "Lào", "La Chí", "La Ha", "Phù Lá", "La Hủ", "Lự", "Lô Lô",
    "Chứt", "Mảng", "Pà Thẻn", "Co Lao", "Cống", "Bố Y", "Si La",
    "Pu Péo", "Brâu", "Rơ Măm", "Ơ Đu", "Ngái", "Khác",
]

# Tôn giáo tại Việt Nam (theo Ban Tôn giáo Chính phủ)
DANH_SACH_TON_GIAO = [
    "Không", "Phật giáo", "Công giáo", "Tin Lành", "Hồi giáo",
    "Cao Đài", "Hòa Hảo", "Tịnh độ cư sĩ Phật hội", "Khác",
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

# ── Aliases dùng trong routes / templates ────────────────────
TINH_THANH = TINH_OPTIONS
XA_PHUONG = DANH_SACH_XA_PHU_THO
LOAI_LIEN_HE = LOAI_LIEN_HE_OPTIONS
LOAI_QUAN_HE = [
    "Bố", "Mẹ", "Vợ", "Chồng", "Con trai", "Con gái",
    "Anh", "Chị", "Em trai", "Em gái", "Bạn bè", "Đồng nghiệp", "Khác",
]
NGAN_HANG = DANH_SACH_NGAN_HANG
LOAI_XE = LOAI_XE_OPTIONS
LOAI_TAI_LIEU = LOAI_TAI_LIEU_OPTIONS
PHAN_LOAI_NGHE_NGHIEP = PHAN_LOAI_NGHE_NGHIEP_OPTIONS
DAN_TOC = DANH_SACH_DAN_TOC
TON_GIAO = DANH_SACH_TON_GIAO


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

