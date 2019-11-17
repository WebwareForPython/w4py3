import unittest


class HTMLStatusCodesTest(unittest.TestCase):

    def testHTTPStatusCodeList(self):
        from WebUtils.HTTPStatusCodes import HTTPStatusCodeList
        self.assertIsInstance(HTTPStatusCodeList, list)
        self.assertIn(
            (409, 'CONFLICT', 'Request conflict'), HTTPStatusCodeList)

    def testHTTPStatusCodes(self):
        from WebUtils.HTTPStatusCodes import HTTPStatusCodes
        self.assertIsInstance(HTTPStatusCodes, dict)
        d = HTTPStatusCodes[409]
        self.assertIs(d, HTTPStatusCodes['CONFLICT'])
        description = d['description']
        self.assertEqual(description, 'Request conflict')
        self.assertEqual(d['asciiMsg'], description)
        self.assertEqual(d['htmlMsg'], description)

    def testHTMLTableOfHTTPStatusCodes(self):
        from WebUtils.HTTPStatusCodes import htmlTableOfHTTPStatusCodes
        table = htmlTableOfHTTPStatusCodes()
        self.assertTrue(table.startswith('<table>'))
        self.assertIn('<th>Identifier</th>', table)
        self.assertIn(
            '<tr style="vertical-align:top"><td>404</td><td>NOT_FOUND</td>'
            '<td>Nothing matches the given URI</td></tr>', table)
        self.assertTrue(table.endswith('</table>'))
