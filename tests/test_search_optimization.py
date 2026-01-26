
import unittest
import sqlite3
import pandas as pd
import os


class TestSearchOptimization(unittest.TestCase):
    DB_NAME = "test_search_opt.db"

    def setUp(self):
        if os.path.exists(self.DB_NAME):
            os.remove(self.DB_NAME)

        self.conn = sqlite3.connect(self.DB_NAME)
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE doi_tuong (
                cccd TEXT PRIMARY KEY,
                ho_ten TEXT,
                dia_chi_tinh TEXT,
                gioi_tinh TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert 50 records for 'Hanoi' (Prefix A - sorts first)
        for i in range(50):
            cursor.execute("INSERT INTO doi_tuong (cccd, ho_ten, dia_chi_tinh, gioi_tinh) VALUES (?, ?, ?, ?)",
                           (f"A{i:03d}", f"User A{i}", "Hanoi", "Nam"))

        # Insert 10 records for 'Danang' (Prefix B - sorts second)
        for i in range(10):
            cursor.execute("INSERT INTO doi_tuong (cccd, ho_ten, dia_chi_tinh, gioi_tinh) VALUES (?, ?, ?, ?)",
                           (f"B{i:03d}", f"User B{i}", "Danang", "Nu"))

        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.DB_NAME):
            os.remove(self.DB_NAME)

    def test_sql_filtering_correctness(self):
        """Verify that pushing filters to SQL returns correct results on Page 1"""
        ITEMS_PER_PAGE = 50
        current_page = 1
        offset = (current_page - 1) * ITEMS_PER_PAGE
        filter_tinh = "Danang"

        # Logic to be implemented in views/tra_cuu.py
        conditions = []
        params = []

        if filter_tinh:
            conditions.append("dia_chi_tinh = ?")
            params.append(filter_tinh)

        where_clause = " WHERE " + \
            " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT cccd, ho_ten, dia_chi_tinh
            FROM doi_tuong
            {where_clause}
            ORDER BY cccd
            LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
        """

        df = pd.read_sql_query(query, self.conn, params=params)

        # Expect 10 records (all Danang records)
        self.assertEqual(len(df), 10)
        self.assertTrue(all(df['dia_chi_tinh'] == 'Danang'))

    def test_count_query_correctness(self):
        """Verify that count query respects filters"""
        filter_tinh = "Danang"

        conditions = []
        params = []

        if filter_tinh:
            conditions.append("dia_chi_tinh = ?")
            params.append(filter_tinh)

        where_clause = " WHERE " + \
            " AND ".join(conditions) if conditions else ""

        count_query = f"SELECT COUNT(*) as total FROM doi_tuong {where_clause}"
        total_count = pd.read_sql_query(
            count_query, self.conn, params=params).iloc[0, 0]

        self.assertEqual(total_count, 10)


if __name__ == "__main__":
    unittest.main()
