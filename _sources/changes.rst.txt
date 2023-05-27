.. _list-of-changes:

List of Changes
===============

What's new in Webware for Python 3
----------------------------------

This is the full list of changes in Webware for Python 3 (first version 3.0.0) compared with Webware for Python 2 (last version 1.2.3):

* Webware for Python 3 now requires Python 3.6 or newer, and makes internal use of newer Python features where applicable. Webware applications must now be migrated to or written for Python 3.
* The "Application" instance is now callable and usable as a WSGI application.
* The application server ("AppServer" class and subclasses including the "ThreadedAppServer") and the various adapters and start scripts and other related scripts for the application server are not supported anymore. Instead, Webware applications are now supposed to be served as WSGI applications using a WSGI server such as waitress, which is now used as the development server.
* The "ASSStreamOut" class has been replaced by a "WSGIStreamOut" class. The "Message" class has been removed, since it was not really used for anything, simplifying the class hierarchy a bit.
* The Application now has a development flag that can be checked to modify the application and its configuration depending on whether it is running in development or production mode.
* The custom "install" script has been replaced by a standard "setup" script, Webware for Python 3 is now distributed as a normal Python package that can be installed in the usual way. The "ReleaseHelper" and "setversion" scripts are not used anymore.
* The "MakeAppWorkDir" script has been moved to a new "Scripts" directory, which now also contains a "WSGIScript" and a "WaitressServer" script which serve as replacements for the old "AppServer" and "Launch" start scripts. These scripts can now be started as subcommands of a new webware console script, which serves as a new common Webware CLI.
* Instead of the "AutoReloadingAppServer", you can use the "reload" option of the WaitressServer script which uses hupper to monitor the application files and reload the waitress server if necessary. The "ImportSpy" has been removed.
* The classes of the core "WebKit" component are now available at the root level of Webware for Python 3, and the WebKit component ceased to exist as a separate plug-in.
* Some built-in plug-ins are not supported anymore: "CGIWrapper", "ComKit" and "KidKit".
* "MiddleKit" is not a built-in plug-in anymore, but is provided as a separate project on GitHub now (WebwareForPython/w4py3-middlekit).
* Webware now uses entry points for discovering plug-ins instead of the old plug-in system, and the plug-in API has slightly changed. Existing plug-ins must be adapted to Python 3 and the new plug-in API.
* The documentation has been moved to a separate directory and is built using Sphinx, instead providing a "Docs" context for Webware and every plug-in, and using custom documentation builders in the install script. The existing content has been reformatted for Sphinx, adapted and supplemented.
* The various examples have been slightly improved and updated. Demo servlets showing the use of Dominate and Yattag for creating HTML in a Pythonic way have been added.
* The side bar page layout now uses divs instead of tables.
* The test suite has been expanded and fully automated using the unit testing framework in the Python standard library. We also use tox to automate various checks and running the test suite with different Python versions.
* In particular, end-to-end tests using Twill have been replaced by more efficient unit tests using WebTest.
* Internal assert statements have been removed or replaced with checks raising real errors.
* The style guide has been slightly revised. We now rely on flake8 and pylint instead of using the custom "checksrc" script.

See also the list of `releases`_ on GitHub for all changes in newer releases of Webware for Python 3 since the first alpha release 3.0.0a0.

.. _releases: https://github.com/WebwareForPython/w4py3/releases
