"""Test Webware Mock Environment"""

import io
import sys
import unittest

import webware


class TestMocking(unittest.TestCase):

    def setUp(self):
        self.sysPath = sys.path
        self.webwarePath = webware.__path__[0]
        sys.path = [path for path in sys.path if path != self.webwarePath]
        self.sysStdout = sys.stdout
        sys.stdout = io.StringIO()
        self.getOutput = sys.stdout.getvalue

    def tearDown(self):
        sys.stdout = self.sysStdout
        sys.path = self.sysPath

    def testAddToSearchPath(self):
        assert self.webwarePath not in sys.path
        webware.addToSearchPath()
        assert self.webwarePath in sys.path

    def testLoadPlugins(self):
        webware.addToSearchPath()
        app = webware.mockAppWithPlugins(
            self.webwarePath, settings={'PrintPlugIns': True})
        self.assertEqual(app.__class__.__name__, 'MockApplication')
        output = self.getOutput().splitlines()
        output = [line.split(' at ', 1)[0] for line in output]
        self.assertEqual(output, [
            'Plug-ins list: MiscUtils, WebUtils, TaskKit, UserKit, PSP',
            'Loading plug-in: MiscUtils', 'Loading plug-in: WebUtils',
            'Loading plug-in: TaskKit', 'Loading plug-in: UserKit',
            'Loading plug-in: PSP', ''])
