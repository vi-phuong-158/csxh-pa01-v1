# backend/utils/validators.py
"""
Tập tiện ích validate đầu vào tập trung — phục vụ defense-in-depth
cho các thao tác filesystem, lưu DB, render HTML.

Bao quát:
    - validate_cccd        : chống Path Traversal qua tham số CCCD trên URL.
    - sanitize_filename    : chuẩn hoá tên file gốc trước khi lưu DB / render.
    - detect_mime          : nhận diện MIME type từ "magic bytes" (không tin
                              vào phần mở rộng do client gửi lên).
    - validate_upload_file : helper async kiểm tra cùng lúc dung lượng + MIME
                              + sanitize tên file của 1 UploadFile.

Tất cả lỗi được bọc thành HTTPException với status code thích hợp để
FastAPI trả response JSON/HTML chuẩn — không leak stack trace ra client.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional

from fastapi import HTTPException, UploadFile

# ============================================================================
# F-18: Tập trung danh sách KEY nhạy cảm cần REDACT trước khi log
# ============================================================================
# Bao gồm cả các bí danh phổ biến của input form. So sánh case-insensitive.
SENSITIVE_LOG_KEYS: frozenset[str] = frozenset({
    "password", "password_hash",
    "new_password", "confirm_password", "current_password", "old_password",
    "_csrf", "csrf_token", "csrf",
    "token", "secret", "secret_key",
    "session_token",
    "db_password", "admin_password",
    "authorization", "cookie", "set-cookie",
})


def redact_sensitive(d) -> dict:
    """
    Trả về bản copy của dict với các key nhạy cảm được thay bằng "***REDACTED***".
    KHÔNG sửa dict gốc. KHÔNG thực hiện đệ quy (audit log không lồng dict).

    Đầu vào không phải dict -> trả về str(d) tránh crash; nếu cần đệ quy
    cho cấu trúc lồng nhau, mở rộng thêm tại đây.
    """
    if not isinstance(d, dict):
        return d
    return {
        k: ("***REDACTED***" if str(k).lower() in SENSITIVE_LOG_KEYS else v)
        for k, v in d.items()
    }


# ============================================================================
# F-04: Validate CCCD / CMND
# ============================================================================
# - CCCD mẫu mới: ĐÚNG 12 chữ số.
# - CMND mẫu cũ : ĐÚNG 9 chữ số (vẫn còn dùng tới hết vòng đời).
# - KHÔNG cho phép bất kỳ ký tự nào khác (kể cả space, dot, slash).
#   -> Triệt tiêu hoàn toàn nguy cơ Path Traversal qua URL ".../profile/../etc"
_CCCD_RE = re.compile(r"^(?:\d{9}|\d{12})$")


def validate_cccd(cccd: str) -> str:
    """
    Đảm bảo `cccd` chỉ gồm 9 hoặc 12 chữ số. Nếu không hợp lệ -> HTTP 400.

    Trả về chính chuỗi đã được kiểm tra (đồng nhất kiểu dữ liệu, tiện cho
    kiểu sử dụng `cccd = validate_cccd(cccd)` ở đầu handler).
    """
    if not isinstance(cccd, str) or not _CCCD_RE.fullmatch(cccd):
        # Tuyệt đối KHÔNG echo lại giá trị xấu vào message để tránh
        # phản chiếu XSS qua trang lỗi mặc định.
        raise HTTPException(
            status_code=400,
            detail="Mã định danh (CCCD/CMND) không hợp lệ — phải đúng 9 hoặc 12 chữ số.",
        )
    return cccd


# Dùng làm FastAPI Dependency cho gọn, ví dụ:
#     def view(cccd: str = Depends(validated_cccd)): ...
# FastAPI sẽ tự lấy `cccd` từ path param/query vì cùng tên tham số.
def validated_cccd(cccd: str) -> str:
    return validate_cccd(cccd)


# ============================================================================
# F-09: Validate `next` URL chống Open Redirect
# ============================================================================
def safe_next_url(value: Optional[str], default: str = "/dashboard") -> str:
    """
    Trả về 1 đường dẫn ĐÃ VALIDATE để dùng trong RedirectResponse.

    Chấp nhận:
        - Bắt đầu bằng "/" (path relative cùng origin)
        - KHÔNG có ký tự xuống dòng / NUL (chống header injection)
        - KHÔNG dạng "//evil.com/x" (protocol-relative URL — trình duyệt
          coi như absolute, dẫn người dùng ra domain khác)
        - KHÔNG có scheme "://" (http:, javascript:, data: ...)

    Bất cứ giá trị nào không thoả -> dùng `default`.

    Đặc biệt quan trọng cho hệ thống offline: dù không có Internet,
    attacker có thể chèn `?next=javascript:fetch("file:///etc/passwd")`
    để chạy XSS trong context cán bộ ngay sau khi đăng nhập.
    """
    if not value or not isinstance(value, str):
        return default

    # Strip whitespace 2 đầu, không cho phép xuống dòng / NUL
    if any(c in value for c in "\r\n\x00"):
        return default

    # Phải bắt đầu bằng "/" và không phải "//" (protocol-relative)
    if not value.startswith("/") or value.startswith("//"):
        return default

    # Cấm scheme dù core đã chặn ở trên
    if "://" in value:
        return default

    # Backslash bị Windows browser ngầm hiểu là "/"
    if "\\" in value:
        return default

    return value


# ============================================================================
# Sanitize filename — chống XSS, path traversal khi render lại tên file gốc
# ============================================================================
# Chỉ giữ: chữ cái Latin/Việt, chữ số, dấu chấm, gạch dưới, gạch ngang, space.
# Mọi ký tự khác (kể cả /, \, control char) đổi thành "_".
_SAFE_NAME_RE = re.compile(
    r"[^A-Za-z0-9 ._\-"
    r"À-ɏ"   # Latin Extended-A/B (chứa các ký tự Việt cơ bản)
    r"Ḁ-ỿ"   # Latin Extended Additional (đầy đủ tiếng Việt)
    r"]"
)


def sanitize_filename(name: Optional[str], max_len: int = 200, fallback: str = "untitled") -> str:
    """
    Làm sạch tên file gốc do client gửi lên, dùng để LƯU DB và HIỂN THỊ lại.

    Quy trình:
        1) Nếu rỗng -> dùng `fallback`.
        2) Bỏ mọi component đường dẫn (vd. "..\\evil\\a.txt" -> "a.txt").
        3) NFC-normalize Unicode để gộp các tổ hợp dấu Việt (chống homoglyph).
        4) Bỏ ký tự control + ký tự không nằm trong whitelist.
        5) Cắt bớt nếu vượt quá `max_len`, BẢO TOÀN phần mở rộng.
        6) Bỏ dấu chấm đầu để chặn file ẩn (".htaccess" v.v.).

    Trả về tên file sạch, an toàn để lưu/hiển thị.
    """
    if not name or not isinstance(name, str):
        return fallback

    # 2) chỉ giữ phần basename (basename của Windows '\\' hoặc POSIX '/')
    name = name.replace("\\", "/").rsplit("/", 1)[-1].strip()

    # 3) chuẩn hoá Unicode về NFC để 1 ký tự Việt = 1 codepoint
    name = unicodedata.normalize("NFC", name)

    # 4a) loại bỏ control character (U+0000..U+001F, U+007F..U+009F)
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C"))

    # 4b) thay ký tự ngoài whitelist bằng '_'
    name = _SAFE_NAME_RE.sub("_", name)

    # 6) bỏ dấu chấm đầu (file ẩn)
    name = name.lstrip(".")

    # 5) cắt độ dài, giữ phần extension cuối
    if len(name) > max_len:
        if "." in name:
            stem, ext = name.rsplit(".", 1)
            ext = ext[:20]  # extension siêu dài cũng cắt
            keep = max_len - len(ext) - 1
            name = (stem[:keep] + "." + ext) if keep > 0 else ext
        else:
            name = name[:max_len]

    return name or fallback


# ============================================================================
# F-08: Nhận diện MIME thực tế từ magic bytes (không tin extension)
# ============================================================================
# Các "chữ ký" magic bytes tham chiếu IANA / Wikipedia "List of file signatures".
# Mục tiêu: chặn vụ "đặt ten.png cho file PHP/exe rồi upload".
def detect_mime(buf: bytes) -> Optional[str]:
    """
    Nhận diện MIME type từ vài byte đầu file. Trả None nếu không khớp.

    Chỉ cover các định dạng được phép trong dự án: ảnh & tài liệu công vụ.
    Bổ sung định dạng mới -> thêm vào đây + cập nhật allowlist nơi gọi.
    """
    if not buf:
        return None

    # JPEG: FF D8 FF
    if buf.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if buf.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # WEBP: "RIFF" .... "WEBP"
    if len(buf) >= 12 and buf.startswith(b"RIFF") and buf[8:12] == b"WEBP":
        return "image/webp"

    # PDF: %PDF-
    if buf.startswith(b"%PDF-"):
        return "application/pdf"

    # MS Compound (.doc cũ): D0 CF 11 E0 A1 B1 1A E1
    if buf.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/msword"

    # ZIP container — DOCX/XLSX/PPTX cũng dùng. Phân biệt sâu hơn cần unzip
    # nhưng ở đây caller chỉ cần biết là "ZIP-based Office", đủ để chặn
    # exe/script.
    if buf.startswith(b"PK\x03\x04"):
        return "application/zip"

    return None


# ============================================================================
# F-08: Helper kiểm tra UploadFile (size + mime + filename)
# ============================================================================
@dataclass
class CheckedUpload:
    """Kết quả sau khi upload đã được validate."""
    content: bytes          # nội dung file (đã đọc, đã giới hạn size)
    mime: str               # MIME type thực tế nhận diện được
    safe_name: str          # tên file gốc đã sanitize (lưu DB / hiển thị)
    extension: str          # phần mở rộng SUY RA TỪ MIME, không từ user


# Map MIME -> extension chuẩn. CỐ TÌNH KHÔNG để client tự đặt extension.
_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    # ZIP container giả định là DOCX (allowlist nơi caller phải kiểm soát).
    "application/zip": ".docx",
}


async def validate_upload_file(
    upload: UploadFile,
    allowed_mimes: Iterable[str],
    max_bytes: int,
) -> CheckedUpload:
    """
    Đọc và kiểm tra 1 UploadFile.

    Args:
        upload        : UploadFile từ FastAPI (Form/File).
        allowed_mimes : iterable các MIME type được chấp nhận, ví dụ
                        {"image/jpeg", "image/png", "image/webp"}.
        max_bytes     : ngưỡng tối đa, vd 5 * 1024 * 1024 = 5MB.

    Quy trình bảo vệ:
        1) Đọc tối đa `max_bytes + 1` byte. Nếu vượt -> 413 Request Too Large.
        2) Detect MIME thực tế qua magic bytes -> phải nằm trong allowlist.
        3) Sanitize tên file gốc trước khi trả về.

    Raises:
        HTTPException(413) nếu file quá lớn.
        HTTPException(415) nếu MIME không được hỗ trợ.
    """
    # 1) ĐỌC AN TOÀN — chặn DoS bằng file lớn:
    # đọc tối đa max_bytes+1, nếu thấy đủ +1 nghĩa là vượt ngưỡng.
    head = await upload.read(max_bytes + 1)
    if len(head) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File vượt quá kích thước cho phép ({max_bytes // (1024 * 1024)}MB).",
        )

    # 2) DETECT MIME thực tế — không tin upload.content_type vì client tự gửi.
    mime = detect_mime(head)
    if mime is None or mime not in set(allowed_mimes):
        raise HTTPException(
            status_code=415,
            detail="Định dạng file không được hỗ trợ hoặc bị giả mạo phần mở rộng.",
        )

    # 3) SANITIZE tên file gốc
    safe_name = sanitize_filename(upload.filename)

    return CheckedUpload(
        content=head,
        mime=mime,
        safe_name=safe_name,
        extension=_MIME_TO_EXT.get(mime, ""),
    )
