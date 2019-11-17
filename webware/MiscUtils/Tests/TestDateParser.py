import unittest

from MiscUtils.DateParser import parseDate, parseTime, parseDateTime


class TestDateTimeParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import datetime
        self.assertIsInstance(
            parseDateTime('Mon Jul 21 02:56:20 1969'), datetime)

    def assertParses(self, s):
        self.assertEqual(parseDateTime(s).isoformat(), '1969-07-21T02:56:20')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('19690721T02:56:20')

    def testWrongFormat(self):
        self.assertRaises(ValueError,
                          parseDateTime, 'Mon Jul 21 02:56:20 19691')
        self.assertRaises(ValueError,
                          parseDateTime, '19691')

    def testDateUtilParser(self):
        try:
            # pylint: disable=unused-import
            from dateutil.parser import parse  # noqa: F401
        except ImportError:
            hasDateUtil = False
        else:
            hasDateUtil = True
        testString = 'July 21, 1969, 2:56:20'
        if hasDateUtil:
            self.assertParses(testString)
        else:
            self.assertRaises(ValueError, parseDateTime, testString)


class TestDateParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import date
        self.assertIsInstance(parseDate('Mon Jul 21 02:56:20 1969'), date)

    def assertParses(self, s):
        self.assertEqual(parseDate(s).isoformat(), '1969-07-21')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('19690721T02:56:20')
        self.assertParses('1969-07-21')
        self.assertParses('19690721')

    def testWrongFormat(self):
        self.assertRaises(ValueError,
                          parseDateTime, 'Mon Jul 21 02:56:20 19691')
        self.assertRaises(ValueError,
                          parseDateTime, '19691')


class TestTimeParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import time
        self.assertIsInstance(parseTime('Mon Jul 21 02:56:20 1969'), time)

    def assertParses(self, s):
        self.assertEqual(parseTime(s).isoformat(), '02:56:20')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('02:56:20')

    def testWrongFormat(self):
        self.assertRaises(ValueError,
                          parseDateTime, 'Mon Jul 21 02:65:20 1969')
        self.assertRaises(ValueError,
                          parseDateTime, '02:65')
