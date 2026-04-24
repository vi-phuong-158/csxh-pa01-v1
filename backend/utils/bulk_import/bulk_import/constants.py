# -*- coding: utf-8 -*-

# Định nghĩa cấu trúc cột cho từng loại CSXH
CSXH_TEMPLATES = {
    "Hon_Nhan_NN": {
        "name": "Hôn nhân với người nước ngoài",
        "headers": ["CCCD (*)", "Quốc tịch người nước ngoài (*)", "Họ tên người nước ngoài (*)",
                    "Năm kết hôn", "Nơi đăng ký kết hôn", "Tình trạng hiện tại",
                    "Địa chỉ hiện tại", "Ghi chú"],
        "sample": ["001234567890", "Trung Quốc", "WANG Xiaoming",
                   "2020", "UBND TP Việt Trì", "Đang chung sống",
                   "Xã Thanh Ba, huyện Thanh Ba, Phú Thọ", "Đang theo dõi"]
    },
    "Lam_Viec_NN": {
        "name": "Làm việc cho tổ chức nước ngoài",
        "headers": ["CCCD (*)", "Tên tổ chức (*)", "Quốc gia gốc của tổ chức (*)",
                    "Loại hình (FDI/NGO/Khác)", "Vị trí công việc",
                    "Năm bắt đầu", "Năm kết thúc", "Địa chỉ làm việc", "Ghi chú"],
        "sample": ["001234567890", "Samsung Electronics Vietnam", "Hàn Quốc",
                   "FDI", "Kỹ sư phần mềm",
                   "2018", "2023", "KCN Yên Phong, Bắc Ninh", ""]
    },
    "Hoc_Tap_Cong_Tac_NN": {
        "name": "Du học - Công tác nước ngoài",
        "headers": ["CCCD (*)", "Quốc gia (*)", "Tên trường/Tổ chức (*)",
                    "Hình thức (Du học/Công tác/Thuê lao động)", "Chuyên ngành/Công việc",
                    "Năm đi", "Năm về", "Nguồn tài trợ", "Ghi chú"],
        "sample": ["001234567890", "Nhật Bản", "Đại học Tokyo",
                   "Du học", "Thạc sĩ CNTT",
                   "2015", "2019", "Học bổng MEXT", ""]
    },
    "Vi_Pham_NN": {
        "name": "Vi phạm pháp luật ở nước ngoài",
        "headers": ["CCCD (*)", "Quốc gia xảy ra vi phạm (*)", "Năm vi phạm (*)",
                    "Loại vi phạm", "Nội dung chi tiết",
                    "Hình thức xử lý", "Tình trạng hiện tại", "Ghi chú"],
        "sample": ["001234567890", "Đài Loan", "2014",
                   "Cư trú bất hợp pháp", "Ở quá hạn visa 30 ngày",
                   "Trục xuất", "Đã về nước", ""]
    },
    "Xac_Minh": {
        "name": "Đã từng được xác minh",
        "headers": ["CCCD (*)", "Ngày đề nghị xác minh (*)", "Cơ quan đề nghị (*)",
                    "Nội dung xác minh", "Cơ quan thực hiện",
                    "Ngày hoàn thành", "Kết quả", "Ghi chú"],
        "sample": ["001234567890", "15/01/2024", "Sở Công thương",
                   "Xác minh lý lịch để bổ nhiệm", "PA01",
                   "30/01/2024", "Đủ điều kiện", ""]
    }
}

# Cấu hình cho các loại dữ liệu nhập liệu khác
TEMPLATE_DEFINITIONS = {
    "doi_tuong": {
        "name": "Thông tin đối tượng",
        "headers": ["CCCD (*)", "Họ và tên (*)", "Ngày sinh (dd/mm/yyyy)",
                    "Giới tính", "Tỉnh/TP", "Xã/Phường",
                    "Phân loại nghề nghiệp", "Chi tiết nơi làm việc", "Ghi chú chung"],
        "sample": ["001234567890", "Nguyễn Văn A", "01/01/1990", "Nam",
                   "Phú Thọ", "Phường Thanh Miếu", "Cơ quan nhà nước",
                   "Công an tỉnh Phú Thọ", "Ghi chú mẫu"]
    },
    "lien_he": {
        "name": "Thông tin liên hệ",
        "headers": ["CCCD (*)", "Loại liên hệ", "Giá trị (*)", "Ghi chú"],
        "sample": ["001234567890", "Số điện thoại", "0912345678", "SĐT chính"]
    },
    "than_nhan": {  # Mới thêm theo yêu cầu
        "name": "Thân nhân",
        "headers": ["CCCD (*)", "Họ tên thân nhân", "Quan hệ", "Năm sinh",
                    "Nghề nghiệp/Nơi làm việc", "Địa chỉ", "Ghi chú"],
        "sample": ["001234567890", "Nguyễn Văn B", "Bố đẻ", "1960",
                   "Hưu trí", "Việt Trì, Phú Thọ", ""]
    },
    "tai_chinh": {
        "name": "Tài chính & Ngân hàng",
        "headers": ["CCCD (*)", "Ngân hàng", "Số tài khoản (*)", "Chủ tài khoản", "Ghi chú"],
        "sample": ["001234567890", "Vietcombank", "1234567890123", "NGUYEN VAN A", "TK chính"]
    },
    "phuong_tien": {
        "name": "Phương tiện đí lại",
        "headers": ["CCCD (*)", "Loại xe", "Biển kiểm soát (*)", "Tên phương tiện", "Ghi chú"],
        "sample": ["001234567890", "Ô tô", "19A-12345", "Toyota Vios 2022", "Xe cá nhân"]
    },
    "qua_trinh_hoat_dong": {  # Mới thêm
        "name": "Quá trình hoạt động",
        "headers": ["CCCD (*)", "Thời gian (từ năm-đến năm)", "Nội dung hoạt động", "Ghi chú"],
        "sample": ["001234567890", "2010-2015", "Học sinh trường THPT Chuyên Hùng Vương", ""]
    }
}
