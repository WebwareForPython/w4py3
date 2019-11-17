"""Automated tests for the PSP BraceConverter

Contributed 2000-09-04 by Dave Wallace
"""

import unittest
from io import StringIO

from PSP.BraceConverter import BraceConverter
from PSP.ServletWriter import ServletWriter


class DummyWriter(ServletWriter):  # pylint: disable=abstract-method
    """Dummy writer for testing."""

    def __init__(self):  # pylint: disable=super-init-not-called
        self._file = StringIO()
        self._tabCount = 3  # base indentation of our test examples
        self._blockCount = 0
        self._indentSpaces = ServletWriter._spaces
        self._useTabs = False
        self._useBraces = False
        self._indent = '    '
        self._userIndent = ServletWriter._emptyString

    def getOutput(self):
        return self._file.getvalue()

    def close(self):
        self._file.close()


class TestBraceConverter(unittest.TestCase):

    @staticmethod
    def trim(text):
        return '\n'.join(filter(None, map(str.rstrip, text.splitlines())))

    def assertParses(self, psp, expected):
        dummyWriter = DummyWriter()
        braceConverter = BraceConverter()
        for line in psp.splitlines():
            braceConverter.parseLine(line, dummyWriter)
        output = dummyWriter.getOutput()
        dummyWriter.close()
        output, expected = list(map(self.trim, (output, expected)))
        self.assertEqual(
            output, expected,
            f'\n\nOutput:\n{output}\n\nExpected:\n{expected}\n')

    def testSimple(self):
        self.assertParses('''
            if a == b: { return True } else: { return False }
        ''', '''
            if a == b:
                return True
            else:
                return False
        ''')

    def testDict(self):
        self.assertParses('''
            for x in range(10): { q = {
            'test': x
            }
            print(x)
            }
        ''', '''
            for x in range(10):
                q = {
                'test': x
                }
                print(x)
        ''')

    def testNestedDict(self):
        self.assertParses(r'''
            if x: { q = {'test': x}; print(x)} else: { print("\"done\"") #""}{
            x = { 'test1': {'sub2': {'subsub1': 2}} # yee ha
            }
            } print("all done")
        ''', r'''
            if x:
                q = {'test': x}; print(x)
            else:
                print("\"done\"") #""}{
                x = { 'test1': {'sub2': {'subsub1': 2}} # yee ha
                }
            print("all done")
        ''')
