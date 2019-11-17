import unittest

from MiscUtils.DateInterval import timeEncode, timeDecode


class TestDateInterval(unittest.TestCase):

    def testTimeEncode(self):
        self.assertEqual(timeEncode(1), '1s')
        self.assertEqual(timeEncode(60), '1m')
        self.assertEqual(timeEncode(176403), '2d1h3s')
        self.assertEqual(timeEncode(349380), '4d1h3m')
        self.assertEqual(timeEncode(38898367), '1y2b3w4d5h6m7s')

    def testTimeDecode(self):
        self.assertEqual(timeDecode('1s'), 1)
        self.assertEqual(timeDecode('1h2d3s'), 176403)
        self.assertEqual(timeDecode('2d1h3s'), 176403)
        self.assertEqual(timeDecode('1h4d3m'), 349380)
        self.assertEqual(timeDecode('3m4d1h'), 349380)
        self.assertEqual(timeDecode('1y2b3w4d5h6m7s'), 38898367)
        self.assertEqual(timeDecode('0y1b2w3d4h5m6s'), 4075506)
        self.assertEqual(timeDecode('6s5m4h3d2w1b0y'), 4075506)
        self.assertEqual(timeDecode('(3s-2d-1h)'), 176403)
        try:
            timeDecode('1h5n')
        except ValueError as e:
            self.assertEqual(str(e), 'Invalid unit of time: n')
