"""Test Webware Application via its WSGI interface"""

import sys

from io import StringIO
from os import chdir, getcwd

from webtest import TestApp, AppError  # pylint: disable=import-error

from Application import Application

__all__ = ['AppTest', 'AppError']


class AppTest:

    settings = dict(
        PrintConfigAtStartUp=False
    )
    capture = False  # set to False if you want to run an individual test and use pdb interactively.

    @classmethod
    def setUpClass(cls):
        stdout, stderr = sys.stdout, sys.stderr
        if cls.capture:
            sys.stdout = sys.stderr = StringIO()
        cls.currentDir = getcwd()
        import webware
        webwareDir = webware.__path__[0]
        chdir(webwareDir)
        try:
            app = Application(settings=cls.settings, development=True)
            cls.app = app
            cls.testApp = TestApp(app)
        except Exception as e:
            error = str(e) or 'Could not create application'
        else:
            error = None
        finally:
            if cls.capture:
                output = sys.stdout.getvalue().rstrip()
            else:
                output = ''
            sys.stdout, sys.stderr = stdout, stderr
        if error:
            raise RuntimeError(
                'Error setting up application:\n' + error +
                '\nOutput was:\n' + output)
        if cls.capture and ((not output.startswith('Webware for Python')
                or 'Running in development mode' not in output
                or 'Loading context' not in output)):
            raise AssertionError(
                'Application was not properly started.'
                ' Output was:\n' + output)

    @classmethod
    def tearDownClass(cls):
        stdout, stderr = sys.stdout, sys.stderr
        if cls.capture:
            sys.stdout = sys.stderr = StringIO()
        cls.app.shutDown()
        if cls.capture:
            output = sys.stdout.getvalue().rstrip()
        else:
            output = ''
        sys.stdout, sys.stderr = stdout, stderr
        chdir(cls.currentDir)
        if cls.capture and output != ('Application is shutting down...\n'
                      'Application has been successfully shutdown.'):
            raise AssertionError(
                'Application was not properly shut down. Output was:\n'
                + output)

    def setUp(self):
        self.stdout, self.stderr = sys.stdout, sys.stderr
        if self.capture:
            sys.stdout = sys.stderr = StringIO()

    def tearDown(self):
        if self.capture:
            self.output = sys.stdout.getvalue().rstrip()
        else:
            self.output = None
        sys.stdout, sys.stderr = self.stdout, self.stderr

    def run(self, result=None):
        result = super().run(result)  # pylint: disable=no-member
        if not result.wasSuccessful() and self.capture and self.output:
            print("Application output was:")
            print(self.output)
