import os
import sys


class WillNotRunError(Exception):
    """Error for Webware components that will not run."""


def versionString(version):
    """Convert the given version tuple to a string.

    For a sequence containing version information such as (2, 0, 0, 'b'),
    this returns a printable string such as '2.0b'.
    The micro version number is excluded from the string if it is zero.
    """
    ver = list(map(str, version))
    ver, suffix = ver[:3], '.'.join(ver[3:])
    if len(ver) > 2 and ver[2] == '0':
        ver = ver[:2]
    return '.'.join(ver) + suffix


class PropertiesObject(dict):
    """A Properties Object.

    A PropertiesObject represents, in a dictionary-like fashion, the values
    found in a Properties.py file. That file is always included with a Webware
    component to advertise its name, version, status, etc. Note that a Webware
    component is a Python package that follows additional conventions.
    Also, the top level Webware directory contains a Properties.py.

    Component properties are often used for:
      * generation of documentation
      * runtime examination of components, especially prior to loading

    PropertiesObject provides additional keys:
      * filename - the filename from which the properties were read
      * versionString - a nicely printable string of the version
      * requiredPyVersionString - like versionString,
        but for requiredPyVersion instead
      * willRun - 1 if the component will run.
        So far that means having the right Python version.
      * willNotRunReason - defined only if willRun is 0,
        contains a readable error message

    Using a PropertiesObject is better than investigating the Properties.py
    file directly, because the rules for determining derived keys and any
    future convenience methods will all be provided here.

    Usage example:
        from MiscUtils.PropertiesObject import PropertiesObject
        props = PropertiesObject(filename)
        for key, value in props.items():
            print(f'{key}: {value}')

    Note: We don't normally suffix a class name with "Object" as we have
    with this class, however, the name Properties.py is already used in
    our containing package and all other packages.
    """

    # region Init and reading

    def __init__(self, filename=None):
        dict.__init__(self)
        if filename:
            self.readFileNamed(filename)

    def loadValues(self, *args, **kwargs):
        self.update(*args, **kwargs)
        self.cleanPrivateItems()

    def readFileNamed(self, filename):
        results = {}
        with open(filename) as f:
            exec(f.read(), results)
        self.update(results)
        self.cleanPrivateItems()
        self.createDerivedItems()

    # endregion Init and reading

    # region Self utility

    def cleanPrivateItems(self):
        """Remove items whose keys start with a double underscore."""
        keys = list(self)
        for key in keys:
            if key.startswith('__'):
                del self[key]

    def addBuiltinItems(self):
        pass

    def createDerivedItems(self):
        self.createVersionString()
        self.createRequiredPyVersionString()
        self.createWillRun()

    def createVersionString(self):
        if 'version' in self:
            self['versionString'] = versionString(self['version'])

    def createRequiredPyVersionString(self):
        if 'requiredPyVersion' in self:
            self['requiredPyVersionString'] = versionString(
                self['requiredPyVersion'])

    def createWillRun(self):
        try:
            # Invoke each of the checkFoo() methods
            for key in self.willRunKeys():
                methodName = 'check' + key[0].upper() + key[1:]
                method = getattr(self, methodName)
                method()
        except WillNotRunError as msg:
            self['willRun'] = False
            self['willNotRunReason'] = msg
        else:
            self['willRun'] = True  # we passed all the tests

    def willRunKeys(self):
        """Return keys to be examined before running the component.

        This returns a set of all keys whose values should be examined in
        order to determine if the component will run. Used by createWillRun().
        """
        return {
            'requiredPyVersion', 'requiredOpSys', 'deniedOpSys', 'willRunFunc'}

    def checkRequiredPyVersion(self):
        if 'requiredPyVersion' in self and tuple(
                sys.version_info) < tuple(self['requiredPyVersion']):
            pythonVersion = '.'.join(map(str, sys.version_info))
            requiredVersion = self['requiredPyVersionString']
            raise WillNotRunError(
                f'Required Python version is {requiredVersion},'
                f' but actual version is {pythonVersion}.')

    def checkRequiredOpSys(self):
        requiredOpSys = self.get('requiredOpSys')
        if requiredOpSys:
            # We accept a string or list of strings
            if isinstance(requiredOpSys, str):
                requiredOpSys = [requiredOpSys]
            opSys = os.name
            if opSys not in requiredOpSys:
                requiredOpSys = '/'.join(requiredOpSys)
                raise WillNotRunError(
                    f'Required operating system is {requiredOpSys},'
                    f' but actual operating system is {opSys}.')

    def checkDeniedOpSys(self):
        deniedOpSys = self.get('deniedOpSys')
        if deniedOpSys:
            # We accept a string or list of strings
            if isinstance(deniedOpSys, str):
                deniedOpSys = [deniedOpSys]
            opSys = os.name
            if opSys in deniedOpSys:
                deniedOpSys = '/'.join(deniedOpSys)
                raise WillNotRunError(
                    f'Will not run on operating system {deniedOpSys}'
                    f' and actual operating system is {opSys}.')

    def checkWillRunFunc(self):
        willRunFunc = self.get('willRunFunc')
        if willRunFunc:
            whyNotMsg = willRunFunc()
            if whyNotMsg:
                raise WillNotRunError(whyNotMsg)

    # endregion Self utility
