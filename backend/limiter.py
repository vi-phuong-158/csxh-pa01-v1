# backend/limiter.py
"""
Rate-limiting cho VCFE Database (offline standalone).

VẤN ĐỀ (F-11):
    SlowAPI mặc định rate-limit theo `get_remote_address`. Trên máy
    standalone IP luôn là 127.0.0.1, nên kẻ tấn công có physical access
    có thể mò mật khẩu của NHIỀU username khác nhau cùng lúc — quota IP
    gộp chung khiến quota theo từng tài khoản KHÔNG có hiệu lực.

GIẢI PHÁP:
    - Giữ `slowapi.Limiter(key_func=get_remote_address)` cho các endpoint
      khác (dashboard, tra-cuu...) như cũ.
    - Riêng `/auth/login` dùng cơ chế custom `check_login_rate(username)`
      tự cài đặt: sliding window in-memory cho từng username (lowercase).
    - Lý do KHÔNG dùng key_func async của SlowAPI: phiên bản 0.1.x của
      SlowAPI không await async key_func đúng cách -> key trở thành
      coroutine object (luôn unique) -> quota vô hiệu. Custom function
      tránh hoàn toàn vấn đề này.

Tầng 2 (defense-in-depth) đã có sẵn ở `backend/services/auth.py`: sau
MAX_FAILED_ATTEMPTS=5 sẽ KHOÁ tài khoản trong DB (lockout_until).
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque, Dict

from slowapi import Limiter
from slowapi.util import get_remote_address

# ============================================================================
# Limiter chung (giữ nguyên — dùng cho các route khác ngoài /auth/login)
# ============================================================================
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# F-11: Sliding-window rate limit theo USERNAME cho /auth/login
# ============================================================================
LOGIN_WINDOW_SECONDS: float = 60.0  # cửa sổ 60 giây
LOGIN_MAX_ATTEMPTS: int = 5         # tối đa 5 lần / cửa sổ

# In-memory store. Mỗi username -> deque các timestamp của lần thử.
# Đủ dùng cho app standalone 1 process. Nếu sau này đa-process, cần Redis.
_attempts: Dict[str, Deque[float]] = defaultdict(deque)
_lock = Lock()


def _purge_old(bucket: Deque[float], now: float) -> None:
    """Xoá các timestamp cũ hơn cửa sổ (sliding window)."""
    while bucket and now - bucket[0] > LOGIN_WINDOW_SECONDS:
        bucket.popleft()


def check_login_rate(username: str) -> bool:
    """
    Kiểm tra & ghi nhận 1 lần thử đăng nhập cho `username`.

    Trả True nếu CÒN trong giới hạn (cho phép xử lý tiếp).
    Trả False nếu vượt quota -> route handler tự raise 429.

    Nguyên tắc:
        - Username chuẩn hoá lowercase + strip (Admin == admin == admin ).
        - Chuỗi rỗng cũng bị tính (chống spam form rỗng).
        - Thread-safe bằng Lock — đề phòng nhiều worker uvicorn cùng
          process xử lý đồng thời.
    """
    key = (username or "").strip().lower()
    now = monotonic()

    with _lock:
        bucket = _attempts[key]
        _purge_old(bucket, now)
        if len(bucket) >= LOGIN_MAX_ATTEMPTS:
            return False
        bucket.append(now)
        return True


def reset_login_rate(username: str) -> None:
    """
    Xoá quota đã ghi nhận cho 1 username — gọi sau khi đăng nhập THÀNH CÔNG
    để không phạt user thật vì vài lần lỡ gõ sai trước đó.
    """
    key = (username or "").strip().lower()
    with _lock:
        _attempts.pop(key, None)


def _testing_clear_all() -> None:
    """Helper cho self-test — clear toàn bộ bucket. KHÔNG dùng ở runtime."""
    with _lock:
        _attempts.clear()
