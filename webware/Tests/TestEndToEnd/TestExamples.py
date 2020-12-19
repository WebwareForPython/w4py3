"""Test Webware Example context"""

import os
import unittest
from time import sleep

from .AppTest import AppTest


class TestExamples(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False
    )

    def setUp(self):
        AppTest.setUp(self)
        self.testApp.reset()

    @staticmethod
    def removeDemoDatabase():
        # pylint: disable=unused-variable
        for i in range(20):
            if not os.path.exists('demo.db'):
                break
            try:
                os.remove('demo.db')
            except OSError:
                sleep(.5)
            else:
                break

    def testStartPage(self):
        r = self.testApp.get('/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.status_int, 200)
        self.assertEqual(r.content_type, 'text/html')
        self.assertTrue(r.text.startswith('<!DOCTYPE html>'))
        self.assertTrue(r.text.rstrip().endswith('</html>'))
        from sys import version
        pythonVersion = version.split(None, 1)[0]
        webwareVersion = self.app.webwareVersionString()
        r.mustcontain(
            '<html lang="en">', '<head>', '</head>',
            '<title>Welcome</title>', '<meta charset="utf-8">',
            '<style>', 'table.NiceTable {', '</style>',
            '<body style="color:black;background-color:white">', '</body>',
            '<div id="Page">', '<div id="CornerTitle">Webware Examples</div>',
            '<div id="Banner">Welcome</div>', '<div id="Sidebar">',
            '<div class="MenuHeading">Examples</div>',
            '<div class="MenuHeading">Other</div>',
            '<div class="MenuHeading">Contexts</div>',
            '<div class="MenuHeading">E-mail</div>', 'webware-discuss',
            '<div class="MenuHeading">Exits</div>',
            '<a href="https://webwareforpython.github.io/w4py3/">Webware</a>',
            '<a href="https://www.python.org/">Python</a>',
            '<div class="MenuHeading">Versions</div>',
            f'>Webware {webwareVersion}<', f'>Python {pythonVersion}<',
            '<div id="Content">',
            f'<h2>Welcome to Webware for Python {webwareVersion}!</h2>',
            'Along the side of this page you will see various links')

    def testWelcome(self):
        r = self.testApp.get('/Welcome')
        self.assertEqual(r.status, '200 OK')
        version = self.app.webwareVersionString()
        r.mustcontain(
            '<title>Welcome</title>',
            f'<h2>Welcome to Webware for Python {version}!</h2>')

    def testMenu(self):
        r = self.testApp.get('/Examples/')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/')
        r.mustcontain(
            '<title>Welcome</title>',
            '<div class="MenuHeading">Examples</div>')
        r = r.click('^Welcome$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/Welcome')
        r.mustcontain('<title>Welcome</title>')
        r = r.click('^ShowTime$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/ShowTime')
        r.mustcontain(
            '<title>ShowTime</title>', 'The current time is:')
        r = r.click('^CountVisits$')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/CountVisits')
        r.mustcontain(
            '<title>CountVisits</title>', '<h3>Counting Visits</h3>')
        r = r.click('^Error')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/Error')
        r.mustcontain(
            '<title>Error raising Example</title>', '<h1>Error Test</h1>')

    def testShowTime(self):
        r = self.testApp.get('/ShowTime')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('<title>ShowTime</title>', 'The current time is:')

    def checkTimes(self, r, n):
        s = '' if n == 1 else 's'
        p = ('<p>You\'ve been here <strong style="background-color:yellow">'
             f'&nbsp;{n}&nbsp;</strong> time{s}.</p>')
        self.assertIn(p, r)

    def testCountVisits(self):
        r = self.testApp.get('/CountVisits')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>CountVisits</title>',
            '<h3>Counting Visits</h3>',
            'This page records your visits using a session object.')
        self.checkTimes(r, 1)
        r = r.click('revisit')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 2)
        r = r.goto('CountVisits')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 3)
        r = r.goto('/CountVisits')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 4)
        r = r.goto('/Examples/CountVisits')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 5)
        r = r.click('expire')
        self.assertEqual(r.status, '302 Found')
        r = r.follow()
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Examples/CountVisits')
        self.checkTimes(r, 1)
        r = r.goto('CountVisits')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 2)

    def testError(self):
        r = self.testApp.get('/Error')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Error raising Example</title>',
            '<h1>Error Test</h1>',
            '<form action="Error" method="post">',
            "Don't click this button!",
            no=['Traceback', 'raise error', 'that button!'])
        r = r.form.submit(expect_errors=True)
        self.assertEqual(r.status, '500 Server Error')
        r.mustcontain(
            '<title>Error</title>',
            '<h2 class="section">Error</h2>',
            'The site is having technical difficulties with this page.',
            '<h2 class="section">Traceback</h2>',
            'self.runTransactionViaServlet', 'raise error',
            'RuntimeError: You clicked that button!',
            no=['CustomError', 'SystemError'])
        r = r.goto('/Error')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('<title>Error raising Example</title>')
        r.form['error'].select(text='System Error')
        r = r.form.submit(expect_errors=True)
        self.assertEqual(r.status, '500 Server Error')
        r.mustcontain(
            '<title>Error</title>',
            'SystemError: You clicked that button!',
            no=['RuntimeError', 'CustomError'])
        r = r.goto('/Error')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('<title>Error raising Example</title>')
        r.form['error'].select(text='Custom Error')
        r = r.form.submit(expect_errors=True)
        self.assertEqual(r.status, '500 Server Error')
        r.mustcontain(
            '<title>Error</title>',
            'CustomError: You clicked that button!',
            no=['RuntimeError', 'SystemError'])

    def testView(self):
        r = self.testApp.get('/View')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>View</title>',
            '<h2>View the source of a Webware servlet.</h2>',
            'for your viewing pleasure')
        r = r.click('View source')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path_qs, '/Examples/View?filename=View.py')
        r.mustcontain(
            '<title>', 'View.py</title>',
            '<pre>', '.highlight .kn {',
            '<span class="kn">from</span>', '</pre>')
        r = r.goto('/View?filename=Nada')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Error</title>',
            '<h3 style="color:#a00">Error</h3>',
            "<p>The requested file 'Nada'"
            " does not exist in the proper directory.</p>")
        r = r.goto('/View?filename=Error.py')
        r.mustcontain(
            '<title>', 'Error.py</title>',
            '<span class="nc">Error</span>',
            '<span class="n">ExamplePage</span>')

    def testIntrospect(self):
        r = self.testApp.get('/Introspect')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Introspect</title>',
            'shows the values for various Python expressions',
            'list(globals())', 'ExamplePage')

    def testColors(self):
        r = self.testApp.get('/Colors')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Colors</title>', '<h3>Color Table Demo</h3>',
            '<body style="color:black;background-color:#FFFFFF">',
            '<div style="text-align:center;color:black">',
            no='<div style="text-align:center;color:white">')
        r.form['bgColor'] = '#CC3366'
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Colors</title>', '<h3>Color Table Demo</h3>',
            '<body style="color:black;background-color:#CC3366">',
            '<div style="text-align:center;color:white">',
            no='<div style="text-align:center;color:black">')

    def testListBox(self):
        r = self.testApp.get('/ListBox')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>ListBox</title>', '<h2>List box example.</h2>',
            '--- empty ---', no='New item')
        r = r.form.submit('_action_new')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'List box example', 'New item 1',
            no=['empty', 'item 2'])
        r = r.form.submit('_action_new').form.submit('_action_new')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'List box example', 'New item 1', 'New item 2', 'New item 3',
            no=['empty', 'item 4'])
        r = r.form.submit('_action_delete')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'List box example', 'must select a row to delete',
            'New item 1', 'New item 2', 'New item 3')
        r.form['items'].select_multiple(texts=['New item 2'])
        r = r.form.submit('_action_delete')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'List box example', 'New item 1', 'New item 3',
            no=['must select', 'empty', 'item 2'])
        r.form['items'].select_multiple(texts=['New item 1', 'New item 3'])
        r = r.form.submit('_action_delete')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'List box example', '--- empty ---',
            no=['must select', 'New item', 'item 1', 'item 2', 'item 3'])
        r.mustcontain('name="items" size="10" style="width:250pt;')
        r = r.form.submit('_action_taller')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('name="items" size="11" style="width:250pt;')
        r = r.form.submit('_action_shorter')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('name="items" size="10" style="width:250pt;')
        r = r.form.submit('_action_wider')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('name="items" size="10" style="width:280pt;')
        r = r.form.submit('_action_narrower')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('name="items" size="10" style="width:250pt;')

    def testForward(self):
        r = self.testApp.get('/Forward')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Forward</title>',
            'This is the <em>Forward</em> servlet speaking.',
            'Hello from IncludeMe')

    def testSecureCountVisits(self):
        r = self.testApp.get('/SecureCountVisits')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Log In</title>', 'Please log in', no='failed')
        r.form['username'] = 'alice'
        r.form['password'] = 'bob'
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Log In</title>', 'Please log in',
            'Login failed', 'try again')
        r.form['username'] = 'alice'
        r.form['password'] = 'alice'
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>SecureCountVisits</title>',
            '<h3>Counting Visits on a Secured Page</h3>',
            'This page records your visits using a session object.',
            'Authenticated user is <strong>alice</strong>.',
            no=['failed', 'log in'])
        self.checkTimes(r, 1)
        r = r.click('Revisit this page')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 2)
        r = r.click('^SecureCountVisits$')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 3)
        r = r.goto('/SecureCountVisits')
        self.assertEqual(r.status, '200 OK')
        self.checkTimes(r, 4)
        r = r.click('Logout')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Log In</title>', 'Please log in',
            no='Counting Visits')
        r.form['username'] = 'bob'
        r.form['password'] = 'bob'
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>SecureCountVisits</title>',
            'Authenticated user is <strong>bob</strong>.')
        r = r.click('Logout')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('<title>Log In</title>', no='Counting Visits')

    def testFileUpload(self):
        r = self.testApp.get('/FileUpload')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>File Upload Example</title>',
            '<h1>Upload Test</h1>',
            'This servlet shows how to handle uploaded files.',
            '<form action="FileUpload"', 'multipart/form-data', '</form>',
            no="Here's the file")
        from webtest import Upload  # pylint: disable=import-error
        r.form['filename'] = Upload(
            'README.txt', b'Hello from uploaded file!', 'text/plain')
        r = r.form.submit()
        r.mustcontain(
            '<title>File Upload Example</title>',
            '<h1>Upload Test</h1>',
            "Here's the file you submitted:",
            '<th>name</th><td><strong>README.txt</strong></td>',
            '<tr><th>disposition</th><td>form-data</td></tr>',
            "<tr><th>disposition_options</th><td>"
            "{'name': 'filename', 'filename': 'README.txt'}</td></tr>",
            '<tr><th>headers</th><td>Content-Disposition: form-data;'
            ' name="filename"; filename="README.txt"',
            'Content-Type: text/plain',
            '<tr><th>size</th><td>25 bytes</td></tr>',
            '<tr><th style="vertical-align:top">contents</th>',
            '<pre style=', 'Hello from uploaded file!', '</pre>',
            no='<form')

    def testRequestInformation(self):
        r = self.testApp.get('/RequestInformation')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>RequestInformation</title>',
            '<h3>Request Variables</h3>',
            '<p>The following table shows the values'
            ' for three important request variables.</p>',
            '>environ()<',
            '<td>PATH_INFO</td><td>/RequestInformation</td>',
            '<td>QUERY_STRING</td>', '<td>REQUEST_METHOD</td>',
            '<td>paste.testing</td><td>True</td>',
            '<td>wsgi.input</td>', '<td>wsgi.version</td>',
            no=['fields()', '<td>answer</td>',
                '>cookies()<', '<td>TestCookieName</td>'])
        r = r.click('Reload the page to see them.')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h3>Request Variables</h3>',
            'The following table shows the values',
            '>environ()<',
            '<td>PATH_INFO</td><td>/RequestInformation</td>',
            '>cookies()<',
            '<td>TestCookieName</td><td>CookieValue</td></tr>',
            '<td>TestAnotherCookie</td><td>AnotherCookieValue</td></tr>',
            no=['fields()', '<td>answer</td>', 'Reload the page'])
        r = r.click('You can also add some test fields.')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h3>Request Variables</h3>',
            'The following table shows the values',
            '>fields()<',
            '<td>answer</td><td>42</td>',
            "<td>list</td><td>['1',<wbr> '2',<wbr> '3']</td>",
            '<td>question</td><td>what</td>',
            '>environ()<',
            '<td>PATH_INFO</td><td>/RequestInformation</td>',
            'We added some cookies for you',
            '>cookies()<',
            '<td>TestCookieName</td><td>CookieValue</td></tr>',
            no=['Reload the page', 'add some test fields'])
        r = r.goto('/RequestInformation',
                   extra_environ=dict(REMOTE_USER='bob'))
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h3>Request Variables</h3>',
            '<td>PATH_INFO</td><td>/RequestInformation</td>',
            '<td>REMOTE_USER</td><td>bob</td>')

    def testImageDemo(self):
        r = self.testApp.get('/ImageDemo')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<title>ImageDemo</title>',
            '<h2>Webware Image Generation Demo</h2>',
            '<img src="ImageDemo?fmt=.png"',
            'image has just been generated using the Python Imaging Library')
        r = self.testApp.get('/ImageDemo?fmt=.png')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'image/png')
        self.assertTrue(2000 < r.content_length < 2500)
        self.assertTrue(r.body.startswith(b'\x89PNG\r\n\x1a\n'))

    def testDominateDemo(self):
        r = self.testApp.get('/DominateDemo')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>DominateDemo</title>',
            'Dominate is a Python library',
            'to generate HTML programmatically',
            '<h1>Using Webware with Dominate</h1>',
            '<h2>Hello World!</h2>',
            '<td>One</td>', '<td>Two</td>', '<td>Three</td>',
            'This content has been produced',
            '<a href="https://github.com/Knio/dominate">Dominate</a>')

    def testYattagDemo(self):
        r = self.testApp.get('/YattagDemo')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>YattagDemo</title>',
            'Yattag is a Python library',
            'to generate HTML programmatically',
            '<h1>Using Webware with Yattag</h1>',
            '<h2>Demo contact form</h2>',
            no=['like spam', 'add the subject', 'did not enter'])
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h2>Demo contact form</h2>',
            'Your message looks like spam!',
            no=['add the subject', 'subject looks like spam', 'did not enter'])
        r.form['message'] = ''
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h2>Demo contact form</h2>',
            'You did not enter a message!',
            no=['add the subject', 'like spam'])
        r.form['message'] = 'Hello, world!'
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            'Congratulations! You have sent the following message:',
            'Just testing', 'Hello, world!',
            no=['contact form', 'did not enter', 'like spam'])
        r = r.click('Try sending another message')
        r.form['subject'] = ''
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h2>Demo contact form</h2>',
            'Please add the subject of your message.',
            'Your message looks like spam!',
            no=['did not enter', 'subject looks like spam'])
        r.form['subject'] = 'Get free money fast!'
        r.form['message'] = 'That subject sounds fishy.'
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<h2>Demo contact form</h2>',
            'Your subject looks like spam!',
            no=['did not enter', 'message looks like spam'])

    def testDBUtilsDemo(self):
        self.removeDemoDatabase()
        r = self.testApp.get('/DBUtilsDemo')
        self.app.addShutDownHandler(self.removeDemoDatabase)
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<title>DBUtils Demo</title>',
            '<h2>Welcome to the DBUtils Demo!</h2>',
            'We are using PooledDB with the sqlite3 database module',
            'Play with the demo database', 'Create tables',
            no=['No database', 'error'])
        r = r.form.submit('_action_createTables')
        r.mustcontain(
            'Creating the following table:',
            'The table was successfully created',
            no=['already exists', 'error'])
        r = r.click('Back')
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_addSeminar')
        r.mustcontain('Add a seminar entry to the database:')
        r.form['id'] = 'W4PY'
        r.form['title'] = 'Creating Webware apps'
        r.form['places'] = 12
        r = r.form.submit()
        r.mustcontain('"Creating Webware apps" added to seminars.')
        r = r.click('Back')
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_addSeminar')
        r.form['id'] = 'JAVA'
        r.form['title'] = 'Creating Java apps'
        r.form['cost'] = 1000
        r = r.form.submit()
        r.mustcontain('"Creating Java apps" added to seminars.')
        r = r.click('Back')
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_listSeminars')
        r.mustcontain(
            'List of seminars in the database:',
            '<td>JAVA</td><td>Creating Java apps</td>'
            '<td align="right">1000</td><td align="right">unlimited</td>',
            '<td>W4PY</td><td>Creating Webware apps</td>'
            '<td align="right">free</td><td align="right">12</td>')
        r.form['id'] = ['JAVA', None]
        r = r.form.submit()
        r.mustcontain('Entries deleted: 1', 'W4PY', no=['JAVA'])
        r = r.click('Back')
        ##
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_addAttendee')
        r.mustcontain('Add an attendee entry to the database:')
        r.form['name'] = 'John Doe'
        r.form['paid'] = '1'
        r = r.form.submit()
        r.mustcontain('John Doe added to attendees.')
        r = r.click('Back')
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_addAttendee')
        r.form['name'] = "John's Bro"
        r.form['paid'] = '0'
        r = r.form.submit()
        r.mustcontain("John's Bro added to attendees.")
        r = r.click('Back')
        r.mustcontain('Play with the demo database')
        r = r.form.submit('_action_listAttendees')
        r.mustcontain(
            'List of attendees in the database:',
            '<td>John Doe</td><td>Creating Webware apps</td>'
            '<td align="center">Yes</td>',
            "<td>John's Bro</td><td>Creating Webware apps</td>"
            '<td align="center">No</td>')
        r.form['id'] = [None, "W4PY:John's Bro"]
        r = r.form.submit()
        r.mustcontain('Entries deleted: 1', 'John Doe', no=["John's Bro"])
        r = r.click('Back')
        r = r.form.submit('_action_listSeminars')
        r.mustcontain(
            'List of seminars in the database:',
            '<td>W4PY</td><td>Creating Webware apps</td>'
            '<td align="right">free</td><td align="right">11</td>')
        r = r.click('Back')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<title>DBUtils Demo</title>',
            '<h2>Welcome to the DBUtils Demo!</h2>')

    def testAjaxSuggest(self):
        r = self.testApp.get('/AjaxSuggest')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<title>AjaxSuggest</title>',
            '<h2>Ajax "Suggest" Example</h2>',
            'This example uses Ajax techniques to make suggestions',
            'JavaScript enabled', 'Start typing',
            no=['just entered', 'try again'])
        r.form['query'] = 'ajax'
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<h2>Ajax "Suggest" Example</h2>',
            'You have just entered the word <b class="in_red">"ajax"</b>.',
            'If you like, you can try again:',
            no=['uses Ajax techniques', 'Start typing'])
        r = r.goto('/AjaxSuggest?_action_=ajaxCall&_call_=suggest&_req_=1&_=a')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'application/json')
        self.assertTrue(r.text.startswith("handleSuggestions(['"))
        self.assertTrue(r.text.endswith("']);"))
        r.mustcontain(no=['AjaxSuggest', 'Ajax "Suggest" Example'])

    def testJSONRPCClient(self):
        r = self.testApp.get('/JSONRPCClient')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'text/html')
        r.mustcontain(
            '<title>JSONRPCClient</title>',
            '<h3>JSON-RPC Example</h3>',
            'This example shows how you can call methods')
        r = self.testApp.post_json('/JSONRPCExample', params={
            "id": 1, "method": "reverse", "params": ["Hello, World!"]})
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'application/json')
        lines = [line.rstrip() for line in r.text.splitlines()]
        self.assertEqual(lines, [
            'throw new Error("Direct evaluation not allowed");',
            '/*{"id": 1, "result": "!dlroW ,olleH"}*/'])
        r = self.testApp.post_json('/JSONRPCExample', params={
            "id": 2, "method": "invalid", "params": ["Hello, World!"]})
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.content_type, 'application/json')
        self.assertEqual(
            r.text, '{"id": 2, "code": -1,'
            ' "error": "invalid is not an approved method"}')


class TestExamplesWithoutWSGIWrite(TestExamples):

    settings = dict(
        PrintConfigAtStartUp=False,
        WSGIWrite=False
    )


class TestExamplesWithoutCaching(TestExamples):

    settings = dict(
        PrintConfigAtStartUp=False,
        CacheServletClasses=False,
        CacheServletInstances=False,
        ReloadServletClasses=False
    )
