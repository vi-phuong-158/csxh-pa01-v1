import unittest
from unittest.mock import MagicMock, patch, ANY
import pandas as pd
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

# Mock streamlit BEFORE importing views
sys.modules['streamlit'] = MagicMock()
sys.modules['streamlit_echarts'] = MagicMock()

# Now we can import
# We defer import to the test or just try here?
# views.tra_cuu imports constants which is fine.

class TestSearchOptimization(unittest.TestCase):

    @patch('views.tra_cuu.pd.read_sql_query')
    def test_search_strategy(self, mock_read_sql):
        """
        Verify that search implements the 2-step fetch strategy:
        1. get_search_candidates fetches index (cccd, ho_ten)
        2. fetch_doi_tuong_details fetches full details
        """
        from views.tra_cuu import get_search_candidates, fetch_doi_tuong_details

        # Mock connection
        mock_conn = MagicMock()

        # Setup mock return values
        
        # 1. Mock for get_search_candidates
        df_index = pd.DataFrame({
            'cccd': ['001', '002', '003'],
            'ho_ten': ['Nguyen Van A', 'Tran Van B', 'Le Van C'],
            'dia_chi_tinh': ['Phú Thọ', 'Hà Nội', 'Phú Thọ'],
        })

        # 2. Mock for fetch_doi_tuong_details
        df_details = pd.DataFrame({
            'cccd': ['001'],
            'ho_ten': ['Nguyen Van A'],
            'full_data': ['...']
        })

        def side_effect(sql, conn, params=None):
            if "SELECT cccd, ho_ten" in sql:
                return df_index
            if "SELECT * FROM doi_tuong WHERE cccd IN" in sql:
                return df_details
            return pd.DataFrame()

        mock_read_sql.side_effect = side_effect

        # Execute Step 1: Get Candidates
        candidates = get_search_candidates(mock_conn, "Nguyen Van A", "Tất cả", "Tất cả", "Tất cả")
        
        # Verify Step 1
        self.assertIsInstance(candidates, list)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], '001')
        
        # Verify SQL for Step 1
        call_args_1 = mock_read_sql.call_args_list[0]
        sql_1 = call_args_1[0][0]
        self.assertIn("SELECT cccd, ho_ten", sql_1)
        self.assertNotIn("*", sql_1.split("FROM")[0])

        # Execute Step 2: Fetch Details
        details = fetch_doi_tuong_details(mock_conn, candidates)
        
        # Verify Step 2
        self.assertFalse(details.empty)
        self.assertEqual(details.iloc[0]['cccd'], '001')
        
        # Verify SQL for Step 2
        call_args_2 = mock_read_sql.call_args_list[1]
        sql_2 = call_args_2[0][0]
        self.assertIn("SELECT * FROM doi_tuong WHERE cccd IN", sql_2)
