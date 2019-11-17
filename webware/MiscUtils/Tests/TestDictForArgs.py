import unittest

from MiscUtils.DictForArgs import (
    DictForArgsError, dictForArgs, pyDictForArgs, expandDictWithExtras)


class TestDictForArgs(unittest.TestCase):

    def testPositives(self):
        cases = '''\
# Basics
x=1       == {'x': '1'}
x=1 y=2   == {'x': '1', 'y': '2'}

# Strings
x='a'     == {'x': 'a'}
x="a"     == {'x': 'a'}
x='a b'   == {'x': 'a b'}
x="a b"   == {'x': 'a b'}
x='a"'    == {'x': 'a"'}
x="a'"    == {'x': "a'"}
x="'a'"   == {'x': "'a'"}
x='"a"'   == {'x': '"a"'}

# No value
x         == {'x': '1'}
x y       == {'x': '1', 'y': '1'}
x y=2     == {'x': '1', 'y': '2'}
x=2 y     == {'x': '2', 'y': '1'}
'''
        self._testPositive('', {})
        self._testPositive(' ', {})
        cases = cases.splitlines()
        for case in cases:
            case = case.partition('#')[0].strip()
            if case:
                inp, out = case.split('==', 1)
                out = eval(out)
                self._testPositive(inp, out)

    def _testPositive(self, inp, out):
        res = dictForArgs(inp)
        self.assertEqual(
            res, out,
            f'Expecting: {out!r}\nGot: {res!r}\n')

    def testNegatives(self):
        cases = '''\
-
$
!@#$
'x'=5
x=5 'y'=6
'''
        cases = cases.splitlines()
        for case in cases:
            case = case.partition('#')[0].strip()
            if case:
                self._testNegative(case)

    def _testNegative(self, input_):
        try:
            res = dictForArgs(input_)
        except DictForArgsError:
            pass  # expected
        except Exception as err:
            self.fail(
                f'Expecting DictForArgError.\nGot error: {err!r}.\n')
        else:
            self.fail(
                f'Expecting DictForArgError.\nGot result: {res!r}.\n')

    def testPyDictForArgs(self):
        cases = '''\
x=1 == {'x': 1}
x=1; y=2 == {'x': 1, 'y': 2}
x='a' == {'x': 'a'}
x="a"; y="""b""" == {'x': 'a', 'y': 'b'}
x=(1, 2, 3) == {'x': (1, 2, 3)}
x=['a', 'b'] == {'x': ['a', 'b']}
x='a b'.split() == {'x': ['a', 'b']}
x=['a b'.split(), 1]; y={'a': 1} == {'x': [['a', 'b'], 1], 'y': {'a': 1}}
'''.splitlines()
        for case in cases:
            case = case.strip()
            if case:
                inp, out = case.split('==', 1)
                out = eval(out)
                self.assertEqual(pyDictForArgs(inp), out)

    def testExpandDictWithExtras(self):
        d = {'Name': 'foo', 'Extras': 'x=1 y=2'}
        result = expandDictWithExtras(d)
        self.assertEqual(result, {'Name': 'foo', 'x': '1', 'y': '2'})
        d = {'Name': 'foo', 'bar': 'z = 3'}
        result = expandDictWithExtras(d)
        self.assertEqual(result, d)
        result = expandDictWithExtras(d, key='bar', delKey=False)
        self.assertEqual(result, {'Name': 'foo', 'bar': 'z = 3', 'z': '3'})
