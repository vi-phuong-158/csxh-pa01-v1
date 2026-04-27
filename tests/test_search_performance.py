import unittest
import pandas as pd
from utils.text_utils import normalize_string


def run_optimized_search(df_all, search_query, search_type):
    # Pre-compute normalization
    query_norm = normalize_string(search_query)
    query_lower = search_query.lower()

    # 1. CCCD Match (Vectorized)
    mask_cccd = pd.Series(False, index=df_all.index)
    if search_type in ["Tất cả", "CCCD"]:
        mask_cccd = df_all['cccd'].astype(str).str.contains(
            query_lower, case=False, na=False)

    # 2. Ho ten Match (Vectorized + Subsequence)
    mask_hoten = pd.Series(False, index=df_all.index)
    if search_type in ["Tất cả", "Họ tên"]:
        # Normalize 'ho_ten' column
        normalized_hoten = df_all['ho_ten'].apply(
            lambda x: normalize_string(x) if x else "")

        # Check containment (Fast)
        mask_hoten_contains = normalized_hoten.str.contains(
            query_norm, na=False, regex=False)
        mask_hoten = mask_hoten_contains

        # Check subsequence (Slower, only if query >= 3 chars)
        if len(query_norm) >= 3:
            def check_subsequence(text_norm):
                it = iter(text_norm)
                return all(char in it for char in query_norm)

            # Only check rows that failed containment
            remaining_indices = ~mask_hoten_contains
            if remaining_indices.any():
                subsequence_matches = normalized_hoten[remaining_indices].apply(
                    check_subsequence)
                mask_hoten = mask_hoten | subsequence_matches.reindex(
                    df_all.index, fill_value=False)

    # Combine masks
    final_mask = mask_cccd | mask_hoten
    return df_all[final_mask]


class TestSearchPerformance(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'cccd': ['025123456789', '025987654321', '000000000000'],
            'ho_ten': ['Nguyễn Văn A', 'Trần Thị B', 'Vi Ngọc Phương']
        })

    def test_search_cccd_exact(self):
        result = run_optimized_search(self.df, '025123456789', 'CCCD')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['cccd'], '025123456789')

    def test_search_cccd_partial(self):
        result = run_optimized_search(self.df, '123', 'CCCD')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['cccd'], '025123456789')

    def test_search_hoten_contains(self):
        result = run_optimized_search(self.df, 'Nguyen', 'Họ tên')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['ho_ten'], 'Nguyễn Văn A')

    def test_search_hoten_fuzzy(self):
        # "viphuong" -> "Vi Ngoc Phuong" (Subsequence match)
        result = run_optimized_search(self.df, 'viphuong', 'Họ tên')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['ho_ten'], 'Vi Ngọc Phương')

    def test_search_all(self):
        result = run_optimized_search(self.df, 'van', 'Tất cả')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['ho_ten'], 'Nguyễn Văn A')


if __name__ == '__main__':
    unittest.main()
