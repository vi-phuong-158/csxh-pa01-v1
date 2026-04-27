# -*- coding: utf-8 -*-
"""
Module Khử trùng lặp dữ liệu - VCFE Database
Áp dụng patterns từ dedupe library: Record Linkage, Blocking, Clustering
"""
from rapidfuzz import fuzz
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
import re

# Trọng số cho các trường (weight) - Pattern từ dedupe
FIELD_WEIGHTS = {
    'cccd': 100,        # CCCD trùng = chắc chắn cùng người
    'ho_ten': 40,       # Tên quan trọng
    'ngay_sinh': 30,    # Ngày sinh
    'sdt': 25,          # SĐT
    'dia_chi': 10,      # Địa chỉ ít quan trọng nhất
}

# Ngưỡng (User-approved: 80%)
DUPLICATE_THRESHOLD = 80


def normalize_phone(phone: str) -> str:
    """
    Chuẩn hóa SĐT về định dạng chuẩn.
    Ví dụ: 0912345678 -> 84912345678
    """
    if not phone:
        return ""
    phone = ''.join(c for c in str(phone) if c.isdigit())
    if phone.startswith('0'):
        phone = '84' + phone[1:]
    return phone


def normalize_name(name: str) -> str:
    """Chuẩn hóa tên để so sánh."""
    if not name:
        return ""
    name = str(name).lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def compare_records(record1: dict, record2: dict) -> dict:
    """
    So sánh 2 bản ghi theo nhiều trường.

    Pattern: Record Linkage từ dedupe
    - Mỗi trường có trọng số khác nhau
    - Tính điểm tổng hợp có trọng số

    Returns:
        Dict với field_scores, overall_score, is_duplicate
    """
    scores = {}
    weighted_sum = 0
    total_weight = 0

    # So sánh CCCD (exact match - quan trọng nhất)
    if record1.get('cccd') and record2.get('cccd'):
        cccd1 = str(record1['cccd']).strip()
        cccd2 = str(record2['cccd']).strip()
        if cccd1 == cccd2:
            scores['cccd'] = 100
        else:
            scores['cccd'] = 0
        weighted_sum += scores['cccd'] * FIELD_WEIGHTS['cccd']
        total_weight += FIELD_WEIGHTS['cccd']

    # So sánh họ tên (fuzzy match)
    if record1.get('ho_ten') and record2.get('ho_ten'):
        scores['ho_ten'] = fuzz.token_set_ratio(
            normalize_name(record1['ho_ten']),
            normalize_name(record2['ho_ten'])
        )
        weighted_sum += scores['ho_ten'] * FIELD_WEIGHTS['ho_ten']
        total_weight += FIELD_WEIGHTS['ho_ten']

    # So sánh ngày sinh (exact match)
    if record1.get('ngay_sinh') and record2.get('ngay_sinh'):
        dob1 = str(record1['ngay_sinh']).strip()
        dob2 = str(record2['ngay_sinh']).strip()
        if dob1 == dob2:
            scores['ngay_sinh'] = 100
        else:
            scores['ngay_sinh'] = 0
        weighted_sum += scores['ngay_sinh'] * FIELD_WEIGHTS['ngay_sinh']
        total_weight += FIELD_WEIGHTS['ngay_sinh']

    # So sánh SĐT (normalized match)
    sdt1 = record1.get('sdt') or record1.get(
        'gia_tri')  # Có thể ở bảng lien_he
    sdt2 = record2.get('sdt') or record2.get('gia_tri')
    if sdt1 and sdt2:
        phone1 = normalize_phone(sdt1)
        phone2 = normalize_phone(sdt2)
        if phone1 and phone2:
            if phone1 == phone2:
                scores['sdt'] = 100
            else:
                scores['sdt'] = 0
            weighted_sum += scores['sdt'] * FIELD_WEIGHTS['sdt']
            total_weight += FIELD_WEIGHTS['sdt']

    # So sánh địa chỉ (fuzzy match)
    addr1 = record1.get('dia_chi_xa') or record1.get('dia_chi')
    addr2 = record2.get('dia_chi_xa') or record2.get('dia_chi')
    if addr1 and addr2:
        scores['dia_chi'] = fuzz.token_set_ratio(
            normalize_name(str(addr1)),
            normalize_name(str(addr2))
        )
        weighted_sum += scores['dia_chi'] * FIELD_WEIGHTS['dia_chi']
        total_weight += FIELD_WEIGHTS['dia_chi']

    # Tính điểm tổng hợp
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0

    return {
        'field_scores': scores,
        'overall_score': round(overall_score, 2),
        'is_duplicate': overall_score >= DUPLICATE_THRESHOLD
    }


def block_by_birth_year(records: List[dict]) -> Dict[str, List[Tuple[int, dict]]]:
    """
    Blocking - Nhóm theo năm sinh trước khi so sánh.

    Pattern từ dedupe: Giảm số cặp cần so sánh từ O(n²) xuống O(n).
    Chỉ so sánh các bản ghi trong cùng block.

    Returns:
        Dict mapping year -> list of (original_index, record) tuples
    """
    blocks = defaultdict(list)

    for idx, record in enumerate(records):
        dob = record.get('ngay_sinh')
        if dob:
            # Extract year từ nhiều format khác nhau
            dob_str = str(dob)
            if len(dob_str) >= 4:
                year = dob_str[:4]  # Assume YYYY-MM-DD or YYYY/MM/DD
                if year.isdigit():
                    blocks[year].append((idx, record))
                    continue

        # Nếu không có ngày sinh, đưa vào block 'unknown'
        blocks['unknown'].append((idx, record))

    return dict(blocks)


def find_duplicates_in_batch(records: List[dict]) -> List[Tuple[int, int, dict]]:
    """
    Tìm các cặp trùng lặp trong batch import.

    Pattern: Blocking + Pairwise comparison

    Returns:
        List of (index1, index2, comparison_result) tuples
    """
    duplicates = []
    blocks = block_by_birth_year(records)

    for block_key, block_records in blocks.items():
        n = len(block_records)
        for i in range(n):
            for j in range(i + 1, n):
                idx1, rec1 = block_records[i]
                idx2, rec2 = block_records[j]

                comparison = compare_records(rec1, rec2)
                if comparison['is_duplicate']:
                    duplicates.append((idx1, idx2, comparison))

    return duplicates


def cluster_duplicates(duplicates: List[Tuple[int, int, dict]]) -> List[Set[int]]:
    """
    Clustering - Gom các bản ghi trùng thành nhóm.

    Pattern từ dedupe: Union-Find algorithm
    Nếu A trùng B, B trùng C thì {A, B, C} là 1 cluster.

    Returns:
        List of sets, each set contains indices of duplicate records
    """
    if not duplicates:
        return []

    # Union-Find algorithm
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Link all duplicate pairs
    for i, j, _ in duplicates:
        union(i, j)

    # Group by cluster root
    clusters = defaultdict(set)
    for idx in parent.keys():
        clusters[find(idx)].add(idx)

    # Only return clusters with more than 1 record
    return [cluster for cluster in clusters.values() if len(cluster) > 1]


def merge_duplicate_cluster(records: List[dict], cluster: Set[int]) -> dict:
    """
    Merge các bản ghi trùng thành 1 bản ghi duy nhất.

    Strategy: Ưu tiên giá trị không rỗng, giá trị xuất hiện nhiều nhất.

    Returns:
        Merged record
    """
    cluster_records = [records[i] for i in cluster]
    merged = {}

    # Các trường cần merge
    fields = ['cccd', 'ho_ten', 'ngay_sinh', 'gioi_tinh', 'dia_chi_xa',
              'phan_loai_nghe_nghiep', 'chi_tiet_nghe_nghiep', 'ghi_chu_chung']

    for field in fields:
        values = [r.get(field) for r in cluster_records if r.get(field)]
        if values:
            # Ưu tiên giá trị xuất hiện nhiều nhất
            merged[field] = max(set(values), key=values.count)

    return merged


def deduplicate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[dict]]:
    """
    API chính cho việc khử trùng batch import từ DataFrame.

    Args:
        df: DataFrame chứa dữ liệu cần khử trùng

    Returns:
        (cleaned_df, duplicate_report)
        - cleaned_df: DataFrame đã loại bỏ trùng lặp
        - duplicate_report: Báo cáo chi tiết về các bản ghi trùng
    """
    records = df.to_dict('records')

    # Tìm các cặp trùng
    duplicates = find_duplicates_in_batch(records)

    if not duplicates:
        return df, []

    # Gom nhóm
    clusters = cluster_duplicates(duplicates)

    duplicate_report = []
    indices_to_remove = set()

    for cluster in clusters:
        if len(cluster) > 1:
            cluster_list = sorted(cluster)
            keep_idx = cluster_list[0]  # Giữ bản ghi đầu tiên
            remove_indices = cluster_list[1:]

            indices_to_remove.update(remove_indices)

            duplicate_report.append({
                'kept_index': keep_idx,
                'kept_record': records[keep_idx],
                'removed_indices': remove_indices,
                'removed_records': [records[i] for i in remove_indices],
                'cluster_size': len(cluster)
            })

    # Xóa các bản ghi trùng
    cleaned_df = df.drop(index=list(indices_to_remove)).reset_index(drop=True)

    return cleaned_df, duplicate_report


def generate_duplicate_report(duplicate_report: List[dict]) -> str:
    """
    Tạo báo cáo text về các bản ghi trùng lặp.
    """
    if not duplicate_report:
        return "✅ Không phát hiện trùng lặp."

    lines = [f"⚠️ Phát hiện {len(duplicate_report)} nhóm trùng lặp:"]
    lines.append("")

    for i, group in enumerate(duplicate_report, 1):
        kept = group['kept_record']
        removed_count = len(group['removed_records'])

        lines.append(f"**Nhóm {i}**: {group['cluster_size']} bản ghi")
        lines.append(
            f"  - Giữ lại: {kept.get('ho_ten', 'N/A')} (CCCD: {kept.get('cccd', 'N/A')})")
        lines.append(f"  - Loại bỏ: {removed_count} bản ghi trùng")
        lines.append("")

    return "\n".join(lines)
