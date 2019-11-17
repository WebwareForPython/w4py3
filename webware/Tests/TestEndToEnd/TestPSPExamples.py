"""Test Webware PSP context"""

import unittest

from .AppTest import AppTest


class TestPSPExamples(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        ClearPSPCacheOnStart=True
    )

    def testStartPage(self):
        r = self.testApp.get('/').click('^PSP$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/PSP/Examples/')
        self.assertEqual(r.content_type, 'text/html')
        self.assertTrue(r.text.startswith('<!DOCTYPE html>'))
        self.assertTrue(r.text.rstrip().endswith('</html>'))
        r.mustcontain(
            '<title>PSP Hello</title>',
            '<div id="CornerTitle">PSP Examples</div>',
            '<h1 style="text-align:center;color:navy">Hello from PSP!</h1>',
            '<img src="psplogo.png" alt="Python Server Pages">',
            'This is <strong>PSP</strong>.', 'Here are some examples.')

    def testIndex(self):
        r = self.testApp.get('/PSP/Examples/index.psp')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>PSP Hello</title>',
            '<div id="CornerTitle">PSP Examples</div>')

    def testHello(self):
        r = self.testApp.get('/PSP/Examples/').click('^Hello$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/PSP/Examples/Hello')
        r.mustcontain(
            '<title>PSP Hello</title>',
            '<div id="CornerTitle">PSP Examples</div>')

    def testBraces(self):
        r = self.testApp.get('/PSP/Examples/').click('^Braces')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/PSP/Examples/Braces')
        r.mustcontain(
            '<title>Braces Test</title>',
            '<h4 style="text-align:center;color:navy">'
            'Python Server Pages</h4>',
            '<h2 style="text-align:center">Braces Test</h2>',
            'just use <strong>braces</strong>',
            "<li>I'm number 1</li>", "<li>I'm number 5</li>",
            no="number 6")

    def testSamplePage(self):
        r = self.testApp.get('/PSP/Examples/').click('^PSPTests$', index=0)
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/PSP/Examples/PSPTests')
        r.mustcontain(
            '<title>PSP Tests Page</title>',
            '<h1 style="text-align:center;color:navy">Hello from PSP!</h1>',
            'This is the sample/test page',
            '<p>Hello from included file!<p>',
            'This is an HTML file that is dynamically inserted.',
            '<h4>Below is a loop test:</h4>',
            '<ul><li>Outer loop: 1', '<li>Inner loop: 2',
            '<a href="PSPTests-Braces">braces</a>'
            ' can make things easier here.</p>',
            '<th style="text-align:left">Path Info:</th>',
            '<td>/PSP/Examples/PSPTests</td>',
            '<h4>Request Variables:</h4>',
            '<td style="color:red;font-size:small">REQUEST_METHOD&nbsp;</td>',
            '<td style="color:blue;font-size:small">GET</td>',
            '<h4>Comments:</h4>', 'Nothing should be visible here.',
            '<p>I\'m a method. <b style="color:maroon">Howdy!</b></p>',
            '<b style="color:green">It\'s True</b></p>',
            "<p><strong>That's all, folks.</strong></p>",
            no=['test page uses <a href="Braces"><strong>braces</strong></a>',
                'Comment check', 'not even in Python file'])

    def testSamplePageBraces(self):
        r = self.testApp.get('/PSP/Examples/').click('^PSPTests-Braces$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/PSP/Examples/PSPTests-Braces')
        r.mustcontain(
            '<title>PSP Tests Page - Braces</title>',
            '<h1 style="text-align:center;color:navy">Hello from PSP!</h1>',
            'This is the sample/test page',
            'test page uses <a href="Braces"><strong>braces</strong></a>',
            '<p>Hello from included file!<p>',
            'This is an HTML file that is dynamically inserted.',
            '<h4>Below is a loop test:</h4>',
            '<ul><li>Outer loop: 1', '<li>Inner loop: 2',
            'The use of braces, while not good for normal Python,'
            ' does make things easier here',
            '<th style="text-align:left">Path Info:</th>',
            '<td>/PSP/Examples/PSPTests-Braces</td>',
            '<h4>Request Variables:</h4>',
            '<td style="color:red;font-size:small">REQUEST_METHOD&nbsp;</td>',
            '<td style="color:blue;font-size:small">GET</td>',
            '<h4>Comments:</h4>', 'Nothing should be visible here.',
            '<p>I\'m a method. <b style="color:maroon">Howdy!</b></p>',
            '<b style="color:green">It\'s True</b></p>',
            "<p><strong>That's all, folks.</strong></p>",
            no=['Comment check', 'not even in Python file'])

    def testMyInclude(self):
        r = self.testApp.get('/PSP/Examples/my_include.psp')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Hello from included file!')

    def testAnotherInclude(self):
        r = self.testApp.get('/PSP/Examples/PSPinclude.psp')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('The current time is:', '<hr>')
