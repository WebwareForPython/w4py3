import unittest

from io import BytesIO

from WebUtils.FieldStorage import FieldStorage


class TestFieldStorage(unittest.TestCase):

    def testGetRequest(self):
        fs = FieldStorage(environ=dict(
            REQUEST_METHOD='GET', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])

    def testPostRequestWithQuery(self):
        fs = FieldStorage(fp=BytesIO(), environ=dict(
            REQUEST_METHOD='GET', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])

    def testPostRequestWithBody(self):
        fs = FieldStorage(fp=BytesIO(b'd=4&e=5&e=6&f=6'), environ=dict(
            REQUEST_METHOD='POST'))
        self.assertEqual(fs.getfirst('d'), '4')
        self.assertEqual(fs.getfirst('e'), '5')
        self.assertEqual(fs.getfirst('f'), '6')
        self.assertEqual(fs.getlist('d'), ['4'])
        self.assertEqual(fs.getlist('e'), ['5', '6'])
        self.assertEqual(fs.getlist('f'), ['6'])

    def testPostRequestOverrides(self):
        fs = FieldStorage(fp=BytesIO(b'b=8&c=9&d=4&e=5&e=6&f=6'), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '8')
        self.assertEqual(fs.getfirst('c'), '9')
        self.assertEqual(fs.getfirst('d'), '4')
        self.assertEqual(fs.getfirst('e'), '5')
        self.assertEqual(fs.getfirst('f'), '6')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['8'])
        self.assertEqual(fs.getlist('c'), ['9'])
        self.assertEqual(fs.getlist('d'), ['4'])
        self.assertEqual(fs.getlist('e'), ['5', '6'])
        self.assertEqual(fs.getlist('f'), ['6'])

    def testPostRequestWithQueryWithSemicolon1(self):
        fs = FieldStorage(fp=BytesIO(), environ=dict(
            REQUEST_METHOD='GET', QUERY_STRING='a=1&b=2;b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])

    def testPostRequestWithQueryWithSemicolon2(self):
        fs = FieldStorage(fp=BytesIO(), environ=dict(
            REQUEST_METHOD='GET', QUERY_STRING='a=1;b=2&b=3;c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])
