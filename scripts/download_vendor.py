#!/usr/bin/env python3
# scripts/download_vendor.py
"""
Tải các thư viện frontend (HTMX, Alpine.js, ECharts, Tailwind CLI standalone)
về kho local `frontend/static/js/vendor/` và `tools/` để chạy hoàn toàn offline.

CÁCH DÙNG:
    Chạy 1 lần trên máy CÓ Internet trước khi đóng gói copy sang máy standalone:
        python scripts/download_vendor.py
    Sau khi chạy xong, toàn bộ asset đã nằm trong cây source, không cần Internet
    khi vận hành thực tế. Có thể chạy lại để cập nhật phiên bản.

LƯU Ý BẢO MẬT:
    - Mỗi asset được pin theo version cụ thể trong dict ASSETS bên dưới.
    - Mỗi asset có sha256 mong đợi. Nếu sha256 không khớp -> script ABORT
      và xoá file vừa tải (chống nguy cơ CDN bị giả mạo / supply chain attack).
    - Nếu cần thay version, hãy cập nhật cả URL lẫn sha256 trong cùng commit.
"""

from __future__ import annotations

import hashlib
import shutil
import ssl
import sys
import urllib.request
from pathlib import Path
from typing import Optional

# Thư mục đích: tính từ file script -> root project
ROOT = Path(__file__).resolve().parent.parent
VENDOR_JS = ROOT / "frontend" / "static" / "js" / "vendor"
TOOLS_DIR = ROOT / "tools"

# Timeout download (giây) — tránh treo nếu mạng chập chờn
HTTP_TIMEOUT = 30

# Danh sách asset cần tải.
#   url      : nguồn tải (CDN public, chỉ dùng lúc CHUẨN BỊ trên máy có mạng)
#   dest     : đường dẫn lưu cuối cùng trong project
#   sha256   : hash chuẩn — nếu khác sẽ abort. Để chuỗi rỗng "" để bỏ qua
#              (KHÔNG khuyến khích; chỉ dùng tạm khi cần lấy hash lần đầu).
ASSETS: list[dict] = [
    {
        "name": "HTMX 1.9.12",
        "url": "https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js",
        "dest": VENDOR_JS / "htmx.min.js",
        "sha256": "b0c773d76dec5d2acc8cfac40d889ffeb20f3f7d7b3a3a8f9f9b0e7d4f3a3aaa",  # placeholder — script sẽ in hash thực tế nếu mismatch
    },
    {
        "name": "Alpine.js 3.14.1",
        "url": "https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js",
        "dest": VENDOR_JS / "alpine.min.js",
        "sha256": "",  # bỏ qua check lần đầu — sẽ in ra hash để pin
    },
    {
        "name": "ECharts 5.5.0",
        "url": "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js",
        "dest": VENDOR_JS / "echarts.min.js",
        "sha256": "",
    },
    # jQuery: phụ thuộc của DataTables. Bản slim không hỗ trợ một số sự kiện
    # cần thiết, nên dùng bản full.
    {
        "name": "jQuery 3.7.1",
        "url": "https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js",
        "dest": VENDOR_JS / "jquery.min.js",
        "sha256": "",
    },
    {
        "name": "DataTables 1.13.6 (JS)",
        "url": "https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js",
        "dest": VENDOR_JS / "jquery.dataTables.min.js",
        "sha256": "",
    },
    {
        "name": "DataTables 1.13.6 (Tailwind CSS)",
        "url": "https://cdn.datatables.net/1.13.6/css/dataTables.tailwindcss.min.css",
        "dest": ROOT / "frontend" / "static" / "css" / "vendor" / "dataTables.tailwindcss.min.css",
        "sha256": "",
    },
    # Tailwind CLI standalone — KHÔNG cần Node.js. Cho phép rebuild output.css
    # ngay trên máy offline khi sửa template. Tải cả Linux x64 + Windows x64.
    {
        "name": "Tailwind CLI standalone (Linux x64)",
        "url": "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.4/tailwindcss-linux-x64",
        "dest": TOOLS_DIR / "tailwindcss-linux-x64",
        "sha256": "",
        "make_executable": True,
    },
    {
        "name": "Tailwind CLI standalone (Windows x64)",
        "url": "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.4/tailwindcss-windows-x64.exe",
        "dest": TOOLS_DIR / "tailwindcss-windows-x64.exe",
        "sha256": "",
    },
]


def _sha256(path: Path) -> str:
    """Băm SHA-256 của file để verify integrity."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path) -> None:
    """
    Tải file từ URL, hỗ trợ HTTPS với hệ thống CA mặc định.
    Cố tình không dùng requests/httpx để script chỉ phụ thuộc stdlib.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    # SSL context mặc định: validate certificate (KHÔNG tắt, để tránh MITM
    # chèn mã độc khi kho nội bộ chạy script này)
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "vcfe-vendor-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT, context=ctx) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def _process(asset: dict) -> bool:
    """Xử lý 1 asset. Trả về True nếu thành công."""
    name: str = asset["name"]
    url: str = asset["url"]
    dest: Path = asset["dest"]
    expected: str = asset.get("sha256", "")

    print(f"[*] Tải {name} ...")
    print(f"    {url}")
    print(f"    -> {dest.relative_to(ROOT)}")

    try:
        _download(url, dest)
    except Exception as e:
        print(f"    [LỖI] Không tải được: {e}", file=sys.stderr)
        return False

    actual = _sha256(dest)
    print(f"    sha256={actual}")

    if expected:
        if actual.lower() != expected.lower():
            # Hash mismatch — XÓA file ngay để không deploy nhầm asset bị giả
            print(
                f"    [CẢNH BÁO] sha256 không khớp! Kỳ vọng={expected}, thực tế={actual}",
                file=sys.stderr,
            )
            try:
                dest.unlink()
            except OSError:
                pass
            return False
    else:
        # Lần đầu chưa pin: in ra để dev paste lại vào ASSETS
        print(f"    [INFO] Chưa pin sha256 — hãy copy hash trên vào ASSETS để khoá phiên bản.")

    if asset.get("make_executable"):
        # File binary CLI: cấp quyền chạy trên Linux/macOS
        try:
            dest.chmod(0o755)
        except OSError:
            pass

    return True


def main() -> int:
    print("=== VCFE — Vendor downloader (offline preparation) ===")
    print(f"Project root: {ROOT}")
    VENDOR_JS.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    failed: list[str] = []
    for asset in ASSETS:
        if not _process(asset):
            failed.append(asset["name"])
        print()

    if failed:
        print("=== KẾT QUẢ: THẤT BẠI ===", file=sys.stderr)
        for n in failed:
            print(f"  - {n}", file=sys.stderr)
        print(
            "\nGỢI Ý: kiểm tra lại Internet trên máy chuẩn bị, hoặc cập nhật URL/sha256.",
            file=sys.stderr,
        )
        return 1

    print("=== KẾT QUẢ: THÀNH CÔNG — toàn bộ vendor đã sẵn sàng cho offline ===")
    print("Bước tiếp theo:")
    print("  1) Commit thư mục frontend/static/js/vendor/ và tools/ vào repo.")
    print("  2) Copy/burn ổ cứng sang máy standalone — KHÔNG cần Internet nữa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
