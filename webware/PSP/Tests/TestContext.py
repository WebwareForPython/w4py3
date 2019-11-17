"""Automated tests for the PSP Context"""

import os
import unittest

from PSP.Context import PSPCLContext


class TestCLContext(unittest.TestCase):

    def testInit(self):
        pspFile = '/files/PSP/ContextTest.psp'.replace('/', os.sep)
        clc = PSPCLContext(pspFile)
        self.assertEqual(clc.getFullPspFileName(), pspFile)
        self.assertEqual(clc.getPspFileName(), 'ContextTest.psp')
        self.assertEqual(clc.getBaseUri(), '/files/PSP'.replace('/', os.sep))

    def testPythonFileEncoding(self):
        clc = PSPCLContext('test.psp')
        self.assertEqual(clc.getPythonFileEncoding(), None)
        clc.setPythonFileEncoding('latin-1')
        self.assertEqual(clc.getPythonFileEncoding(), 'latin-1')

    def testResolveRelativeURI(self):
        pspFile = '/files/PSP/Test1.psp'.replace('/', os.sep)
        clc = PSPCLContext(pspFile)
        uri = clc.resolveRelativeURI('Test2.psp')
        self.assertEqual(uri, '/files/PSP/Test2.psp'.replace('/', os.sep))
        self.assertEqual(clc.resolveRelativeURI(uri), uri)

    def testPSPReader(self):
        reader = object()
        clc = PSPCLContext('test.psp')
        clc.setPSPReader(reader)
        self.assertEqual(clc.getReader(), reader)

    def testClassName(self):
        clc = PSPCLContext('test.psp')
        clc.setClassName('ContextTestClass')
        self.assertEqual(clc.getServletClassName(), 'ContextTestClass')
