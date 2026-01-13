# -*- coding: utf-8 -*-
"""
Module Fuzzy Matching cho tiếng Việt - Security Profile 360
Áp dụng patterns từ thefuzz/rapidfuzz với ngưỡng 80%
"""
from rapidfuzz import fuzz, process
import unicodedata
import re
from typing import List, Dict, Optional, Tuple

# Ngưỡng độ tương đồng (User-approved: 80%)
THRESHOLD_EXACT = 95      # Khớp chính xác
THRESHOLD_SUSPECT = 80    # Nghi vấn - cần kiểm tra (ngưỡng chính)
THRESHOLD_LOW = 60        # Có thể liên quan


def normalize_vietnamese(text: str) -> str:
    """
    Chuẩn hóa chuỗi tiếng Việt:
    - Chuyển lowercase
    - Loại bỏ dấu câu thừa
    - Giữ nguyên dấu tiếng Việt
    """
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def remove_vietnamese_diacritics(text: str) -> str:
    """
    Chuyển đổi chữ có dấu thành không dấu.
    Ví dụ: 'Nguyễn Văn An' -> 'Nguyen Van An'
    """
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))


def compare_names(name1: str, name2: str) -> Dict[str, int]:
    """
    So sánh 2 tên với nhiều thuật toán khác nhau.
    Returns dict với các loại score khác nhau (0-100).
    
    Pattern từ thefuzz:
    - ratio: Levenshtein distance cơ bản
    - partial_ratio: So sánh substring
    - token_sort: Sắp xếp từ trước khi so sánh
    - token_set: Bỏ qua thứ tự và từ trùng
    - weighted: Tự động chọn thuật toán tốt nhất
    """
    n1 = normalize_vietnamese(name1)
    n2 = normalize_vietnamese(name2)
    
    if not n1 or not n2:
        return {
            'ratio': 0,
            'partial_ratio': 0,
            'token_sort': 0,
            'token_set': 0,
            'weighted': 0,
            'best': 0
        }
    
    scores = {
        'ratio': fuzz.ratio(n1, n2),
        'partial_ratio': fuzz.partial_ratio(n1, n2),
        'token_sort': fuzz.token_sort_ratio(n1, n2),
        'token_set': fuzz.token_set_ratio(n1, n2),
        'weighted': fuzz.WRatio(n1, n2),
    }
    scores['best'] = max(scores.values())
    
    return scores


def find_similar_names(
    query: str, 
    candidates: List[str], 
    threshold: int = THRESHOLD_SUSPECT,
    limit: int = 10
) -> List[Dict]:
    """
    Tìm các tên tương tự trong danh sách.
    
    Pattern: extractOne với custom scorer (token_set_ratio)
    Đặc biệt phù hợp cho tiếng Việt vì bỏ qua thứ tự họ/tên.
    
    Args:
        query: Tên cần tìm
        candidates: Danh sách tên để so sánh
        threshold: Ngưỡng tối thiểu (mặc định 80%)
        limit: Số kết quả tối đa
        
    Returns:
        List of dicts với {name, score, index}
    """
    if not candidates or not query:
        return []
    
    normalized_query = normalize_vietnamese(query)
    
    if not normalized_query:
        return []
    
    # Sử dụng token_set_ratio - tốt nhất cho tiếng Việt
    results = process.extract(
        normalized_query,
        candidates,
        scorer=fuzz.token_set_ratio,
        limit=limit
    )
    
    return [
        {'name': name, 'score': score, 'index': idx}
        for name, score, idx in results
        if score >= threshold
    ]


def classify_match(score: int) -> Tuple[str, str]:
    """
    Phân loại kết quả match dựa trên score.
    
    Returns:
        (status_text, status_type)
    """
    if score >= THRESHOLD_EXACT:
        return ('✅ Khớp chính xác', 'exact')
    elif score >= THRESHOLD_SUSPECT:
        return ('⚠️ Nghi vấn - cần kiểm tra', 'suspect')
    elif score >= THRESHOLD_LOW:
        return ('🔍 Có thể liên quan', 'related')
    else:
        return ('❌ Không khớp', 'no_match')


def batch_screen(
    input_names: List[str], 
    database_names: List[str],
    threshold: int = THRESHOLD_SUSPECT
) -> List[Dict]:
    """
    Rà soát hàng loạt - So sánh danh sách đầu vào với database.
    
    Pattern từ process.extractWithoutOrder của thefuzz.
    
    Args:
        input_names: Danh sách tên cần rà soát
        database_names: Danh sách tên trong database
        threshold: Ngưỡng (mặc định 80%)
        
    Returns:
        List of screening results
    """
    results = []
    
    for query in input_names:
        if not query or not str(query).strip():
            continue
        
        query = str(query).strip()
        matches = find_similar_names(query, database_names, threshold)
        
        if matches:
            best = matches[0]
            status, status_type = classify_match(best['score'])
            results.append({
                'input': query,
                'matched': best['name'],
                'score': best['score'],
                'status': status,
                'status_type': status_type,
                'alternatives': matches[1:5]  # Top 4 alternatives
            })
        else:
            results.append({
                'input': query,
                'matched': None,
                'score': 0,
                'status': '❌ Không tìm thấy',
                'status_type': 'not_found',
                'alternatives': []
            })
    
    return results


def find_potential_duplicates(names: List[str], threshold: int = THRESHOLD_SUSPECT) -> List[Dict]:
    """
    Tìm các cặp tên có thể trùng lặp trong danh sách.
    Phục vụ cho việc khử trùng khi import Excel.
    
    Args:
        names: Danh sách tên
        threshold: Ngưỡng coi là trùng (mặc định 80%)
        
    Returns:
        List of potential duplicate pairs
    """
    duplicates = []
    n = len(names)
    
    for i in range(n):
        for j in range(i + 1, n):
            if not names[i] or not names[j]:
                continue
                
            score = fuzz.token_set_ratio(
                normalize_vietnamese(names[i]),
                normalize_vietnamese(names[j])
            )
            
            if score >= threshold:
                duplicates.append({
                    'index_1': i,
                    'index_2': j,
                    'name_1': names[i],
                    'name_2': names[j],
                    'score': score,
                    'status': classify_match(score)[0]
                })
    
    return duplicates


# Convenience functions for common use cases
def quick_match(name1: str, name2: str) -> int:
    """Quick match score between two names using WRatio."""
    return fuzz.WRatio(
        normalize_vietnamese(name1),
        normalize_vietnamese(name2)
    )


def is_likely_same_person(name1: str, name2: str, threshold: int = THRESHOLD_SUSPECT) -> bool:
    """Check if two names likely belong to the same person."""
    return quick_match(name1, name2) >= threshold
