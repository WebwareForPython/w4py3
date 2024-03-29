import unittest

from MiscUtils.CSVParser import CSVParser, ParseError


class CSVParserTests(unittest.TestCase):
    """CSV parser tests.

    TO DO

      * Test the different options for parser, see CSVParser.__init__().
    """

    def setUp(self):
        self.parse = CSVParser().parse

    def testNegatives(self):
        inputs = [
            '""a',
            '"a"b',
            'a\n,b'
        ]
        for inp in inputs:
            with self.assertRaises(
                    ParseError, msg=f'Did not get an exception for: {inp!r}'):
                results = self.parse(inp)
                print(f'\nresults: {results!r}')

    def testPositives(self):
        tests = [
            # basics
            ('', []),
            (',', ['', '']),
            (',,', ['', '', '']),
            ('a', ['a']),
            ('a,b', ['a', 'b']),
            ('a,b,c,d,e,f', 'a b c d e f'.split()),

            # surrounding whitespace
            (' a', ['a']),
            ('a ', ['a']),
            (' a ', ['a']),
            ('a, b', ['a', 'b']),
            ('  a  ,  b  ', ['a', 'b']),

            # commas in fields
            ('","', [',']),
            ('",",","', [',', ',']),
            ('"a  ,  b",b', ['a  ,  b', 'b']),

            # quotes in fields
            ('""""', ['"']),
            ('""""""', ['""']),
            ('"""a""",b,"""c"""', ['"a"', 'b', '"c"']),

            # single line combos
            (' "a", "b"', ['a', 'b']),
            ('  """"', ['"']),
            ('""""  ', ['"']),
            ('  """"  ', ['"']),
            (' """a""",  """b"""', ['"a"', '"b"']),
            ('  """",  ",",   ""","""', ['"', ',', '","']),

            # comments
            ('#a,b', []),

            # multiple line records
            ('"a\nb"', ['a\nb']),
            ('a,"b\nc"', ['a', 'b\nc']),
            ('a,"b\nc\n\n\n"', ['a', 'b\nc']),

            # MiddleKit enums
            ('a,Enums="b"', ['a', 'Enums="b"']),
            ("a,Enums='b'", ['a', "Enums='b'"]),
            ('a,"Enums=""b, c"""', ['a', 'Enums="b, c"']),
            ('''a,"Enums='b, c'"''', ['a', "Enums='b, c'"]),
        ]
        for inp, out in tests:
            if '\n' not in inp:
                # single line
                res = self.parse(inp)
                self.assertEqual(
                    res, out,
                    f'\ninput={inp!r}\nresult={res!r}\noutput={out!r}')
                res = self.parse(inp + '\n')
                self.assertEqual(
                    res, out,
                    f'\ninput={inp!r}\nresult={res!r}\noutput={out!r}')
            else:
                # multiple lines
                res = None
                for line in inp.splitlines():
                    self.assertIsNone(res)
                    res = self.parse(line)
                self.assertEqual(
                    res, out,
                    f'\ninput={inp!r}\nresult={res!r}\noutput={out!r}')
