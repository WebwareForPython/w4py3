"""Test Webware server script"""

import unittest

from os import environ, getcwd, chdir
from re import compile as reCompile
from subprocess import Popen, PIPE, STDOUT
from queue import Empty
from multiprocessing import Process, Queue, SimpleQueue
from urllib.request import urlopen

import psutil  # pylint: disable=import-error

expectedServerOutput = r'''
Webware for Python .+ Application

Process id: \d+
Start date/time: .+
Python: .+

ActivityLogColumns              = \[.+\]
ActivityLogFilename             = '.+'
AdminPassword                   = ''
AlwaysSaveSessions              = True
CacheServletClasses             = False
CacheServletInstances           = False
LogActivity                     = False
LogErrors                       = True
Verbose                         = True
WSGIWrite                       = True
WebwarePath                     = '.+'

Loading context: Examples at .+Examples
Loading context: Admin at .+Admin
Loading context: Testing at .+Testing
Plug-ins list: MiscUtils, WebUtils, TaskKit, UserKit, PSP
Loading plug-in: MiscUtils at .+MiscUtils
Loading plug-in: WebUtils at .+WebUtils
Loading plug-in: TaskKit at .+TaskKit
Loading plug-in: UserKit at .+UserKit
Loading plug-in: PSP at .+PSP
Loading context: PSP/Examples at .+Examples

Waitress serving Webware application...
Serving on http://.+:8080
'''

expectedStartPage = r'''
<!DOCTYPE html>
<html lang="en">
<head>
\s*<title>Welcome</title>
\s*<meta charset="utf-8">
<style>
html {
}
h1 { .+; }
#Page {
\s*display: table;
}
</style>
</head>
<body style="color:black;background-color:white">
<div id="Page"><div>
<div id="CornerTitle">Webware Examples</div><div id="Banner">Welcome</div>
</div><div id="Content">
<h2>Welcome to Webware .+!</h2>
</div></div></div>
</body>
</html>
'''


class RunServer(Process):
    """Run a given command until a given line is found in the output."""

    def __init__(self, cmd=None, waitForLine='Serving on '):
        super().__init__()
        self.cmd = cmd or ['webware', 'serve']
        self.waitForLine = waitForLine
        self.outputQueue = SimpleQueue()
        self.pollQueue = Queue()
        self.stopQueue = SimpleQueue()

    def getOutput(self):
        output = []
        while not self.outputQueue.empty():
            output.append(self.outputQueue.get())
        return output

    def getExitCode(self, timeout=10):
        try:
            return self.pollQueue.get(timeout=timeout)
        except Empty:
            self.stop()
            return f'timeout - {self.waitForLine!r} not found'

    def stop(self, timeout=10):
        if not self.is_alive():
            return
        # Because on Windows serve.exe starts another Python process,
        # we need to make sure the grandchildren are stopped as well.
        children = psutil.Process(self.pid).children(recursive=True)
        for p in children:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        children = psutil.wait_procs(children, timeout=timeout)[1]
        for p in children:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

    def run(self):
        # Because on Windows serve.exe starts another Python process,
        # we need to make sure that process runs in unbuffered mode as well.
        environ['PYTHONUNBUFFERED'] = '1'
        with Popen(self.cmd, bufsize=1, universal_newlines=True,
                   encoding='utf-8', stdout=PIPE, stderr=STDOUT) as p:
            outputStarted = False
            while True:
                ret = p.poll()
                if ret is not None:
                    break
                line = p.stdout.readline().rstrip()
                if line:
                    outputStarted = True
                if outputStarted:
                    self.outputQueue.put(line)
                    if line.startswith(self.waitForLine):
                        break
            self.pollQueue.put(ret)
            if ret is None:
                while True:
                    ret = p.poll()
                    if ret is not None:
                        break
                    line = p.stdout.readline().rstrip()
                    self.outputQueue.put(line)
            self.pollQueue.put(ret)


class TestServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.currentDir = getcwd()
        import webware
        webwareDir = webware.__path__[0]
        chdir(webwareDir)
        from Properties import version
        from MiscUtils.PropertiesObject import versionString
        cls.version = versionString(version)
        cls.server = RunServer()
        cls.server.start()
        cls.exitCode = cls.server.getExitCode()
        cls.running = cls.exitCode is None
        cls.output = cls.server.getOutput()
        cls.running = cls.exitCode is None

    @classmethod
    def tearDownClass(cls):
        try:
            cls.server.stop()
        finally:
            chdir(cls.currentDir)

    def getPage(self, path=''):
        return urlopen(f'http://localhost:8080/{path}')

    def compareOutput(self, gotLines, expectedLines):
        self.assertTrue(gotLines, 'We could not collect any output.')
        index = 0
        for expectedLine in expectedLines:
            expectedPattern = reCompile(expectedLine)
            foundLine = False
            lastIndex = index
            while True:
                try:
                    line = gotLines[index]
                except IndexError:
                    break
                index += 1
                if expectedPattern.match(line):
                    foundLine = True
                    break
            if not foundLine:
                break
        else:
            expectedLine = False
        nextOutput = '\n'.join(gotLines[lastIndex:][:3])
        fullOutput = '\n'.join(gotLines)
        msg = (f'Expected line not found:\n{expectedLine}\n\n'
               f'Next three lines were:\n{nextOutput}\n\n'
               f'Complete output was:\n{fullOutput}\n')
        self.assertTrue(foundLine, msg)

    def testExitCode(self):
        ret = self.exitCode
        self.assertIsNone(ret, f'Server exited with {ret}')

    def testExpectedServerOutput(self):
        expectedOutput = expectedServerOutput.strip().splitlines()
        self.compareOutput(self.output, expectedOutput)
        startLine = f'Webware for Python {self.version} Application'
        self.assertEqual(self.output[0], startLine)
        self.assertTrue(not any(
            'ERROR' in line or 'WARNING' in line for line in self.output))

    def testStartPage(self):
        self.assertTrue(self.running)
        expectedPage = expectedStartPage.strip().splitlines()
        with self.getPage() as page:
            page = page.read().decode('utf-8')
            page = [page.lstrip() for page in page.splitlines()]
            self.compareOutput(page, expectedPage)
            welcomeLine = f'Welcome to Webware for Python {self.version}'
            self.assertTrue(any(welcomeLine in line for line in page))

    def testShowTimeExample(self):
        self.assertTrue(self.running)
        with self.getPage('ShowTime') as page:
            page = page.read().decode('utf-8')
            self.assertIn('The current time is:', page)

    def testForward(self):
        self.assertTrue(self.running)
        with self.getPage('Forward') as page:
            page = page.read().decode('utf-8')
            self.assertIn('the <em>Forward</em> servlet speaking', page)
            self.assertIn('<h1>Hello from IncludeMe</h1>', page)

    def testIfModifiedSince(self):
        self.assertTrue(self.running)
        with self.getPage('Testing/TestIMS') as page:
            page = page.read().decode('utf-8')
            self.assertIn('Test If-Modified-Since support in Webware', page)
            self.assertIn('TestIMS passed.', page)
