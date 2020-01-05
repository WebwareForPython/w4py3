"""Test Webware Testing context"""

import unittest

from .AppTest import AppTest


class TestContextMap(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        ExtraPathInfo=False,
        Contexts={'Testing': 'Testing', 'default': 'Testing'}
    )

    def testStartPage(self):
        r = self.testApp.get('/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/')
        r.mustcontain('<title>Testing</title>')

    def testContextPage(self):
        r = self.testApp.get('/Testing/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Testing/')
        r.mustcontain('<title>Testing</title>')

    def testBadContextPage(self):
        r = self.testApp.get('/default/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)
        r = self.testApp.get('/TestAlias/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)


class TestAliasedContext(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        ExtraPathInfo=False,
        Contexts={'TestAlias': 'Testing', 'default': 'TestAlias'}
    )

    def testStartPage(self):
        r = self.testApp.get('/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/')
        r.mustcontain('<title>Testing</title>')

    def testContextPage(self):
        r = self.testApp.get('/TestAlias/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/TestAlias/')
        r.mustcontain('<title>Testing</title>')

    def testBadContextPage(self):
        r = self.testApp.get('/default/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)
        r = self.testApp.get('/Testing/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)


class TestOnlyDefaultContext(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        ExtraPathInfo=False,
        Contexts={'default': 'Testing'}
    )

    def testStartPage(self):
        r = self.testApp.get('/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/')
        r.mustcontain('<title>Testing</title>')

    def testContextPage(self):
        r = self.testApp.get('/default/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/default/')
        r.mustcontain('<title>Testing</title>')

    def testBadContextPage(self):
        r = self.testApp.get('/Testing/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)
        r = self.testApp.get('/TestAlias/', expect_errors=True)
        self.assertEqual(r.status, '404 Not Found', r.status)
