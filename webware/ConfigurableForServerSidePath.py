import os.path

from MiscUtils.Configurable import Configurable, NoDefault


class ConfigurableForServerSidePath(Configurable):
    """Configuration file functionality incorporating a server side path.

    This is a version of `MiscUtils.Configurable.Configurable` that provides
    a customized `setting` method for classes which have a `serverSidePath`
    method. If a setting's name ends with ``Filename`` or ``Dir``, its value
    is passed through `serverSidePath` before being returned.

    In other words, relative filenames and directory names are expanded with
    the location of the object, *not* the current directory.

    Application is a prominent class that uses this mix-in. Any class that
    has a `serverSidePath` method and a `Configurable` base class, should
    inherit this class instead.

    This is used for `MakeAppWorkDir`, which changes the `serverSidePath`.
    """

    def setting(self, name, default=NoDefault):
        """Return setting, using the server side path when indicated.

        Returns the setting, filtered by `self.serverSidePath()`,
        if the name ends with ``Filename`` or ``Dir``.
        """
        value = Configurable.setting(self, name, default)
        if name.endswith(('Dir', 'Filename')) and (
                value or name.endswith('Dir')):
            if name.endswith('LogFilename') and '/' not in value:
                value = os.path.join(
                    Configurable.setting(self, 'LogDir'), value)
            value = self.serverSidePath(value)  # pylint: disable=no-member
        return value
