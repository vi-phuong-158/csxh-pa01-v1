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
        Verify that search_doi_tuong uses the 2-step fetch strategy:
        1. Fetch cccd, ho_ten (index)
        2. Fetch full details for matches
        """
        from views.tra_cuu import search_doi_tuong

        # Mock connection
        mock_conn = MagicMock()

        # Setup mock return values
        # Call 1: Index fetch (returns cccd, ho_ten)
        df_index = pd.DataFrame({
            'cccd': ['001', '002', '003'],
            'ho_ten': ['Nguyen Van A', 'Tran Van B', 'Le Van C'],
            'dia_chi_tinh': ['Phú Thọ', 'Hà Nội', 'Phú Thọ'],
        })

        # Call 2: Details fetch (returns full rows for matches)
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

        # Execute
        results = search_doi_tuong(mock_conn, "Nguyen Van A", "Tất cả", "Tất cả", "Tất cả")

        # Verify
        self.assertEqual(len(results), 1)
        self.assertEqual(results.iloc[0]['cccd'], '001')

        # Verify calls
        self.assertTrue(mock_read_sql.call_count >= 2)

        # Verify first call was lightweight
        call_args_1 = mock_read_sql.call_args_list[0]
        sql_1 = call_args_1[0][0]
        self.assertIn("SELECT cccd, ho_ten", sql_1)
        self.assertNotIn("*", sql_1.split("FROM")[0]) # Ensure * is not in SELECT part

        # Verify second call used IN clause
        call_args_2 = mock_read_sql.call_args_list[1]
        sql_2 = call_args_2[0][0]
        self.assertIn("SELECT * FROM doi_tuong WHERE cccd IN", sql_2)
