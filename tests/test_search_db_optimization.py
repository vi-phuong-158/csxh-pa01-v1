import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from views.tra_cuu import page_tra_cuu

class TestSearchDBOptimization(unittest.TestCase):
    def setUp(self):
        # Mock streamlit to avoid UI errors
        self.st_patcher = patch('views.tra_cuu.st')
        self.mock_st = self.st_patcher.start()

        # Mock connection
        self.conn_patcher = patch('views.tra_cuu.get_connection')
        self.mock_get_conn = self.conn_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_get_conn.return_value = self.mock_conn

        # Setup inputs for search
        self.mock_st.text_input.return_value = "Nguyen" # Search Query
        self.mock_st.selectbox.return_value = "Tất cả" # Filters

        def columns_side_effect(spec):
            if isinstance(spec, int):
                return [MagicMock() for _ in range(spec)]
            elif isinstance(spec, (list, tuple)):
                return [MagicMock() for _ in range(len(spec))]
            return [MagicMock()]

        self.mock_st.columns.side_effect = columns_side_effect
        self.mock_st.expander.return_value.__enter__.return_value = MagicMock()

    def tearDown(self):
        self.st_patcher.stop()
        self.conn_patcher.stop()

    @patch('views.tra_cuu.pd.read_sql_query')
    def test_column_pruning_and_deferred_loading(self, mock_read_sql):
        """Verify that search uses lightweight query first, then full fetch."""

        # 1. Setup mock returns
        # Lightweight DF
        df_light = pd.DataFrame({
            'cccd': ['001', '002', '003'],
            'ho_ten': ['Nguyen A', 'Tran B', 'Nguyen C']
        })

        # Full DF (for matches)
        df_full = pd.DataFrame({
            'cccd': ['001', '003'],
            'ho_ten': ['Nguyen A', 'Nguyen C'],
            'other_col': ['Data 1', 'Data 3']
        })

        def side_effect(sql, conn, params=None):
            if "SELECT cccd, ho_ten FROM doi_tuong" in sql:
                return df_light
            elif "SELECT * FROM doi_tuong WHERE cccd IN" in sql:
                return df_full
            elif "SELECT COUNT(*)" in sql:
                return pd.DataFrame({'total': [10]})
            return pd.DataFrame()

        mock_read_sql.side_effect = side_effect

        # 2. Run the page function
        page_tra_cuu()

        # 3. Verify calls
        # Expect at least 2 calls to read_sql_query
        # Call 1: Lightweight fetch
        call_args_list = mock_read_sql.call_args_list

        # Verify first call is lightweight
        first_call_sql = call_args_list[0][0][0]
        self.assertIn("SELECT cccd, ho_ten FROM doi_tuong", first_call_sql)
        self.assertNotIn("*", first_call_sql.split("FROM")[0]) # Ensure * is not in SELECT clause

        # Verify second call is full fetch with IN clause
        # Note: Depending on implementation, there might be filter logic calls, but here we expect the fetch for matches
        found_full_fetch = False
        for args in call_args_list:
            sql = args[0][0]
            if "SELECT * FROM doi_tuong WHERE cccd IN" in sql:
                found_full_fetch = True
                # Verify params contain the matched CCCDs ('001', '003') because '002' (Tran B) shouldn't match "Nguyen"
                # (Assuming "Nguyen" matches "Nguyen A" and "Nguyen C")
                self.assertIn("?", sql)
                params = args[1].get('params')
                self.assertEqual(len(params), 2)
                self.assertIn('001', params)
                self.assertIn('003', params)

        self.assertTrue(found_full_fetch, "Did not find secondary full fetch query")

    @patch('views.tra_cuu.pd.read_sql_query')
    def test_chunking_logic(self, mock_read_sql):
        """Verify that large result sets are chunked."""

        # Generate 1000 matching records
        matches_light = pd.DataFrame({
            'cccd': [str(i) for i in range(1000)],
            'ho_ten': ['Nguyen A' for _ in range(1000)]
        })

        def side_effect(sql, conn, params=None):
            if "SELECT cccd, ho_ten" in sql:
                return matches_light
            elif "SELECT * FROM doi_tuong WHERE cccd IN" in sql:
                # Return dummy DF with required columns
                return pd.DataFrame({
                    'cccd': params,
                    'ho_ten': ['Name']*len(params)
                })
            return pd.DataFrame()

        mock_read_sql.side_effect = side_effect

        page_tra_cuu()

        # Verify chunking
        # 1000 matches, chunk size 900 -> 2 chunks
        full_fetch_calls = [
            args for args in mock_read_sql.call_args_list
            if "SELECT * FROM doi_tuong WHERE cccd IN" in args[0][0]
        ]

        self.assertEqual(len(full_fetch_calls), 2)

        # Verify params size
        params1 = full_fetch_calls[0][1]['params']
        params2 = full_fetch_calls[1][1]['params']

        self.assertEqual(len(params1), 900)
        self.assertEqual(len(params2), 100)

if __name__ == '__main__':
    unittest.main()
