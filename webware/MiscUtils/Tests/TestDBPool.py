import sqlite3
import unittest

from MiscUtils.DBPool import DBPool


class TestDBPool(unittest.TestCase):

    def testDbPool(self):
        pool = DBPool(sqlite3, 10, database=':memory:')
        for _count in range(15):
            con = pool.connection()
            cursor = con.cursor()
            cursor.execute("select 1 union select 2 union select 3 order by 1")
            rows = cursor.fetchall()
            self.assertEqual(rows, [(1,), (2,), (3,)])
            con.close()
