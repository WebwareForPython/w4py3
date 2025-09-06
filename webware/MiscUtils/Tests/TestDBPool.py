import sqlite3
import unittest

from MiscUtils.DBPool import DBPool


class TestDBPool(unittest.TestCase):

    def setUp(self):
        self.pool = DBPool(sqlite3, 10, database=':memory:')

    def tearDown(self):
        self.pool.close()

    def testDbPool(self):
        query = "select 1 union select 2 union select 3 order by 1"
        result = [(1,), (2,), (3,)]
        for _count in range(15):
            con = self.pool.connection()
            cursor = con.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            self.assertEqual(rows, result)
            con.close()
