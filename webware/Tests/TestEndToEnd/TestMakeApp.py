"""Test Webware make script"""

import os
import shutil
import subprocess
import tempfile
import unittest


class TestMakeApp(unittest.TestCase):

    def setUp(self):
        self.testDir = tempfile.mkdtemp()
        self.currentDir = os.getcwd()
        os.chdir(self.testDir)

    def tearDown(self):
        os.chdir(self.currentDir)
        shutil.rmtree(self.testDir)

    def runMake(self, opts=None):
        args = ['webware', 'make']
        if opts:
            args += opts
        result = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, universal_newlines=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        return result.stdout.splitlines()

    def testMakeHelp(self):
        output = self.runMake(['-h'])
        self.assertEqual(output.pop(0),
                         'usage: webware make [-h]'
                         ' [-c CONTEXT_NAME] [-d CONTEXT_DIR] [-l LIBRARY]')
        if hasattr(shutil, 'chown'):
            self.assertEqual(output.pop(0).lstrip(), '[-u USER] [-g GROUP]')
        self.assertEqual(output.pop(0).lstrip(), 'WORK_DIR')

    def testMakeNewApp(self):
        output = self.runMake(['MyApp'])
        self.assertEqual(
            output[0], 'Making a new Webware runtime directory...')
        self.assertIn('Creating the directory tree...', output)
        self.assertIn('Copying config files...', output)
        self.assertIn('Copying other files...', output)
        self.assertIn('Creating default context...', output)
        self.assertIn('Updating config for default context...', output)
        self.assertIn('Creating .gitignore file...', output)
        self.assertIn(
            "Congratulations, you've just created a"
            " runtime working directory for Webware.", output)
        self.assertIn(
            'To start the development server, run this command:', output)
        self.assertIn('webware serve', output)
        self.assertTrue(os.path.isdir('MyApp'))
        os.chdir('MyApp')
        appDirs = 'Cache Configs ErrorMsgs Logs MyContext Sessions'.split()
        for appDir in appDirs:
            self.assertTrue(os.path.isdir(appDir), appDir)
        appFiles = '.gitignore error404.html Scripts/WSGIScript.py'.split()
        for appFile in appFiles:
            self.assertTrue(os.path.isfile(appFile), appFile)
        with open('Scripts/WSGIScript.py') as f:
            wsgiScript = f.read().splitlines()
        self.assertEqual(wsgiScript[0], '#!/usr/bin/env python3')
        self.assertIn('from Application import Application', wsgiScript)
        os.chdir('MyContext')
        with open('__init__.py') as f:
            initScript = f.read().splitlines()
        self.assertIn('def contextInitialize(application, path):', initScript)
        with open('Main.py') as f:
            mainServlet = f.read().splitlines()
        self.assertIn('class Main(Page):', mainServlet)
