"""Test Webware Testing context"""

import time
import unittest

from .AppTest import AppTest


class TestTesting(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        ExtraPathInfo=False
    )

    def testStartPage(self):
        r = self.testApp.get('/').click('Testing')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Testing/')
        self.assertEqual(r.content_type, 'text/html')
        self.assertTrue(r.text.startswith('<!DOCTYPE html>'))
        r.mustcontain(
            '<title>Testing</title>',
            '<h2 style="text-align:center">Test cases</h2>',
            '<td>1.</td>', '<td>2.</td>', '<td>3.</td>', '<td>17.</td>')
        headings = [h.string for h in r.html.find('table').find('tr').children]
        self.assertEqual(headings, ['#', 'URL', 'Expectation'])

    def getTestCaseUrls(self, n, expect):
        r = self.testApp.get('/Testing/')
        case = list(r.html.find('table').find_all('tr')[n].children)
        self.assertEqual(case[0].string, f'{n}.')
        urls = [a['href'] for a in case[1].find_all('a')]
        self.assertGreater(len(urls), 0, 'Expected at least one URL')
        s = ' '.join(str(s) for s in case[2].contents)
        s = s.replace('<br/>', ' ')
        s = ' '.join(s.split())
        self.assertIn(expect, s, 'Unexpected test')
        return urls

    def getTestCaseUrl(self, n, expect):
        urls = self.getTestCaseUrls(n, expect)
        self.assertEqual(len(urls), 1, 'Expected only one URL')
        return urls[0]

    def testCase1(self):
        urls = self.getTestCaseUrls(1, 'Show /Examples/Welcome')
        for url in urls:
            r = self.testApp.get(url)
            self.assertEqual(r.status, '200 OK')
            r.mustcontain(
                '<title>Welcome</title>', 'Welcome to Webware for Python')

    def testCase2(self):
        urls = self.getTestCaseUrls(2, 'Show admin pages')
        for url in urls:
            r = self.testApp.get(url)
            self.assertEqual(r.status, '200 OK')
            r.mustcontain(
                '<title>LoginPage</title>',
                '<div id="CornerTitle">Webware Admin</div>',
                'Logins to admin pages are disabled')

    def testCase3(self):
        url = self.getTestCaseUrl(3, 'Redirect to /Admin/')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '301 Moved Permanently')
        r = r.follow()
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/')
        r.mustcontain('<div id="CornerTitle">Webware Admin</div>')

    def testCase4(self):
        url = self.getTestCaseUrl(4, 'Redirect to /Examples/')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '301 Moved Permanently')
        r = r.follow()
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/')
        r.mustcontain('<div id="CornerTitle">Webware Examples</div>')

    def testCase5(self):
        urls = self.getTestCaseUrls(5, 'Display the file')
        for url in urls:
            r = self.testApp.get(url)
            self.assertEqual(r.status, '200 OK')
            r.mustcontain('This is <code style="color:#558">File.html</code>'
                          ' in <code style="color:#555">/Testing/Dir/</code>')

    def testCase6(self):
        urls = self.getTestCaseUrls(6, 'Display the index file')
        for url in urls:
            r = self.testApp.get(url)
            if r.status_int == 301:
                r = r.follow()
            self.assertEqual(r.status, '200 OK')
            self.assertEqual(r.request.path, '/Testing/Dir/')
            r.mustcontain('This is <code style="color:#558">index.html</code>'
                          ' in <code style="color:#555">/Testing/Dir/</code>')

    def testCase7(self):
        urls = self.getTestCaseUrls(7, 'Not Found if ExtraPathInfo is not set')
        for url in urls:
            if self.app.setting('ExtraPathInfo'):
                r = self.testApp.get(url)
                self.assertEqual(r.status, '200 OK')
                r.mustcontain(
                    '<title>Welcome</title>', 'Welcome to Webware for Python',
                    no='extraURLPath')
            else:
                r = self.testApp.get(url, expect_errors=True)
                self.assertEqual(r.status, '404 Not Found')
                r.mustcontain(
                    '<h1 style="color:#008">Error 404</h1>',
                    'The page you requested,'
                    f' <strong>{url}</strong>, was not found')

    def testCase8(self):
        urls = self.getTestCaseUrls(8, 'Not Found or if ExtraPathInfo is set')
        for url in urls:
            if self.app.setting('ExtraPathInfo'):
                r = self.testApp.get(url)
                self.assertEqual(r.status, '200 OK')
                if url.startswith('/Examples/'):
                    url = url[9:]
                r.mustcontain(
                    '<title>Welcome</title>', 'Welcome to Webware for Python',
                    f'<li>extraURLPath: <code>{url}</code></li>')
            else:
                r = self.testApp.get(url, expect_errors=True)
                self.assertEqual(r.status, '404 Not Found')

    def testCase9(self):
        urls = self.getTestCaseUrls(9, 'test servlet displays extra path info')
        for url in urls:
            if self.app.setting('ExtraPathInfo'):
                r = self.testApp.get(url)
                self.assertEqual(r.status, '200 OK')
                extraPathInfo = url.partition('/Testing/Servlet')[2]
                extraPathInfo = extraPathInfo.partition('?')[0]
                r.mustcontain(
                    '<title>Test of extra path info.</title>',
                    '<h2>Webware Testing Servlet</h2>',
                    '<h3>Test of extra path info.</h3>',
                    f'<p>extraURLPath = <code>{extraPathInfo}</code></p>')
            else:
                r = self.testApp.get(url, expect_errors=True)
                self.assertEqual(r.status, '404 Not Found')

    def testCase10(self):
        url = self.getTestCaseUrl(10, 'IncludeURLTest test')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>IncludeURLTest</title>',
            '<h2>IncludeURLTest</h2>', '<h2>IncludeURLTest2</h2>',
            'Including the Main servlet of the Testing context:',
            '<h2 style="text-align:center">Test cases</h2>',
            '<h4>IncludeURLTest complete.</h4>')

    def testCase11(self):
        url = self.getTestCaseUrl(11, 'lower level IncludeURLTest test')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>IncludeURLTest2</title>',
            '<h2>IncludeURLTest2</h2>',
            'This is the second part of the URL test code.',
            no=['<h2>IncludeURLTest</h2>', 'Test cases'])

    def testCase12(self):
        url = self.getTestCaseUrl(12, 'Forward1Target')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Forward1Target</title>',
            '<h2><code>Forward1Target</code></h2>',
            no='Test cases')

    def testCase13(self):
        url = self.getTestCaseUrl(13, 'Dir/Forward2Target')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Forward2Target</title>',
            '<h2><code>Forward2Target</code></h2>',
            no='Test cases')

    def testCase14(self):
        url = self.getTestCaseUrl(14, 'Forward3Target')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Forward3Target</title>',
            '<h2><code>Forward3Target</code></h2>',
            no='Test cases')

    def testCase15(self):
        url = self.getTestCaseUrl(15, 'Test of WebUtils.FieldStorage')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>FieldStorage</title>',
            'FieldStorage class can be tested here', 'press the button',
            no=['Test cases', 'works as expected'])
        r = r.form.submit('testbutton')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>FieldStorage</title>',
            'Everything ok', 'FieldStorage works as expected',
            no=['Test cases', 'press the button'])
        r = r.click('Back to the test cases overview.')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Testing</title>', 'Test cases')

    def testCase16(self):
        url = self.getTestCaseUrl(16, 'Test of HTTPResponse.setCookie')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>SetCookie</title>', 'The time right now is:',
            '<h2>Cookies being sent:</h2>', "'onclose' sends:",
            no="'onclose' =")
        r = r.goto(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>SetCookie</title>', 'The time right now is:',
            '<h2>Cookies received:</h2>', "'onclose' =")

    def testCase17(self):
        url = self.getTestCaseUrl(17, 'TestIMS passed')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>TestIMS</title>',
            '<h2>Test If-Modified-Since support in Webware</h2>',
            'test requires a running web server')
        url = '/PSP/Examples/psplogo.png'
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.headers.get('Content-Type'), 'image/png')
        size = len(r.body)
        self.assertGreater(size, 0)
        lastMod = r.headers.get('Last-Modified')
        self.assertTrue(lastMod)
        r = self.testApp.get(url, headers={'If-Modified-Since': lastMod})
        self.assertEqual(r.status, '304 Not Modified')
        self.assertNotIn('Content-Type', r.headers)
        self.assertEqual(len(r.body), 0)
        arpaFormat = '%a, %d %b %Y %H:%M:%S GMT'
        t = time.strptime(lastMod, arpaFormat)
        t = (t[0] - 1,) + t[1:]  # one year before last modification
        beforeMod = time.strftime(arpaFormat, time.gmtime(time.mktime(t)))
        r = self.testApp.get(url, headers={'If-Modified-Since': beforeMod})
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.headers.get('Content-Type'), 'image/png')
        self.assertEqual(r.headers.get('Last-Modified'), lastMod)
        self.assertEqual(len(r.body), size)

    def testCase18(self):
        url = self.getTestCaseUrl(18, 'Servlet import test passed')
        r = self.testApp.get(url)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>ServletImport</title>',
            '<h2>Webware Servlet Import Test</h2>',
            '<h3>Test of servlet import details.</h3>',
            '<p>modName = <code>Testing.ServletImport</code></p>',
            '<p>modNameFromClass = <code>Testing.ServletImport</code></p>',
            'passed', no='failed')


class TestTestingWithExtraPathInfo(TestTesting):

    settings = dict(
        PrintConfigAtStartUp=False,
        ExtraPathInfo=True
    )
