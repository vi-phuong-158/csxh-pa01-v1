# -*- coding: utf-8 -*-
"""
Text Utility Functions
"""
import unicodedata
import re


def remove_accents(input_str):
    """
    Loại bỏ dấu tiếng Việt
    """
    if not input_str:
        return ""
    # Thay thế Đ/đ
    s1 = u'Đ'.encode('utf-8')
    s2 = u'đ'.encode('utf-8')
    input_str = input_str.replace(
        s1.decode('utf-8'), 'D').replace(s2.decode('utf-8'), 'd')
    # Chuẩn hóa NFD và loại bỏ ký tự combining marks (dấu)
    return ''.join(c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn')


def normalize_string(s):
    """
    Chuẩn hóa chuỗi cho tìm kiếm: bỏ dấu, thường, bỏ khoảng trắng và ký tự đặc biệt
    Ví dụ: "Nguyễn Văn A" -> "nguyenvana"
    """
    if not s:
        return ""
    s = remove_accents(s).lower()
    return re.sub(r'[^a-z0-9]', '', s)
