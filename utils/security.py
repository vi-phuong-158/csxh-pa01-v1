# -*- coding: utf-8 -*-
"""
Security Utilities
Tập trung các hàm xử lý bảo mật, sanitization
"""

def sanitize_for_excel(text):
    """
    Sanitize input to prevent Excel Formula Injection (CSV Injection).
    Prepend single quote if string starts with =, +, -, or @
    """
    if text and isinstance(text, str):
        if text.startswith(('=', '+', '-', '@')):
            return f"'{text}"
    return text
