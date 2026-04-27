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

DANH_SACH_QUOC_GIA = [
    "Ac-mê-ni-a", "Ai Cập", "Ai-rơ-len", "Ai-xơ-len", "An-ba-ni", "An-giê-ri", "An-ti-goa và Bác-bu-đa", "An-đô-ra", "Ap-ga-ni-xtan", "Ba Lan", "Ba-ha-ma", "Ba-ren", "Bra-xin", "Bru-nây", "Bu-tan", "Bun-ga-ri", "Bác-ba-đốt", "Bê-la-rút", "Bê-li-xê", "Bê-nanh", "Bô-li-vi-a", "Bô-xni-a và Héc-xê-gô-vi-na", "Băng-la-đét", "Bỉ", "Bốt-xoa-na", "Bồ Đào Nha", "Bờ Biển Ngà", "CH Hàn Quốc", "CH Hồi giáo I-ran", "CH Liên bang Đức", "CH Trung Phi", "CH Đô-mi-ni-ca", "CHDCND Lào", "CHDCND Triều Tiên", "Ca-dắc-xtan", "Ca-mơ-run", "Ca-na-da", "Ca-ta", "Chi-lê", "Crô-a-ti-a", "Cu Ba", "Các Tiểu vương quốc Ả Rập Thống nhất", "Cáp-ve", "Cô-lôm-bi-a", "Cô-mô-rô", "Cô-oét", "Công dân các địa phận thuộc Vương quốc liên hiệp Anh", "Công-gô (CH)", "Công-gô (CHDC)", "Căm-pu-chia", "Cư-rơ-gư-xtan", "Cốt-ri-ca", "Cộng hoà Séc", "Dim-ba-bu-ê", "Dăm-bi-a", "E-xtô-ni-a", "En Xal-va-đo", "Ga-bông", "Ga-na", "Gi-bu-ti", "Giam-mai-ca", "Goa-tê-ma-la", "Gru-di-a", "Grê-na-đa", "Gui-nê", "Gui-nê Bích-xao", "Guy-a-na", "Găm-bi-a", "Hai-ti", "Hoa Kỳ", "Hung-ga-ri", "Hy Lạp", "Hà Lan", "Hôn-đu-rát", "Hồng Kông (Trung Quốc)", "I-rắc", "I-ta-li-a", "I-xra-en", "In-đô-nê-xi-a", "Joc-đan", "Ki-ri-ba-ti", "Kê-ni-a", "Li-bi", "Li-bê-ri-a", "Li-băng", "Liên bang Nga", "Luyx-xâm-bua", "Lát-vi-a", "Lích-ten-xtên", "Lít-va", "Lô-xô-tô", "Ma lai", "Ma-cao (Trung Quốc)", "Ma-la-uy", "Ma-li", "Ma-rốc", "Ma-đa-gát-xca", "Man-ta", "Man-đi-vơ", "Mi-an-ma", "Mi-crô-nê-xi-a", "Mê-xi-cô", "Mô-dăm-bích", "Mô-na-cô", "Mô-ri-ta-ni", "Mô-ri-xơ", "Môn-tê-nê-grô", "Môn-đô-va", "Mông Cổ", "Na Uy", "Nam Phi", "Nam Xu-đăng", "Nam-mi-bi-a", "Người được Liên hiệp Anh bảo hộ", "Nhật Bản", "Ni-ca-ra-goa", "Ni-giê", "Ni-giê-ri-a", "Niu Di-lân", "Nâu-ru", "Nê-pan", "Pa-ki-xtan", "Pa-lau", "Pa-lét-tin", "Pa-na-ma", "Pa-pua Niu Gui-nê", "Pa-ra-goay", "Phi-líp-pin", "Pháp", "Phần Lan", "Pê-ru", "Quần đảo Man-vi-na", "Quần đảo Mác-san", "Quần đảo Xô-lô-môn", "Ru-an-đa", "Ru-ma-ni", "Ta-gi-ki-xtan", "Tan-da-ni-a", "Thuỵ Sĩ", "Thuỵ Điển", "Thái Lan", "Thổ Nhĩ Kỳ", "Tri-ni-đát và Tô-ba-gô", "Trung Quốc", "Trung Quốc (Đài Loan)", "Tu-va-lu", "Tuy-ni-di", "Tuốc-mê-ni-xtan", "Tây Ban Nha", "Tô-gô", "Tông-ga", "U-crai-na", "U-dơ-bê-ki-xtan", "U-gan-da", "U-ru-goay", "Va-nu-a-tu", "Va-ti-căng", "Việt Nam", "Vê-nê-xu-ê-la", "Vương quốc Anh và Bắc Ai len", "Xa-mô-a", "Xan Ma-ri-nô", "Xanh Kít và Nê-vi", "Xanh Lu-xi-a", "Xanh Vin-xen và Grê-na-din", "Xao Tô-mê và Prin-xi-pê", "Xi-ê-ra Nê-ôn", "Xin-ga-po", "Xlô-va-ki-a", "Xlô-ven-ni-a", "Xoa-di-len", "Xri-Lan-ca", "Xu-ri-nam", "Xu-đăng", "Xây-sen", "Xéc-bi-a", "Xê-nê-gan", "Xô-ma-li", "Y-ê-men", "Ác-hen-ti-na", "Áo", "Ê-cu-a-đo", "Ê-ri-tơ-ri-a", "Ê-ti-ô-pi-a", "Ô-man", "Ô-xtrây-li-a", "Ăng-gô-la", "Đan Mạch", "Đô-mi-ni-ca", "Đông Ti-mo", "Đảo Síp", "Ả-rập Xê-út", "Ấn Độ"
]
