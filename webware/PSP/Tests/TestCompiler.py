"""Automated tests for PSPCompiler

Copyright (c) by Winston Wolff, 2004 https://www.stratolab.com
"""

import os
import importlib
import shutil
import sys
import tempfile
import unittest

from io import StringIO
from time import sleep

from PSP import Context, PSPCompiler


class TestCompiler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testDir = tempfile.mkdtemp()
        sys.path.insert(0, cls.testDir)

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(cls.testDir)
        shutil.rmtree(cls.testDir)

    @staticmethod
    def sync():
        """Make sure everything is written to disk."""
        try:
            os.sync()
        except AttributeError:
            pass  # not Unix
        sleep(0.05)

    def compileString(self, pspSource, classname):
        """Compile a string to an object.

        Takes a string, compiles it, imports the Python file, and returns you
        the Python class object.

        classname = some string so that each file is unique per test case.
        """
        # write string to temporary file
        moduleName = "tmp_TestCompiler_" + classname
        modulePath = os.path.join(self.testDir, moduleName)
        tmpInName = modulePath + '.psp'
        tmpOutName = modulePath + '.py'
        with open(tmpInName, 'w') as fp:
            fp.write(pspSource)
        # Compile PSP into .py file
        context = Context.PSPCLContext(tmpInName)
        context.setClassName(classname)
        context.setPythonFileName(tmpOutName)
        clc = PSPCompiler.Compiler(context)
        clc.compile()
        self.sync()
        self.assertTrue(os.path.isfile(tmpOutName))
        # Have Python import the .py file.
        theModule = importlib.__import__(moduleName)
        # want to return the class inside the module.
        theClass = getattr(theModule, classname)
        return theClass

    def compileAndRun(self, pspSource, classname):
        pspClass = self.compileString(pspSource, classname)
        pspInstance = pspClass()
        outStream = StringIO()
        pspInstance._writeHTML(outStream)
        output = outStream.getvalue()
        return output

    def testExpression(self):
        output = self.compileAndRun(
            'two plus three is: <%= 2+3 %>', 'testExpression')
        self.assertEqual("two plus three is: 5", output)

    def testScript(self):
        output = self.compileAndRun(
            'one plus two is: <% res.write(str(1+2)) %>', 'testScript')
        self.assertEqual("one plus two is: 3", output)

    def testScriptNewLines(self):
        psp = '''\nthree plus two is: \n<%\nres.write(str(3+2)) \n%>'''
        expect = '''\nthree plus two is: \n5'''
        output = self.compileAndRun(psp, 'testScriptNewLines')
        self.assertEqual(output, expect)
        psp = '''\nthree plus two is: \n<%\n  res.write(str(3+2)) \n%>'''
        expect = '''\nthree plus two is: \n5'''
        output = self.compileAndRun(psp, 'testScriptNewLines')
        self.assertEqual(output, expect)

    def testScriptReturns(self):
        psp = '''\rthree plus two is: \r<%\rres.write(str(3+2)) \r%>'''
        expect = '''\nthree plus two is: \n5'''
        output = self.compileAndRun(psp, 'testScriptReturns')
        self.assertEqual(output, expect)
        psp = '''\rthree plus two is: \r<%\r     res.write(str(3+2)) \r%>'''
        expect = '''\nthree plus two is: \n5'''
        output = self.compileAndRun(psp, 'testScriptReturns')
        self.assertEqual(output, expect)

    def testScriptIf(self):
        psp = '''PSP is <% if 1: %>Good<% end %>'''
        expect = '''PSP is Good'''
        output = self.compileAndRun(psp, 'testScriptIf')
        self.assertEqual(output, expect)

    def testScriptIfElse(self):
        psp = '''JSP is <% if 0: %>Good<% end %><% else: %>Bad<% end %>'''
        expect = '''JSP is Bad'''
        output = self.compileAndRun(psp, 'testScriptIfElse')
        self.assertEqual(output, expect)

    def testScriptBlocks(self):
        psp = '''
<% for i in range(3): %>
<%= i %><br/>
<% end %>'''
        expect = '''

0<br/>

1<br/>

2<br/>
'''
        output = self.compileAndRun(psp, 'testScriptBlocks')
        self.assertEqual(output, expect)

    def testScriptBraces(self):
        psp = '''\
<%@page indentType="braces" %>
<% for i in range(3): { %>
<%= i %><br/>
<% } %>'''
        expect = '''

0<br/>

1<br/>

2<br/>
'''
        output = self.compileAndRun(psp, 'testScriptBraces')
        self.assertEqual(output, expect)

    def testPspMethod(self):
        psp = '''
        <psp:method name="add" params="a,b">
        return a+b
        </psp:method>
        7 plus 8 = <%= self.add(7,8) %>
        '''
        output = self.compileAndRun(psp, 'testPspMethod').strip()
        self.assertEqual("7 plus 8 = 15", output)

    def testPspFile(self):
        psp = '''
        <psp:file>
            def square(a):
                return a*a
        </psp:file>
        7^2 = <%= square(7) %>
        '''
        output = self.compileAndRun(psp, 'testPspFile').strip()
        self.assertEqual("7^2 = 49", output)

    def testPspClass(self):
        psp = '''
        <psp:class>
            def square(self, a):
                return a*a
        </psp:class>
        4^2 = <%= self.square(4) %>
        '''
        output = self.compileAndRun(psp, 'testPspClass').strip()
        self.assertEqual("4^2 = 16", output)
