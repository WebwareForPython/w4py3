.. _migration-guide:

Migration Guide
===============

In this chapter we try to give some advice on what needs to be done to migrate an existing Webware for Python application to Webware for Python 3.

Regarding the API, we tried to stay compatible with Webware for Python 2 as much as possible, even though modern Python uses different naming conventions  and prefers the use of properties over getter and setter methods. So, in this regard, we expect a migration to Webware for Python 3 to be very smooth. The main points in a migration will be the conversion of the application from Python 2 to Python 3. the adaptation to the use of the WSGI standard instead of the custom application server, and maybe the usage of Webware plug-ins that are not supported anymore and may need to be migrated as well.

Check which Webware plug-ins you were using
-------------------------------------------

First you should check whether the plug-ins your application is using are still available as built-ins plugin of Webware for Python 3 (`w4py3 <https://github.com/WebwareForPython/w4py3>`_) or as externally provided plug-ins. PSP is still provided as a built-in plug-in. MiddleKit is now provided as an external plug-in on GitHub (`w4py3-middlekit <https://github.com/WebwareForPython/w4py3-middlekit>`_). The "COMKit", "CGIWrapper" and "KidKit" built-in plug-ins have been discontinued. Other external plug-ins that have been developed for Webware for Python 2 must first be ported to Webware for Python 3 before you can use them. See the section on :ref:`plug-ins` for details on how to write plug-ins for Webware for Python 3.

Migrate your application to Python 3
------------------------------------

The main migration effort will be porting your Webware application from Python 2 to Python 3. More precisely, Webware for Python 3 requires Python 3.6 or newer. This effort is necessary anyway, if you want to keep your Webware application alive for some more years, because the Python foundation declared to end Python 2 support on January 1st 2020, which means that Python 2 will also not be supported by newer operating systems anymore and not even get security updates anymore. The positive aspect of this is that your Webware application will run slightly faster and you can now make use of all the modern Python features and libraries in your application. Particularly, f-strings can be very handy when creating Webware applications.

We will not go into the details of migrating your application from Python 2 to Python 3 here, since much good advice is already available on the Internet, for instance:

* `Porting Python 2 Code to Python 3 <https://docs.python.org/3/howto/pyporting.html>`_ (Brett Cannon)
* `Supporting Python 3: An in-depth guide <http://python3porting.com/>`_ (Lennart Regebro)
* `The Conservative Python 3 Porting Guide <https://portingguide.readthedocs.io/en/latest/>`_ (Peter Viktorin et al)
* `How To Port Python 2 Code to Python 3 <https://www.digitalocean.com/community/tutorials/how-to-port-python-2-code-to-python-3/>`_ (Lisa Tagliaferri)
* `Migrating from Python 2 to Python 3 <https://www.techrepublic.com/article/migrating-from-python-2-to-python-3-a-guide-to-preparing-for-the-2020-deadline/>`_ (Nick Heath)
* `Migrating Applications From Python 2 to Python 3 <https://realpython.com/courses/migrating-applications-python-2-python-3/>`_ (Mahdi Yusuf)

Note that some of the how-tos also explain how to create code that is backward compatible with Python 2, which is much more difficult than just porting to Python 3, as we can do when migrating a Webware application to Python 3. So don't be frightened by the seeming complexity of the task -- it is probably much easier than you may think.

One of the biggest problems when migrating a Python 2 application to Python 3 is often the fact that in Python 3, strings are now always Unicode, while in Python 2, the native strings were byte strings and you had to add a "u" prefix to indicate that a string should be Unicode. However, this should not be a big issue when converting a Webware for Python application. Code such as ``self.write('<p>Hello, World!</p>')`` does not need to be modified. The fact that the string that is written to the output stream had been a byte string in Python 2 and is a Unicode string now in Python 3 is a detail that you as the application developer do not need to care about. Webware for Python 3 will encode everything properly to UTF-8 for you behind the scenes. If necessary, you can also change the output encoding from UTF-8 to something else with the ``OutputEncoding`` setting in the application configuration, but nowadays, UTF-8 is the usual and normally best choice.

Traditionally, Webware applications used simple print statements to output error or debug messages for logging or debugging purposes. You will need to change these print statements with print function calls when migrating from Python 2 to Python 3. In a future version of Webware for Python, we may change this and support a proper logging mechanism instead.

Use a WSGI server instead of the WebKit application server
----------------------------------------------------------

The other big change is that instead of using the custom "WebKit" application server, Webware for Python 3 utilizes the WSGI standard as the only way of serving applications. You will need to adapt your deployment accordingly. See the section on :ref:`deployment` for instructions on how to get your application into production using WSGI.

Search your application for direct references to the ``AppServer`` instance which does not exist anymore in Webware for Python 3. In most cases, you can replace these with references to the ``Application`` instance which also serves as the WSGI callable.

Also, search for references to the former ``WebKit`` package. This package does not exist anymore as separate plug-in in Webware for Python 3, its classes can now be found directly in the top level package of Webware for Python 3. So an import statement like ``from WebKit.Page import Page`` should be changed to a simple ``from Page import Page``.
