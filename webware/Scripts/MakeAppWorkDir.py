#!/usr/bin/env python3

"""MakeAppWorkDir.py

INTRODUCTION

This utility builds a directory tree that can be used as the current
working directory of an instance of your Webware application.
By using a separate directory tree like this, your application can run
without needing write access etc. to the Webware directory tree, and
you can also run more than one application server at once using the
same Webware code. This makes it easy to reuse and keep Webware
updated without disturbing your applications.

USAGE

MakeAppWorkDir.py [Options] WorkDir

Options:
  -c, --context-name=...  The name for the pre-installed context.
                          By default, it will be "MyContext".
  -d, --context-dir=...   The directory where the context will be located,
                          so you can place it outside of the WorkDir.
  -l, --library=...       Other dirs to be included in the search path.
                          You may specify this option multiple times.

WorkDir:
  The target working directory to be created.
"""

import argparse
import glob
import os
import shutil

import webware


defaultContext = 'MyContext'

try:
    chown, chmod = shutil.chown, os.chmod
    import stat
except (AttributeError, ImportError):
    chown = chmod = stat = None


class MakeAppWorkDir:
    """Make a new application runtime directory for Webware.

    This class breaks down the steps needed to create a new runtime
    directory for Webware. That includes all the needed
    subdirectories, default configuration files, and startup scripts.
    Each step can be overridden in a derived class if needed.

    Existing files will not be overwritten, but access permissions
    will be changed accordingly in any case.
    """

    def __init__(self, workDir,
                 contextName=defaultContext, contextDir='', libraryDirs=None,
                 user=None, group=None, verbose=True):
        """Initializer for MakeAppWorkDir.

        Pass in at least the target working directory.
        If you pass None for contextName, then the default context
        will be the the Examples directory as usual.
        """
        self._workDir = os.path.abspath(workDir)
        self._contextName = contextName
        self._contextDir = contextDir
        if libraryDirs is None:
            libraryDirs = []
        self._libraryDirs = libraryDirs
        self._user, self._group = user, group
        self._verbose = verbose
        self._webwareDir = webware.__path__[0]

    def buildWorkDir(self):
        """These are all the steps needed to make a new runtime directory.

        You can override the steps taken here with your own methods.
        """
        if os.path.exists(self._workDir):
            self.msg("The target directory already exists.")
            self.msg(
                "Adding everything needed for a Webware runtime directory...")
        else:
            self.msg("Making a new Webware runtime directory...")
        self.msg()
        self.makeDirectories()
        self.copyConfigFiles()
        self.copyOtherFiles()
        self.setLibDirs()
        if self._contextName:
            self.makeDefaultContext()
        self.addGitIgnore()
        self.changeOwner()
        self.printCompleted()

    def makeDirectories(self):
        """Create all the needed directories if they don't already exist."""
        self.msg("Creating the directory tree...")
        standardDirs = ('', 'Cache', 'Configs', 'ErrorMsgs', 'Logs',
                        'Scripts', 'Sessions', 'Static')
        for path in standardDirs:
            path = os.path.join(self._workDir, path)
            if os.path.exists(path):
                self.msg(f"\t{path} already exists.")
            else:
                os.mkdir(path)
                self.msg(f"\t{path}")
        for path in self._libraryDirs:
            path = os.path.join(self._workDir, path)
            if os.path.exists(path):
                self.msg(f"\t{path} already exists.")
            else:
                os.makedirs(path)
                open(os.path.join(path, '__init__.py'), 'w').write('#\n')
                self.msg(f"\t{path} created.")

    def copyConfigFiles(self):
        """Make a copy of the config files in the Configs directory."""
        self.msg("Copying config files...")
        configs = glob.glob(os.path.join(
            self._webwareDir, 'Configs', '*.config'))
        for name in configs:
            newName = os.path.join(
                self._workDir, "Configs", os.path.basename(name))
            if os.path.exists(newName):
                self.msg(f"\t{newName} already exists.")
            else:
                self.msg(f"\t{newName}")
                shutil.copyfile(name, newName)

    def copyOtherFiles(self):
        """Make a copy of any other necessary files in the new work dir."""
        self.msg("Copying other files...")
        wsgiScriptFile = os.path.join('Scripts', 'WSGIScript.py')
        otherFiles = ('error404.html', wsgiScriptFile)
        for name in otherFiles:
            newName = os.path.join(self._workDir, name)
            if os.path.exists(newName):
                self.msg(f"\t{newName} already exists.")
            else:
                oldName = os.path.join(self._webwareDir, name)
                if os.path.exists(oldName):
                    self.msg(f"\t{newName}")
                    shutil.copyfile(oldName, newName)
                else:
                    self.msg(f"\tWarning: Cannot find {oldName!r}.")

    def setLibDirs(self):
        """Set the library directories in the WSGI script."""
        if not self._libraryDirs:
            return
        self.msg("Setting the library directories...")
        wsgiScript = os.path.join(self._workDir, 'Scripts', 'WSGIScript.py')
        if os.path.isfile(wsgiScript):
            with open(wsgiScript) as f:
                script = f.read()
            if 'libDirs = []' not in script:
                self.msg("\tWarning: Unexpected WSGI script")
            else:
                script = script.replace(
                    'libDirs = []', f'libDirs = {self._libraryDirs!r}')
                with open(wsgiScript, 'w') as f:
                    f.write(script)
        else:
            self.msg("\tWarning: Cannot find WSGI script.")

    def makeDefaultContext(self):
        """Make a very simple context for the newbie user to play with."""
        self.msg("Creating default context...")
        contextDir = os.path.join(
            self._workDir,
            self._contextDir or self._contextName)
        if contextDir.startswith(self._workDir):
            configDir = contextDir[len(self._workDir):]
            while configDir[:1] in (os.sep, os.altsep):
                configDir = configDir[1:]
        else:
            configDir = contextDir
        if os.path.exists(contextDir):
            self.msg(f"\t{contextDir} already exists.")
        else:
            self.msg(f"\t{contextDir}")
            os.makedirs(contextDir)
        for name in exampleContext:
            filename = os.path.join(contextDir, name)
            if os.path.exists(filename):
                self.msg(f"\t{filename} already exists.")
            else:
                self.msg(f"\t{filename}")
                open(filename, "w").write(exampleContext[name])
        self.msg("Updating config for default context...")
        filename = os.path.join(
            self._workDir, 'Configs', 'Application.config')
        self.msg(f"\t{filename}")
        content = open(filename).readlines()
        foundContext = 0
        with open(filename, 'w') as output:
            for line in content:
                contextName = self._contextName
                if line.startswith(
                        f"Contexts[{contextName!r}] = {configDir!r}\n"):
                    foundContext += 1
                elif line.startswith("Contexts['default'] = "):
                    output.write(
                        f"Contexts[{contextName!r}] = {configDir!r}\n")
                    output.write(f"Contexts['default'] = {contextName!r}\n")
                    foundContext += 2
                else:
                    output.write(line)
        if foundContext < 2:
            self.msg("\tWarning: Default context could not be set.")

    def addGitIgnore(self):
        self.msg("Creating .gitignore file...")
        existed = False
        ignore = '*~ *.bak *.default *.log *.patch *.pstats *.pyc *.ses *.swp'
        ignore = '\n'.join(ignore.split()) + '\n\n__pycache__/\n'
        ignoreDirs = 'Cache ErrorMsgs Logs Sessions'
        ignore += '\n' + '\n'.join(f'/{d}/' for d in ignoreDirs.split()) + '\n'
        filename = os.path.join(self._workDir, '.gitignore')
        if os.path.exists(filename):
            existed = True
        else:
            with open(filename, 'w') as f:
                f.write(ignore)
        if existed:
            self.msg("\tDid not change existing .gitignore file.")

    def changeOwner(self):
        owner = {}
        if self._user:
            owner['user'] = self._user
        if self._group:
            owner['group'] = self._group
        if not owner:
            return
        if not chown:
            self.msg("\tCannot change ownership on this system.")
            return
        self.msg("Changing the ownership...")
        mode = (
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
            stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
        try:
            path = self._workDir
            chown(path, **owner)
            chmod(path, os.stat(path).st_mode & mode)
            for dirPath, dirNames, fileNames in os.walk(self._workDir):
                for name in dirNames + fileNames:
                    path = os.path.join(dirPath, name)
                    chown(path, **owner)
                    chmod(path, os.stat(path).st_mode & mode)
        except Exception as e:
            self.msg("\tWarning: The ownership could not be changed.")
            self.msg("\tYou may need superuser privileges to do that.")
            self.msg(f"\tThe error message was: {e}")
            return
        mode = 0
        if self._user:
            mode |= stat.S_IWUSR
        if self._group:
            mode |= stat.S_ISGID | stat.S_IWGRP
        try:
            writeDirs = ('Cache', 'ErrorMsgs', 'Logs', 'Sessions')
            for dirName in writeDirs:
                path = os.path.join(self._workDir, dirName)
                chmod(path, os.stat(path).st_mode | mode)
        except Exception as e:
            self.msg("\tWarning: Write permissions could not be set.")
            self.msg(f"\tThe error message was: {e}")

    def printCompleted(self):
        print("""
Congratulations, you've just created a runtime working directory for Webware.

To start the development server, run this command:

webware serve

If you want to open your web browser after running the server, you can
add the "-b" option. Use the "-h" option to see all other possible options.

In a productive environment, we recommend using Apache and mod_wsgi instead
of the waitress development server, and serving the static assets directly
via the Apache server. The Scripts directory contains a WSGI script that can
also be used with any other WSGI server as application server, and any other
web server as reverse proxy which can also be used to serve static assets.

Have fun!""")

    def msg(self, text=None):
        if self._verbose:
            if text:
                print(text)
            else:
                print()


exampleContext = {  # files copied to example context

    # This is used to create a very simple sample context for the new
    # work dir to give the newbie something easy to play with.

    '__init__.py': r"""
def contextInitialize(application, path):
    # You could put initialization code here to be executed
    # when the context is loaded into Webware.
    pass
""",

    'Main.py': r"""
from Page import Page


class Main(Page):

    def title(self):
        return 'My Sample Context'

    def htBodyArgs(self):
        return ('style="color:#202040;background-color:#e8e8f0;'
                'font-family:Tahoma,Verdana,Arial,Helvetica,sans-serif;'
                'font-size:12pt;line-height:1.5;padding:2em"')

    def writeContent(self):
        self.writeln('<h1>Welcome to Webware for Python!</h1>')
        self.writeln('''
        <p>
        This is a sample context generated for you that has purposely been
        kept very simple to give you something to play with to get yourself
        started. The code that implements this page is located in <b>{}</b>.
        </p>'''.format(self.request().serverSidePath()))
        self.writeln('''
        <p>
        There are more examples and documentation in the Webware distribution,
        which you can get to from here:</p>
        <ul>
        ''')
        servletPath = self.request().servletPath()
        contextName = self.request().contextName()
        for ctx in sorted(self.application().contexts()):
            if ctx in ('default', contextName) or '/' in ctx:
                continue
            self.writeln(f'<li><a href="{servletPath}/{ctx}/">{ctx}</a></li>')
        self.writeln('</ul>')
"""

}  # end of example context files


def make(args):
    workDir = args.working_directory
    contextName = args.context_name
    contextDir = args.context_dir
    if not contextName:
        if contextDir:
            contextName = os.path.basename(contextDir)
        else:
            contextName = defaultContext
    libraryDirs = args.library
    if chown:
        user, group = args.user, args.group
    else:
        user = group = None
    command = MakeAppWorkDir(
        workDir, contextName, contextDir, libraryDirs, user, group)
    command.buildWorkDir()


def addArguments(parser):
    """Add command line arguments to the given parser."""
    parser.add_argument(
        '-c', '--context-name',
        help='the name for the pre-installed context'
        f' (by default, the name will be {defaultContext!r})')
    parser.add_argument(
        '-d', '--context-dir',
        help='the directory where the context will be located'
        ' (so you can place it outside the WORK_DIR)')
    parser.add_argument(
        '-l', '--library', action='append',
        help='other directories to be included in the search path'
        ' (you may specify this option multiple times)')
    if chown:
        parser.add_argument(
            '-u', '--user',
            help='the user that shall own the files'
            ' (name or id, e.g. user running the web server)')
        parser.add_argument(
            '-g', '--group',
            help='the group that shall own the files'
            ' (name or id, e.g. group running the web server)')
    parser.add_argument('working_directory', metavar='WORK_DIR')


def main(args=None):
    """Evaluate the command line arguments and call make()."""
    parser = argparse.ArgumentParser(
        description="Make a Webware application working directory")
    addArguments(parser)
    args = parser.parse_args(args)
    make(args)


if __name__ == '__main__':
    main()
