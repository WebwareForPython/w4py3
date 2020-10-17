"""Configurable.py

Provides configuration file functionality.
"""

import os
import sys

from MiscUtils import AbstractError, NoDefault

from .Funcs import valueForString


class ConfigurationError(Exception):
    """Error in configuration file."""


class Configurable:
    """Abstract superclass for configuration file functionality.

    Subclasses should override:

      * defaultConfig()  to return a dictionary of default settings
                         such as {'Frequency': 5}

      * configFilename() to return the filename by which users can
                         override the configuration such as 'Pinger.config'

    Subclasses typically use the setting() method, for example:

        time.sleep(self.setting('Frequency'))

    They might also use the printConfig() method, for example:

        self.printConfig()     # or
        self.printConfig(file)

    Users of your software can create a file with the same name as
    configFilename() and selectively override settings. The format of
    the file is a Python dictionary.

    Subclasses can also override userConfig() in order to obtain the
    user configuration settings from another source.
    """

    # region Init

    def __init__(self):
        self._config = None

    # endregion Init

    # region Configuration

    def config(self):
        """Return the configuration of the object as a dictionary.

        This is a combination of defaultConfig() and userConfig().
        This method caches the config.
        """
        if self._config is None:
            self._config = {
                **self.defaultConfig(),
                **self.userConfig(),
                **self.commandLineConfig()}
        return self._config

    def setting(self, name, default=NoDefault):
        """Return the value of a particular setting in the configuration."""
        if default is NoDefault:
            try:
                return self.config()[name]
            except KeyError as e:
                keys = ', '.join(sorted(self.config()))
                raise KeyError(
                    f'{name} not found - config keys are: {keys}') from e
        else:
            return self.config().get(name, default)

    def setSetting(self, name, value):
        """Set a particular configuration setting."""
        self.config()[name] = value

    def hasSetting(self, name):
        """Check whether a configuration setting has been changed."""
        return name in self.config()

    def defaultConfig(self):
        """Return a dictionary with all the default values for the settings.

        This implementation returns {}. Subclasses should override.
        """
        return {}

    def configFilename(self):
        """Return the full name of the user config file.

        Users can override the configuration by this config file.
        Subclasses must override to specify a name.
        Returning None is valid, in which case no user config file
        will be loaded.
        """
        raise AbstractError(self.__class__)

    def configName(self):
        """Return the name of the configuration file without the extension.

        This is the portion of the config file name before the '.config'.
        This is used on the command-line.
        """
        return os.path.splitext(os.path.basename(self.configFilename()))[0]

    def configReplacementValues(self):
        """Return a dictionary for substitutions in the config file.

        This must be a dictionary suitable for use with "string % dict"
        that should be used on the text in the config file.
        If an empty dictionary (or None) is returned, then no substitution
        will be attempted.
        """
        return {}

    def userConfig(self):
        """Return the user config overrides.

        These settings can be found in the optional config file.
        Returns {} if there is no such file.

        The config filename is taken from configFilename().
        """
        # pylint: disable=assignment-from-no-return
        filename = self.configFilename()
        if not filename:
            return {}
        try:
            contents = self.readConfig(filename)
        except IOError as e:
            print('WARNING: Config file', filename, 'not loaded:', e.strerror)
            print()
            return {}
        if contents.lstrip().startswith('{'):
            raise ConfigurationError(
                'Configuration via a dict literal is not supported anymore.')
        try:
            from ImportManager import ImportManager
            ImportManager().watchFile(filename)
        except Exception as e:
            print('WARNING: Config file', filename, 'cannot be watched:', e)
            print()
        config = self.configReplacementValues().copy()
        try:
            exec(contents, config)
            keys = [key for key in config if key.startswith('_')]
            for key in keys:
                del config[key]
        except Exception as e:
            raise ConfigurationError(
                f'Invalid configuration file, {filename} ({e}).') from e
        return config

    @staticmethod
    def readConfig(filename):
        """Read the configuration from the file with the given name.

        Raises an UIError if the configuration cannot be read.

        This implementation assumes the file is stored in utf-8 encoding with
        possible BOM at the start, but also tries to read as latin-1 if it
        cannot be decoded as utf-8. Subclasses can override this behavior.
        """
        try:
            with open(filename, encoding='utf-8-sig') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filename, encoding='latin-1') as f:
                return f.read()

    def printConfig(self, dest=None):
        """Print the configuration to the given destination.

        The default destination is stdout. A fixed with font is assumed
        for aligning the values to start at the same column.
        """
        if dest is None:
            dest = sys.stdout
        config = self.config()
        width = max(map(len, config))
        for key in sorted(config):
            dest.write(f'{key.ljust(width)} = {self.setting(key)!r}\n')
        dest.write('\n')

    def commandLineConfig(self):
        """Return the settings that came from the command-line.

        These settings come via addCommandLineSetting().
        """
        return _settings.get(self.configName(), {})

    # endregion Configuration


# region Command line settings

_settings = {}


def addCommandLineSetting(name, value):
    """Override the configuration with a command-line setting.

    Take a setting, like "Application.Verbose=0", and call
    addCommandLineSetting('Application.Verbose', '0'), and
    it will override any settings in Application.config
    """
    configName, settingName = name.split('.', 1)
    value = valueForString(value)
    if configName not in _settings:
        _settings[configName] = {}
    _settings[configName][settingName] = value


def commandLineSetting(configName, settingName, default=NoDefault):
    """Retrieve a command-line setting.

    You can use this with non-existent classes, like "Context.Root=/Webware",
    and then fetch it back with commandLineSetting('Context', 'Root').
    """
    if default is NoDefault:
        return _settings[configName][settingName]
    return _settings.get(configName, {}).get(settingName, default)

# endregion Command line settings
