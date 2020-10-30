import time
import unittest

from MiscUtils.Funcs import (
    asclocaltime, commas, charWrap, wordWrap, excstr,
    hostName, localIP, localTimeDelta, positiveId,
    safeDescription, timestamp, uniqueId, valueForString)


class TestFuncs(unittest.TestCase):
    """Unit tests for the functions in MiscUtils.Funcs."""

    def testCommas(self):
        testSpec = '''
            0 '0'
            0.0 '0.0'
            1 '1'
            11 '11'
            111 '111'
            1111 '1,111'
            11111 '11,111'
            1.0 '1.0'
            11.0 '11.0'
            1.15 '1.15'
            12345.127 '12,345.127'
            -1 '-1'
            -11 '-11'
            -111 '-111'
            -1111 '-1,111'
            -11111 '-11,111'
        '''
        tests = testSpec.split()
        count = len(tests)
        i = 0
        while i < count:
            source = eval(tests[i])
            result = eval(tests[i+1])
            self.assertEqual(commas(source), result)
            # also try the source as a string instead of a number
            source = eval(f"'{tests[i]}'")
            self.assertEqual(commas(source), result)
            i += 2

    def testCharWrap(self):
        self.assertEqual(charWrap("""
            Sparse is better than dense.
            Readability counts.""", 34, 16), """
            Sparse is better than
                dense.
            Readability counts.""")

    def testWordWrap(self):
        # an example with some spaces and newlines
        msg = '''Arthur:  "The Lady of the Lake, her arm clad in the purest \
shimmering samite, held aloft Excalibur from the bosom of the water, \
signifying by Divine Providence that I, Arthur, was to carry \
Excalibur. That is why I am your king!"

Dennis:  "Listen. Strange women lying in ponds distributing swords is \
no basis for a system of government. Supreme executive power derives \
from a mandate from the masses, not from some farcical aquatic ceremony!"'''

        for margin in range(20, 200, 29):
            if margin == 78:
                s = wordWrap(msg)
            else:
                s = wordWrap(msg, margin)
            for line in s.splitlines():
                self.assertLessEqual(
                    len(line), margin,
                    f'len={len(line)}, margin={margin}, line={line!r}')
            self.assertEqual(msg.split(), s.split())

    def testExcstr(self):
        self.assertEqual(excstr(None), None)
        self.assertEqual(
            excstr(ValueError('Kawoom!')), 'ValueError: Kawoom!')

    def testHostName(self):
        # About all we can do is invoke hostName() to see that no exceptions
        # are thrown, and do a little type checking on the return type.
        host = hostName()
        self.assertIsNotNone(host)
        self.assertIsInstance(host, str)
        self.assertEqual(host, host.lower())

    def testLocalIP(self):
        ip = localIP()
        self.assertTrue(ip)
        self.assertFalse(ip.startswith('127.'))
        self.assertEqual(localIP(), ip)  # second invocation
        self.assertEqual(localIP(useCache=None), ip)
        # ignore if the following tests fetch the WSL address
        ips = (ip, '192.168.80.1', '172.25.112.1')
        self.assertIn(
            localIP(remote=None, useCache=None), ips,
            'See if this works: localIP(remote=None).'
            ' If this fails, dont worry.')
        self.assertIn(
            localIP(remote=('www.hostname.and.domain.are.invalid', 80),
                    useCache=None), ips)

    def testPositiveId(self):
        # About all we can do is invoke positiveId()
        # to see that no exceptions are thrown and the result is positive.
        self.assertIsInstance(positiveId(self), int)
        self.assertGreater(positiveId(self), 0)

    def testSafeDescription(self):
        desc = safeDescription

        # basics:
        s = desc(1).replace('type=', 'class=')
        self.assertEqual(s, "what=1 class=<class 'int'>")
        s = desc(1, 'x').replace('type=', 'class=')
        self.assertEqual(s, "x=1 class=<class 'int'>")
        s = desc('x').replace('type=', 'class=')
        s = s.replace("<type 'string'>", "<class 'str'>")
        self.assertEqual(s, "what='x' class=<class 'str'>")

        class Dummy:
            pass

        s = desc(Dummy())
        self.assertIn('Dummy object', s, repr(s))

        # okay now test that safeDescription eats exceptions from repr():
        class Bogus:
            def __repr__(self):
                raise KeyError('bogus')

        b = Bogus()
        try:
            s = desc(b)
        except Exception:
            s = 'failure: should not throw exception'

        self.assertIn("(exception from repr(obj): KeyError: 'bogus')", s)

    def testAsclocaltime(self):
        self.assertEqual(len(asclocaltime()), 24)
        t = time.time()
        self.assertEqual(asclocaltime(t), time.asctime(time.localtime(t)))

    def testTimestamp(self):
        d = timestamp()
        self.assertIsInstance(d, dict)
        self.assertEqual(','.join(sorted(d)), 'condensed,dashed,pretty,tuple')
        self.assertEqual(len(d['tuple']), 6)
        self.assertEqual(len(d['condensed']), 14)
        self.assertEqual(len(d['pretty']), 19)
        self.assertEqual(len(d['dashed']), 19)
        t = time.time()
        d = timestamp(t)
        t = time.localtime(t)[:6]
        self.assertEqual(d['tuple'], t)
        self.assertEqual(
            d['condensed'], '{:4d}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(*t))
        self.assertEqual(
            d['condensed'],
            d['pretty'].replace('-', '').replace(':', '').replace(' ', ''))
        self.assertEqual(d['condensed'], d['dashed'].replace('-', ''))

    def testLocalTimeDelta(self):
        d = localTimeDelta()
        self.assertEqual(d.microseconds, 0)
        self.assertEqual(d.seconds % 3600, 0)
        self.assertTrue(-1 <= d.days < 1)
        d = localTimeDelta(time.time())
        self.assertEqual(d.microseconds, 0)
        self.assertEqual(d.seconds % 3600, 0)
        self.assertTrue(-1 <= d.days < 1)

    def testUniqueId(self):
        past = set()

        def checkId(i):
            self.assertIsInstance(i, str, type(i))
            self.assertEqual(len(i), 32)
            for c in i:
                self.assertTrue(c in '0123456789abcdef')
            self.assertFalse(i in past)
            past.add(i)

        for n in range(10):
            checkId(uniqueId())
            checkId(uniqueId(None))
            checkId(uniqueId(n))
            checkId(uniqueId(forObject=checkId))

    def testValueForString(self):
        evalCases = '''
            1
            9223372036854775808
            5.5
            True
            False
            None
            [1]
            ['a']
            {'x':1}
            (1, 2, 3)
            'a'
            "z"
            """1234"""
        '''

        stringCases = '''
            kjasdfkasdf
            2389234lkdsflkjsdf
            *09809
        '''

        evalCases = [s.strip() for s in evalCases.strip().splitlines()]
        for case in evalCases:
            value = valueForString(case)
            evalCase = eval(case)
            self.assertEqual(
                value, evalCase,
                f'case={case!r}, valueForString()={value!r},'
                f' eval()={evalCase!r}')

        stringCases = [s.strip() for s in stringCases.strip().splitlines()]
        for case in stringCases:
            value = valueForString(case)
            self.assertEqual(
                value, case,
                f'case={case!r}, valueForString()={value!r}')
