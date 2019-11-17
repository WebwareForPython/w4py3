"""Automated tests for PSPUtils

Copyright (c) by Winston Wolff, 2004 https://www.stratolab.com
"""

import unittest

from PSP import PSPUtils


class TestUtils(unittest.TestCase):

    def testRemoveQuotes(self):
        self.assertEqual(PSPUtils.removeQuotes(
            r'html <% psp %\\> html'), 'html <% psp %> html')

    def testIsExpression(self):
        self.assertEqual(PSPUtils.isExpression('<%= bla'), False)
        self.assertEqual(PSPUtils.isExpression('bla %>'), False)
        self.assertEqual(PSPUtils.isExpression('<%= bla %>'), True)
        self.assertEqual(PSPUtils.isExpression('bla <%= bla %>'), False)
        self.assertEqual(PSPUtils.isExpression('<%= bla %> bla'), False)

    def testGetExpr(self):
        self.assertEqual(PSPUtils.getExpr('<%= bla'), '')
        self.assertEqual(PSPUtils.getExpr('bla %>'), '')
        self.assertEqual(PSPUtils.getExpr('<%= bla %>'), ' bla ')
        self.assertEqual(PSPUtils.getExpr('bla <%= bla %>'), '')
        self.assertEqual(PSPUtils.getExpr('<%= bla %> bla'), '')

    def testSplitLines(self):
        self.assertEqual(PSPUtils.splitLines(
            'foo\nbar\n'), ['foo', 'bar'])
        self.assertEqual(PSPUtils.splitLines(
            'foo\rbar\r'), ['foo', 'bar'])
        self.assertEqual(PSPUtils.splitLines(
            'foo\rbar\n', True), ['foo\r', 'bar\n'])

    def testStartsNewBlock(self):
        startsNewBlock = PSPUtils.startsNewBlock
        self.assertEqual(startsNewBlock('x = 1'), False)
        self.assertEqual(startsNewBlock('if x == 1:'), True)
        self.assertEqual(startsNewBlock('x = 1 # bla:'), False)
        self.assertEqual(startsNewBlock('if x == 1: # bla'), True)
        self.assertEqual(startsNewBlock('if x == 1: bla'), False)
        self.assertEqual(startsNewBlock('x = "if x == 1:" # bla:'), False)

    def testCheckAttributes(self):
        checkAttributes = PSPUtils.checkAttributes
        for attrs in (dict(man=1), dict(man=1, opt=1)):
            checkAttributes('test', attrs, (['man'], ['opt']))
        PSPParserException = PSPUtils.PSPParserException
        for attrs in (dict(), dict(opt=1), dict(man=1, noopt=1)):
            self.assertRaises(
                PSPParserException, checkAttributes,
                'test', attrs, (['man'], ['opt']))
        self.assertRaises(
            PSPParserException, checkAttributes,
            'test', dict(opt=1), (['man1', 'man2'], []))
        self.assertRaises(
            PSPParserException, checkAttributes,
            'test', dict(man=1), ([], ['opt1', 'opt2']))

    def testNormalizeIndentation(self):
        normalizeIndentation = PSPUtils.normalizeIndentation

        before = """
    def add(a,b):
      return a+b"""
        expected = """
def add(a,b):
  return a+b"""
        self.assertEqual(normalizeIndentation(before), expected)

        # Comments should be ignored for the un-indentation
        before = """
# Will comments throw off the indentation?
    def add(a,b):
      return a+b"""
        expected = """
# Will comments throw off the indentation?
def add(a,b):
  return a+b"""
        self.assertEqual(normalizeIndentation(before), expected)

        # Will blank lines cause a problem?
        before = """
# Will blank lines cause a problem?

    def add(a,b):

      return a+b"""
        expected = """
# Will blank lines cause a problem?

def add(a,b):

  return a+b"""
        self.assertEqual(normalizeIndentation(before), expected)

        # Tab chars OK?
        before = '\tdef add(a,b):\n\t\treturn a+b'
        expected = 'def add(a,b):\n\treturn a+b'
        self.assertEqual(normalizeIndentation(before), expected)

        # Different line endings OK?
        before = '#line endings\r  def add(a,b):\r  \r  return a+b'
        expected = '#line endings\rdef add(a,b):\r\rreturn a+b'
        self.assertEqual(normalizeIndentation(before), expected)
