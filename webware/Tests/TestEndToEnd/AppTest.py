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
    catchOutput = True  # set to False if you want to run pdb inside a test

    @classmethod
    def setUpClass(cls):
        stdout, stderr = sys.stdout, sys.stderr
        if cls.catchOutput:
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
            if cls.catchOutput:
                output = sys.stdout.getvalue().rstrip()
                sys.stdout, sys.stderr = stdout, stderr
            else:
                output = ''
        if error:
            raise RuntimeError(
                'Error setting up application:\n' + error +
                '\nOutput was:\n' + output)
        if cls.catchOutput and not (
                output.startswith('Webware for Python')
                and 'Running in development mode' in output
                and 'Loading context' in output):
            raise AssertionError(
                'Application was not properly started.'
                ' Output was:\n' + output)

    @classmethod
    def tearDownClass(cls):
        stdout, stderr = sys.stdout, sys.stderr
        if cls.catchOutput:
            sys.stdout = sys.stderr = StringIO()
        cls.app.shutDown()
        if cls.catchOutput:
            output = sys.stdout.getvalue().rstrip()
            sys.stdout, sys.stderr = stdout, stderr
        else:
            output = ''
        chdir(cls.currentDir)
        if cls.catchOutput and output != (
                'Application is shutting down...\n'
                'Application has been successfully shut down.'):
            raise AssertionError(
                'Application was not properly shut down. Output was:\n'
                + output)

    def setUp(self):
        self.output = ''
        self.stdout, self.stderr = sys.stdout, sys.stderr
        if self.catchOutput:
            sys.stdout = sys.stderr = StringIO()

    def tearDown(self):
        if self.catchOutput:
            self.output = sys.stdout.getvalue().rstrip()
            sys.stdout, sys.stderr = self.stdout, self.stderr

    def run(self, result=None):
        result = super().run(result)  # pylint: disable=no-member
        if not result.wasSuccessful() and self.output:
            print("Application output was:")
            print(self.output)
