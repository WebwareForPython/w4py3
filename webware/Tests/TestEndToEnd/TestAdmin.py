"""Test Webware Admin context"""

import unittest

from .AppTest import AppTest


class TestAdminLogin(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        AdminPassword='LoginTestPassword'
    )

    def testLogin(self):
        r = self.testApp.get('/')
        r = r.click('Admin', index=0)
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/')
        r.mustcontain(
            '<title>LoginPage</title>',
            'Please log in to view Administration Pages.',
            no=['>Webware Administration Pages<',
                'Login failed', 'Try again',
                'You have been logged out'])
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Login failed. Please try again.')
        r.form['username'] = 'admin'
        r.form['password'] = 'BadPassword'
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Login failed. Please try again.')
        r.form['username'] = 'alice'
        r.form['password'] = self.settings['AdminPassword']
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Login failed. Please try again.')
        r.form['username'] = 'admin'
        r.form['password'] = self.settings['AdminPassword']
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Admin</title>',
            '>Webware Administration Pages<',
            no=['Please log in', 'Login failed', 'Try again'])
        r = r.goto('./')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Admin</title>',
            '>Webware Administration Pages<',
            no=['Please log in', 'Login failed', 'Try again'])
        r = r.click('Logout')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>LoginPage</title>',
            'You have been logged out.',
            'Please log in to view Administration Pages.',
            no=['>Webware Administration Pages<',
                'Login failed', 'Try again'])
        r = r.goto('./')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>LoginPage</title>',
            'Please log in to view Administration Pages.',
            no=['>Webware Administration Pages<',
                'You have been logged out.',
                'Login failed', 'Try again'])


class TestAdminWithoutPassword(AppTest, unittest.TestCase):

    def testLogin(self):
        r = self.testApp.get('/Admin/')
        r.mustcontain(
            'Logins to admin pages are disabled'
            ' until you supply an AdminPassword in Application.config.')


class TestAdmin(AppTest, unittest.TestCase):

    settings = dict(
        PrintConfigAtStartUp=False,
        AdminPassword='AdminTestPassword',
        CacheServletClasses=True,
        CacheServletInstances=True
    )

    def setUp(self):
        AppTest.setUp(self)
        self.testApp.reset()
        r = self.testApp.get('/Admin/')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Please log in')
        r.form['username'] = 'admin'
        r.form['password'] = self.settings['AdminPassword']
        r = r.form.submit('login')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(no=['Login failed'])

    def tearDown(self):
        try:
            r = self.testApp.get('/Admin/?logout=yes')
            self.assertEqual(r.status, '200 OK')
            r.mustcontain('You have been logged out.')
        finally:
            AppTest.tearDown(self)

    def testStartPage(self):
        r = self.testApp.get('/Admin/')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Admin</title>',
            '>Webware Administration Pages<',
            no=['Please log in', 'Login failed'])
        r.mustcontain(
            '<th colspan="2">Application Info</th>',
            'Webware Version', 'Local Time', 'Up Since',
            'Num Requests', 'Working Dir', 'Active Sessions')

    def testActivityLog(self):
        r = self.testApp.get('/Admin/').click('Activity log')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/Access')
        r.mustcontain('<title>View Activity</title>')

    def testErrorLog(self):
        r = self.testApp.get('/Admin/').click('Error log')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/Errors')
        r.mustcontain('<title>View Errors</title>')

    def testConfig(self):
        r = self.testApp.get('/Admin/').click('Config')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/Config')
        adminPassword = self.settings['AdminPassword']
        r.mustcontain(
            '<title>Config</title>',
            '<tr class="TopHeading"><th colspan="2">Application</th></tr>',
            f'<tr><th>AdminPassword</th><td>{adminPassword}</td></tr>',
            '<tr><th>LogActivity</th><td>False</td></tr>',
            '<tr><th>Verbose</th><td>True</td></tr>',
            '<tr><th>WSGIWrite</th><td>True</td></tr>')

    def testPlugins(self):
        r = self.testApp.get('/Admin/').click('Plug-ins')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/PlugIns')
        webwareVersion = self.app.webwareVersionString()
        r.mustcontain(
            '<title>PlugIns</title>',
            'The following Plug-ins were found:',
            '<tr class="TopHeading"><th colspan="3">Plug-ins</th></tr>',
            '<tr class="SubHeading"><th>Name</th>'
            '<th>Version</th><th>Directory</th></tr>',
            f'<td style="text-align:center">{webwareVersion}</td>',
            '<td>MiscUtils</td>', '<td>PSP</td>', '<td>TaskKit</td>',
            '<td>UserKit</td>', '<td>WebUtils</td>')

    def testServletCache(self):
        r = self.testApp.get('/Admin/').click('Servlet Cache')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/ServletCache')
        r.mustcontain(
            '<title>Servlet Cache</title>', '<h4>PythonServletFactory</h4>',
            '<p>Uniqueness: file</p>', "<p>Extensions: '.py', '.pyc'</p>",
            'Click any link to jump to the details for that path.', 'Flush',
            '<h5>Filenames:</h5>', '<tr><th>File</th><th>Directory</th></tr>',
            '<h5>Full paths:</h5>', '<tr><th>Servlet path</th></tr>',
            '>Main.py</a></td><td>', '>ServletCache.py</a></td><td>',
            '<h5>Details:</h5>', 'free reusable servlets:',
            '<strong>Main.py</strong>', '<strong>ServletCache.py</strong>',
            '<th>class</th>', '<th>instances</th>',
            '<th>mtime</th>', '<th>path</th>',
            '<td>Main</td>', '<td>ServletCache</td>',
            no='has been flushed')
        r = r.form.submit('flush_PythonServletFactory')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Servlet Cache</title>', '<h4>PythonServletFactory</h4>',
            'The servlet cache has been flushed.', 'Reload',
            no=['Click any link', 'Uniqueness:', '<h5>Filenames:</h5>'])
        r = r.form.submit()
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Servlet Cache</title>', '<h4>PythonServletFactory</h4>',
            '<p>Uniqueness: file</p>', "<p>Extensions: '.py', '.pyc'</p>",
            'Unique paths in the servlet cache: <strong>1</strong>',
            'Click any link to jump to the details for that path.',
            '<strong>ServletCache.py</strong>', '<td>ServletCache</td>',
            no=['has been flushed', 'Main.py', '<td>Main</td>'])
        r = self.testApp.get('/Admin/').click('Servlet Cache')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Servlet Cache</title>', '<h4>PythonServletFactory</h4>',
            '<p>Uniqueness: file</p>', "<p>Extensions: '.py', '.pyc'</p>",
            'Unique paths in the servlet cache: <strong>2</strong>',
            'Click any link to jump to the details for that path.',
            '<strong>Main.py</strong>', '<td>Main</td>',
            '<strong>ServletCache.py</strong>', '<td>ServletCache</td>',
            no='has been flushed')

    def testAppControl(self):
        r = self.testApp.get('/Admin/').click('Application Control')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.request.path, '/Admin/AppControl')
        r.mustcontain(
            '<title>AppControl</title>',
            'Clear the class and instance caches of each servlet factory.',
            'Reload the selected Python modules. Be careful!',
            '<input type="checkbox" name="reloads"'
            ' value="Admin.AdminPage"> Admin.AdminPage<br>')
        r = r.form.submit('action', index=0)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>AppControl</title>',
            'Flushing cache of PythonServletFactory...',
            'The caches of all factories have been flushed.',
            'Click here to view the Servlet cache:',
            no=['<input type="checkbox"', 'Clear the class and instance'])
        r = r.click('Servlet Cache', index=1)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>Servlet Cache</title>', '<h4>PythonServletFactory</h4>',
            'Unique paths in the servlet cache: <strong>1</strong>')
        r = r.click('Application Control')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>AppControl</title>',
            'Clear the class and instance caches of each servlet factory.',
            'Reload the selected Python modules. Be careful!',
            '<input type="checkbox" name="reloads"'
            ' value="Admin.AdminPage"> Admin.AdminPage<br>')
        for i, checkbox in enumerate(
                r.html.find_all('input', attrs={'name': 'reloads'})):
            if checkbox.attrs['value'] == 'Admin.AdminPage':
                r.form.get('reloads', index=i).checked = True
                break
        else:
            self.fail('Did not find expected checkbox for Admin.AdminPage')
        r = r.form.submit('action', index=1)
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>AppControl</title>',
            'Reloading selected modules.',
            "Reloading &lt;module 'Admin.AdminPage'",
            'The selected modules have been reloaded.',
            no=['<input type="checkbox"', 'Be careful!'])
        r = r.goto('/Admin/AppControl')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain(
            '<title>AppControl</title>',
            'Clear the class and instance caches of each servlet factory.',
            'Reload the selected Python modules. Be careful!',
            '<input type="checkbox" name="reloads"'
            ' value="Admin.AdminPage"> Admin.AdminPage<br>')
