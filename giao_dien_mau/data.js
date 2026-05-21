// Mock data for VCFE prototype
// Realistic Phú Thọ context, fictional names

const XA_PHU_THO = [
  "Phường Vân Phú", "Phường Tiên Cát", "Phường Gia Cẩm", "Phường Nông Trang",
  "Xã Hùng Sơn", "Xã Hy Cương", "Xã Chu Hóa", "Xã Phượng Lâu",
  "Thị trấn Thanh Sơn", "Xã Tân Lập", "Xã Yên Lãng", "Xã Cự Thắng",
  "Thị trấn Đoan Hùng", "Xã Hữu Đô", "Xã Vân Du", "Xã Tiêu Sơn",
  "Thị trấn Cẩm Khê", "Xã Tuy Lộc", "Thị trấn Tam Nông", "Xã Hương Nộn",
  "Thị trấn Lâm Thao", "Xã Cao Xá", "Xã Vĩnh Lại",
];

const NGHE_NGHIEP = [
  "Cơ quan nhà nước","Tự kinh doanh","Doanh nghiệp tư nhân","Nông nghiệp",
  "Doanh nghiệp FDI","Tổ chức phi chính phủ","Học sinh/Sinh viên","Về hưu","Thất nghiệp","Khác"
];

const LOAI_HINH = {
  "Hon_Nhan_NN":         "Kết hôn với người NN",
  "Lam_Viec_NN":         "Làm việc cho TC nước ngoài",
  "Hoc_Tap_Cong_Tac_NN": "Học tập / công tác NN",
  "Vi_Pham_NN":          "Vi phạm pháp luật NN",
  "Xac_Minh":            "Đã xác minh",
};

// ---- Đối tượng (objects under tracking) ----
const DOI_TUONG = [
  {
    cccd: "025198003142", ho_ten: "NGUYỄN THỊ MAI HƯƠNG",
    ngay_sinh: "1989-03-12", gioi_tinh: "Nữ",
    dia_chi_xa: "Phường Vân Phú", dia_chi_tinh: "Phú Thọ",
    nghe: "Doanh nghiệp FDI", chi_tiet_nghe: "Phiên dịch viên — Cty TNHH Hyosung Việt Nam",
    loai_hinh: ["Hon_Nhan_NN", "Xac_Minh"],
    quoc_gia: "Hàn Quốc",
    cap_nhat: "2026-05-04",
    phu_trach: "Trung úy Lê Minh Tuấn",
    ghi_chu: "Kết hôn với Park Joon-ho (sinh 1985, Seoul), đăng ký 2018."
  },
  {
    cccd: "025193002671", ho_ten: "TRẦN VĂN BÁCH",
    ngay_sinh: "1993-08-22", gioi_tinh: "Nam",
    dia_chi_xa: "Xã Hùng Sơn", dia_chi_tinh: "Phú Thọ",
    nghe: "Tự kinh doanh", chi_tiet_nghe: "Chủ shop nhập hàng Đài Loan, sàn TMĐT",
    loai_hinh: ["Lam_Viec_NN"], quoc_gia: "Đài Loan", cap_nhat: "2026-05-12",
    phu_trach: "Thiếu úy Phạm Quỳnh Anh",
  },
  {
    cccd: "025195000485", ho_ten: "ĐỖ THỊ LAN ANH",
    ngay_sinh: "1995-11-04", gioi_tinh: "Nữ",
    dia_chi_xa: "Phường Tiên Cát", dia_chi_tinh: "Phú Thọ",
    nghe: "Học sinh/Sinh viên", chi_tiet_nghe: "Du học tự túc Nhật Bản — Tokyo, 2022",
    loai_hinh: ["Hoc_Tap_Cong_Tac_NN"], quoc_gia: "Nhật Bản", cap_nhat: "2026-05-11",
    phu_trach: "Trung úy Lê Minh Tuấn",
  },
  {
    cccd: "088192004012", ho_ten: "HOÀNG QUỐC KHẢI",
    ngay_sinh: "1992-01-30", gioi_tinh: "Nam",
    dia_chi_xa: "Thị trấn Thanh Sơn", dia_chi_tinh: "Phú Thọ",
    nghe: "Doanh nghiệp tư nhân", chi_tiet_nghe: "Giám đốc Cty CP Khải Nguyên (XNK)",
    loai_hinh: ["Lam_Viec_NN", "Vi_Pham_NN"], quoc_gia: "Trung Quốc", cap_nhat: "2026-05-15",
    phu_trach: "Đại úy Vi Ngọc Phương",
    ghi_chu: "Vi phạm hải quan TQ năm 2023, đã chấp hành xong."
  },
  {
    cccd: "025187003311", ho_ten: "VŨ ĐỨC THẮNG",
    ngay_sinh: "1987-06-18", gioi_tinh: "Nam",
    dia_chi_xa: "Phường Gia Cẩm", dia_chi_tinh: "Phú Thọ",
    nghe: "Doanh nghiệp FDI", chi_tiet_nghe: "Kỹ sư cơ điện — Samsung Display Bắc Ninh",
    loai_hinh: ["Lam_Viec_NN", "Xac_Minh"], quoc_gia: "Hàn Quốc", cap_nhat: "2026-05-09",
    phu_trach: "Thiếu úy Phạm Quỳnh Anh",
  },
  {
    cccd: "025198009127", ho_ten: "LÊ THỊ KIM NGÂN",
    ngay_sinh: "1998-09-25", gioi_tinh: "Nữ",
    dia_chi_xa: "Phường Nông Trang", dia_chi_tinh: "Phú Thọ",
    nghe: "Khác", chi_tiet_nghe: "Lao động tại Đài Loan, hợp đồng 3 năm",
    loai_hinh: ["Lam_Viec_NN"], quoc_gia: "Đài Loan", cap_nhat: "2026-05-14",
    phu_trach: "Trung úy Lê Minh Tuấn",
  },
  {
    cccd: "025191005533", ho_ten: "PHẠM THỊ HỒNG NHUNG",
    ngay_sinh: "1991-12-09", gioi_tinh: "Nữ",
    dia_chi_xa: "Xã Hy Cương", dia_chi_tinh: "Phú Thọ",
    nghe: "Tự kinh doanh", chi_tiet_nghe: "Spa thẩm mỹ, đối tác Hàn Quốc",
    loai_hinh: ["Hon_Nhan_NN"], quoc_gia: "Hàn Quốc", cap_nhat: "2026-04-28",
    phu_trach: "Thiếu úy Phạm Quỳnh Anh",
  },
  {
    cccd: "025190007722", ho_ten: "BÙI VĂN CƯỜNG",
    ngay_sinh: "1990-04-14", gioi_tinh: "Nam",
    dia_chi_xa: "Thị trấn Đoan Hùng", dia_chi_tinh: "Phú Thọ",
    nghe: "Doanh nghiệp tư nhân", chi_tiet_nghe: "Xuất khẩu lao động sang Nhật Bản",
    loai_hinh: ["Lam_Viec_NN"], quoc_gia: "Nhật Bản", cap_nhat: "2026-05-13",
    phu_trach: "Trung úy Lê Minh Tuấn",
  },
  {
    cccd: "025196003845", ho_ten: "NGÔ THỊ THANH HẢI",
    ngay_sinh: "1996-07-02", gioi_tinh: "Nữ",
    dia_chi_xa: "Xã Phượng Lâu", dia_chi_tinh: "Phú Thọ",
    nghe: "Khác", chi_tiet_nghe: "Kết hôn và định cư tại Singapore",
    loai_hinh: ["Hon_Nhan_NN", "Xac_Minh"], quoc_gia: "Singapore", cap_nhat: "2026-05-05",
    phu_trach: "Đại úy Vi Ngọc Phương",
  },
  {
    cccd: "025194001236", ho_ten: "ĐINH NHẬT MINH",
    ngay_sinh: "1994-02-19", gioi_tinh: "Nam",
    dia_chi_xa: "Thị trấn Cẩm Khê", dia_chi_tinh: "Phú Thọ",
    nghe: "Doanh nghiệp FDI", chi_tiet_nghe: "Lập trình viên — Cty Niteco (Thụy Điển)",
    loai_hinh: ["Lam_Viec_NN"], quoc_gia: "Thụy Điển", cap_nhat: "2026-05-10",
    phu_trach: "Thiếu úy Phạm Quỳnh Anh",
  },
  {
    cccd: "025189002098", ho_ten: "TRƯƠNG VĂN HẢI",
    ngay_sinh: "1989-10-08", gioi_tinh: "Nam",
    dia_chi_xa: "Thị trấn Tam Nông", dia_chi_tinh: "Phú Thọ",
    nghe: "Tự kinh doanh", chi_tiet_nghe: "Mở quán ăn tại Sydney, Úc — 2019",
    loai_hinh: ["Lam_Viec_NN", "Xac_Minh"], quoc_gia: "Úc", cap_nhat: "2026-04-30",
    phu_trach: "Trung úy Lê Minh Tuấn",
  },
  {
    cccd: "025199008820", ho_ten: "ĐẶNG THÙY LINH",
    ngay_sinh: "1999-05-21", gioi_tinh: "Nữ",
    dia_chi_xa: "Thị trấn Lâm Thao", dia_chi_tinh: "Phú Thọ",
    nghe: "Học sinh/Sinh viên", chi_tiet_nghe: "Sinh viên ĐH Sungkyunkwan — Seoul",
    loai_hinh: ["Hoc_Tap_Cong_Tac_NN"], quoc_gia: "Hàn Quốc", cap_nhat: "2026-05-16",
    phu_trach: "Thiếu úy Phạm Quỳnh Anh",
  },
];

// Detail data for case 1 (HƯƠNG)
const HO_SO_HUONG = {
  cccd: "025198003142",
  lien_he: [
    { id: 1, loai: "SĐT", gia_tri: "0912 384 590", ghi_chu: "Số dùng chính, Zalo" },
    { id: 2, loai: "SĐT", gia_tri: "+82 10 4928 1024", ghi_chu: "Số Hàn Quốc, dùng khi sang HQ" },
    { id: 3, loai: "Email", gia_tri: "huong.nguyen@hyosung.co.kr", ghi_chu: "Email công ty" },
    { id: 4, loai: "Facebook", gia_tri: "facebook.com/huong.nguyen.parkjh", ghi_chu: "Tài khoản chính" },
    { id: 5, loai: "Zalo", gia_tri: "0912384590", ghi_chu: "" },
  ],
  tai_chinh: [
    { id: 1, ngan_hang: "Vietcombank", so_tk: "0451 0000 384 122", chu_tk: "NGUYEN THI MAI HUONG", ghi_chu: "TK lương — VCB Phú Thọ" },
    { id: 2, ngan_hang: "Shinhan Bank", so_tk: "110-501-928374", chu_tk: "NGUYEN THI MAI HUONG", ghi_chu: "TK ngoại tệ KRW" },
    { id: 3, ngan_hang: "Techcombank", so_tk: "1903 8420 1190", chu_tk: "NGUYEN THI MAI HUONG", ghi_chu: "TK sinh hoạt gia đình" },
  ],
  phuong_tien: [
    { id: 1, loai_xe: "Ô tô", bks: "19A-238.40", ten: "Hyundai Elantra 2022, màu trắng", ghi_chu: "Xe gia đình" },
    { id: 2, loai_xe: "Xe máy", bks: "19E1-082.34", ten: "Honda SH 150i, màu đen", ghi_chu: "" },
  ],
  nhan_than: [
    { id: 1, quan_he: "Chồng (NN)", ho_ten: "PARK JOON-HO", cccd: "Hộ chiếu HQ M81928374", ngay_sinh: "1985-04-22", gioi: "Nam", noi_o: "Seoul, Hàn Quốc / Phú Thọ" },
    { id: 2, quan_he: "Con", ho_ten: "PARK MIN-WOO (KIM JUN)", cccd: "—", ngay_sinh: "2019-08-14", gioi: "Nam", noi_o: "Phú Thọ" },
    { id: 3, quan_he: "Bố", ho_ten: "NGUYỄN VĂN ĐÔ", cccd: "025162001847", ngay_sinh: "1962-01-10", gioi: "Nam", noi_o: "Phường Vân Phú, Phú Thọ" },
    { id: 4, quan_he: "Mẹ", ho_ten: "TRẦN THỊ MIÊN", cccd: "025165003291", ngay_sinh: "1965-09-03", gioi: "Nữ", noi_o: "Phường Vân Phú, Phú Thọ" },
    { id: 5, quan_he: "Em ruột", ho_ten: "NGUYỄN VĂN TRƯỜNG", cccd: "025195006182", ngay_sinh: "1995-06-30", gioi: "Nam", noi_o: "Hà Nội" },
  ],
  ho_so_dac_thu: [
    { id: 1, loai: "Hon_Nhan_NN", noi_dung: "Đăng ký kết hôn với Park Joon-ho (quốc tịch Hàn Quốc) tại Sở Tư pháp Phú Thọ ngày 14/06/2018. Đã có 01 con chung.", cap_nhat: "2024-11-12" },
    { id: 2, loai: "Xac_Minh", noi_dung: "Đã xác minh nhân thân và lý lịch tư pháp của Park Joon-ho qua Đại sứ quán Hàn Quốc. Không có tiền án tiền sự.", cap_nhat: "2025-02-08" },
  ],
  tai_lieu: [
    { id: 1, ten: "GiayKetHon_NguyenHuong_ParkJH.pdf", loai: "Giấy tờ pháp lý", size: "1.2 MB", ngay: "2024-11-12" },
    { id: 2, ten: "HoChieuHQ_ParkJH_scan.jpg", loai: "Ảnh tài liệu", size: "640 KB", ngay: "2024-11-12" },
    { id: 3, ten: "GiayKhaiSinh_ParkMinWoo.pdf", loai: "Giấy tờ pháp lý", size: "880 KB", ngay: "2024-11-12" },
    { id: 4, ten: "ThongTinTaiKhoanShinhan.pdf", loai: "Tài chính", size: "320 KB", ngay: "2025-01-04" },
  ],
  qua_trinh: [
    { id: 1, thoi_gian: "06/2018 — nay", noi_dung: "Đăng ký kết hôn và sinh sống tại Phú Thọ. Đi lại Hàn Quốc 2–3 lần/năm." },
    { id: 2, thoi_gian: "09/2019 — nay", noi_dung: "Công tác tại Cty TNHH Hyosung Việt Nam (chi nhánh Bắc Ninh), vị trí Phiên dịch viên." },
    { id: 3, thoi_gian: "02/2025", noi_dung: "Hoàn tất hồ sơ xác minh lý lịch tư pháp chồng người Hàn Quốc qua Đại sứ quán." },
  ],
};

// Audit log entries
const AUDIT_LOG = [
  { id: 1, when: "2026-05-16 14:32:08", who: "phuongvi", bang: "doi_tuong", hd: "UPDATE", khoa: "025198003142", ip: "192.168.1.42" },
  { id: 2, when: "2026-05-16 14:18:51", who: "tuanle",   bang: "tai_lieu",  hd: "INSERT", khoa: "id=128", ip: "192.168.1.18" },
  { id: 3, when: "2026-05-16 14:02:22", who: "tuanle",   bang: "lien_he",   hd: "INSERT", khoa: "id=472", ip: "192.168.1.18" },
  { id: 4, when: "2026-05-16 13:48:01", who: "anhph",    bang: "doi_tuong", hd: "INSERT", khoa: "025199008820", ip: "192.168.1.27" },
  { id: 5, when: "2026-05-16 13:20:45", who: "anhph",    bang: "nhan_than", hd: "UPDATE", khoa: "id=901", ip: "192.168.1.27" },
  { id: 6, when: "2026-05-16 12:55:09", who: "phuongvi", bang: "tai_chinh", hd: "INSERT", khoa: "id=320", ip: "192.168.1.42" },
  { id: 7, when: "2026-05-16 11:42:18", who: "tuanle",   bang: "doi_tuong", hd: "UPDATE", khoa: "025194001236", ip: "192.168.1.18" },
  { id: 8, when: "2026-05-16 10:30:02", who: "anhph",    bang: "phuong_tien", hd: "DELETE", khoa: "id=58", ip: "192.168.1.27" },
  { id: 9, when: "2026-05-16 09:18:42", who: "phuongvi", bang: "users",     hd: "UPDATE", khoa: "id=4", ip: "192.168.1.42" },
  { id: 10, when: "2026-05-16 08:42:11", who: "system",  bang: "audit_log", hd: "BACKUP", khoa: "—", ip: "127.0.0.1" },
];

// Users
const USERS = [
  { id: 1, username: "phuongvi", ho_ten: "Đại úy Vi Ngọc Phương", role: "super_admin", active: true,  last: "2026-05-16 14:32" },
  { id: 2, username: "tuanle",   ho_ten: "Trung úy Lê Minh Tuấn",  role: "user",        active: true,  last: "2026-05-16 14:18" },
  { id: 3, username: "anhph",    ho_ten: "Thiếu úy Phạm Quỳnh Anh",role: "user",        active: true,  last: "2026-05-16 13:48" },
  { id: 4, username: "thangvn",  ho_ten: "Đại úy Vương Ngọc Thắng",role: "user",        active: true,  last: "2026-05-15 17:02" },
  { id: 5, username: "huongnt",  ho_ten: "Thượng úy Nguyễn Thu Hương",role: "user",     active: false, last: "2026-04-22 09:14" },
];

// Activity sparkline (last 30 days, operations per day)
const ACTIVITY_30D = [12,8,15,22,18,14,9,11,24,31,28,22,19,15,12,18,26,30,34,28,21,17,23,29,32,38,42,35,27,31];

// Country breakdown
const QUOC_GIA_STATS = [
  { name: "Hàn Quốc",   count: 142, pct: 32 },
  { name: "Trung Quốc", count: 98,  pct: 22 },
  { name: "Đài Loan",   count: 76,  pct: 17 },
  { name: "Nhật Bản",   count: 58,  pct: 13 },
  { name: "Mỹ",         count: 31,  pct: 7  },
  { name: "Singapore",  count: 18,  pct: 4  },
  { name: "Khác",       count: 23,  pct: 5  },
];

const LOAI_HINH_STATS = [
  { code: "Hon_Nhan_NN",         name: "Kết hôn NN",           count: 168 },
  { code: "Lam_Viec_NN",         name: "Làm việc cho TC NN",   count: 142 },
  { code: "Hoc_Tap_Cong_Tac_NN", name: "Học tập / công tác NN",count: 84  },
  { code: "Vi_Pham_NN",          name: "Vi phạm pháp luật NN", count: 12  },
  { code: "Xac_Minh",            name: "Đã xác minh",          count: 196 },
];

window.VCFE = {
  DOI_TUONG, HO_SO_HUONG, AUDIT_LOG, USERS,
  ACTIVITY_30D, QUOC_GIA_STATS, LOAI_HINH_STATS,
  LOAI_HINH, XA_PHU_THO, NGHE_NGHIEP,
};
