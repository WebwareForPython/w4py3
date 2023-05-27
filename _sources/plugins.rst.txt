.. _plug-ins:

Plug-ins
========

Webware for Python supports "plug-ins" to extend the framework and provide additional capabilities.

In Webware for Python 3, plug-ins are implemented as packages with metadata ("entry points") through which they can be automatically discovered, even if they have been installed independetly of Webware. You only need to specify which plug-ins shall be loaded in the ``PlugIns`` configuration setting, and Webware will automatically load them if they are installed.

Every Webware plug-in is a Python package, i.e. a directory that contains a ``__init__.py`` file and optionally other files. As a Webware plugin, it must also contain a special ``Properties.py`` file. You can disable a specific plug-in by placing a ``dontload`` file in its package directory.

If you want to distribute a Webware plug-in, you should advertize it as an entry point using the ``webware.plugins`` identifier in the ``setup.py`` file used to install the plug-in.

The ``__init.py__`` file of the plug-in must contain at least a function like this::

    def installInWebware(application):
        pass

The function doesn't need to do anything, but this gives it the opportunity to do something with the global Webware ``Application`` object. For instance, the PSP plugin uses ``addServletFactory.addServletFactory`` to add a handler for ``.psp`` files.

The ``Properties.py`` file should contain a number of assignments::

    name = "Plugin name"
    version = (1, 0, 0)
    status = 'beta'
    requiredPyVersion = (3, 6)
    requiredOpSys = 'posix'
    synopsis = """A paragraph-long description of the plugin"""
    webwareConfig = {
        'examplePages': [
            'Example1',
            'ComplexExample',
            ]
        }
    def willRunFunc():
        if softwareNotInstalled:
            return "some message to that effect"
        else:
            return None

If you want to provide some examples for using your plug-in, they should be put in an ``Examples/`` subdirectory.

A plugin who's ``requiredPyVersion`` or ``requiredOpSys`` aren't satisfied will simply be ignored.  ``requiredOpSys`` should be something returned by ``os.name``, like ``posix`` or ``nt``.  Or you can define a function ``willRunFunc`` to test.  If there aren't requirements you can leave these variables and functions out.

If you plan to write your own Webware plug-in, also have a look at our :ref:`style-guidelines` and the source code of the built-in plug-ins (PSP, TaskKit, UserKit, WebUtils, MiscUtils) which can serve as examples. We also recommend to add some tests to your plug-in, see the section on :ref:`testing`.


