.. _application-development:

Application Development
=======================

Webware provides Python classes for generating dynamic content from a web-based, server-side application. It is a significantly more
powerful alternative to CGI scripts for application-oriented development.

In this chapter we explain some more fundamental concepts of Webware for Python and describe best practices for developing a web application using Webware.


Core Concepts
-------------

The core concepts of Webware for Python are the Application, Servlet, Request, Response and Transaction, for which there are one or more Python classes.

The application resides on the server-side and manages incoming requests in order to deliver them to servlets which then produce responses that get sent back to the client. A transaction is a simple
container object that holds references to all of these objects and is accessible to all of them.

Content is normally served in HTML format over an HTTP connection. However, applications can provide other forms of content and the framework is designed to allow new classes for supporting
protocols other than HTTP.

In order to connect the web server and the application, Webware for Python 3 uses the Web Server Gateway Interface (WSGI). The Webware Application instance serves as the WSGI callable. The web server calls the Application, passing a dictionary containing CGI-style environment variables for every request. The Application then then processes the request and sends the response back to the web server, for which WSGI provides to different mechanisms. By default, Webware applications use the ``write()`` callable mechanism, because this is more suitable for the way Webware for Python applications create responses, by writing to an output stream. However, since not all WSGI servers support this mechanism, it is also possible to use the more usual WSGI mechanism of passing the response as an iterable. You will need to switch the ``Application.config`` setting ``WSGIWrite`` to ``False`` in order to use this mechanism.

Many different WSGI servers are available that can be used with Webware for Python 3. By default, Webware uses the `waitress`_ WSGI server as its development server. If you have installed Webware with the "development" or "test" extra, as recommended in the chapter on :ref:`Installation`, the waitress server should already be installed together with Webware for Python and will be used when running the ``webware serve`` command.

.. _waitress: https://docs.pylonsproject.org/projects/waitress/

In production, you may want to use a web server with better performance. In the chapter on :ref:`deployment` we describe how you can configure a web server like Apache to serve static files directly, while passing dynamic contents to the Webware application via WSGI, using the `mod_wsgi`_ module.

.. _mod_wsgi: https://modwsgi.readthedocs.io/

The whole process of serving a page with Webware for Python then looks like this:

* A user requests a web page by typing a URL or submitting a form.
* The user's browser sends the request to the remote Apache web server.
* The Apache web server passes the request to a mod_wsgi daemon process.
* The mod_wsgi daemon process collects information about the request and sends it to the Webware Application using the WSGI protocol.
* The Webware Application dispatch the raw request.
* The application instantiates an HTTPRequest object and asks the appropriate Servlet (as determined by examining the URL) to process it.
* The servlet generates content into a given HTTPResponse object, whose content is then sent back via WSGI to the mod_wsgi daemon process.
* The mod_wsgi daemon process sends the content through the web server and ultimately to the user's web browser.


Setting up your application
---------------------------

The first task in developing an application is to set up the file structure in which you will be working.

It is possible to put your application in a subdirectory at the path where the ``webware`` package is installed and change ``Configs/Application.config`` to add another context. But *do not do this*. Your application will be entwined with the Webware installation, making it difficult to upgrade Webware, and difficult to identify your own files from Webware files.


Creating a working directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead you should use the ``webware make`` command to create an application working directory. You should run it like::

    webware make -c Context -l Lib WorkDir

This will create a directory ``WorkDir`` that will contain a directory structure for your application. The options are:

``-c Context``:
    Use ``Context`` as the name for the application default context. A subdirectory with the same name will be created in the work dir (you can change that with the ``-d`` option). If you do not use the ``-c`` option, the context name will be ``MyContext``. You may simply want to call it ``App`` or ``Context``, particularly if you are using only one context. If you want to add more than one context, you need to create a subdirectory and a corresponding ``Contexts`` dictionary entry in the ``Application.config`` file manually.
``-l Lib``:
    Create a ``Lib`` directory in the work dir which will be added to the Python module search path. You can use the ``-l`` option multiple times; and you can also add already existent library directories outside of the work dir. If you want to add the work dir itself to the Python path, pass ``-l .``. In that case, you can import from any Python package placed directly in the working, including the Webware contexts. Note that the webware package will always be added to the Python module search path, so that you can and should import any Webware modules and sub packages directly from the top level.
``WorkDir``:
    The files will be put here. Name if after your application, place it where it is convenient for you. It makes sense to put the working directory together with the virtual environment where you installed Webware for Python inside the same distinct base directory. Install any other requirements either into the virtual environment or provide them in one of the directories specified with the ``-l`` option.

You can see all available options if you run ``webware make --help``.

When you run the ``webware make`` command with the options describe above, the following directory structure will be created inside the ``WorkDir`` directory::

    Cache/          Context/        ErrorMsgs/      Logs/           Sessions/
    Configs/        error404.html   Lib/            Scripts/        Static/

Here's what the files and directories are for:

``Cache``:
    A directory containing cache files. You won't need to look in here.
``Configs``:
    Configuration files for the application. These files are copied from the ``Configs`` subdirectory in the ``webware`` package, but are specific to this application.
``Context``:
    The directory for your default context. This is where you put your servlets. You can change its name and location with the ``-c`` and ``-d`` options. You can also change this subsequently in the ``Application.config`` file in the ``Configs`` directory, where you can also configure more than one context. You may also want to remove the other standard contexts that come with Webware from the config file.
``error404.html``:
    The static HTML page to be displayed when a page is not found. You can remove this to display a standard error message, modify the page according to your preferences, or use a custom error servlet instead by setting ``ErrorPage`` in the ``Application.config`` file appropriately.
``ErrorMsgs``:
    HTML pages for any errors that occur. These can pile up and take up considerable size (even just during development), so you'll want to purge these every so often.
``Lib``:
    An example for an application-specific library package that can be created ``-l`` option (in this case, ``-l Lib``).
``Logs``:
    Logs of accesses.
``Scripts``:
    This directory contains a default WSGI script named ``WSGIScript.py`` that can be used to start the development server or connect the Webware application with another WSGI server.
``Sessions``:
    Users sessions. These should be cleaned out automatically, you won't have to look in this directory.
``Static``:
    This directory can be used as a container for all your static files that are used by your application, but should be served directly via the web server.


Using a Version Control system for Your Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A version control system is a useful tool for managing your application. Currently, Git_ is the most popular one. These systems handle versioning, but they also make it possible for other people to see snapshots of your progress, for multiple developers to collaborate and work on an application simultaneously, and they create a sort of implicit file share for your project. Even if you are the only developer on an application, a version control system can be very helpful.

.. _Git: https://git-scm.com/

The working directory is a good place to start for creating a versioned project. Assuming you're using Git, you can get started by creating a repository and importing your project into the repository simply by running::

    cd WorkDir
    git init
    git add .
    git commit -m "initial import"

Note that a hidden ``.gitignore`` file with reasonable defaults has already been created for you in the working directory. It tells Git to ignore files with certain extensions (such as ``.log`` or ``.pyc`` files), and all the files in certain directories (``Cache``, ``ErrorMsgs``, ``Logs``, and ``Sessions``).


Structuring your Code
---------------------

Once you've got the basic files and directories in place, you're ready to go in and write some code. Don't let this document get in the way of developing the application how you choose, but here are some common patterns that have proven useful for Webware applications.

SitePage
~~~~~~~~

Subclass a ``SitePage`` from ``Page`` for your application. This subclass will change some methods and add some new methods. It serves as the basis and as a template for all the pages that follow. If you have added a ``Lib`` subdirectory to your working directory as explained above, place the ``SitePage.py`` file containing the ``SitePage`` class into that directory.

Some code you may wish to include in your ``SitePage``:

* Authentication and security
* Accessing common objects (e.g., a user object, or a document object)
* Page header and footer
* Common layout commands, like ``writeHeader``
* Database access

You may also want to add other frequently used functions into the ``SitePage`` module and then do ``from SitePage import *`` in each servlet. You can also put these functions in a dedicated ``SiteFuncs`` module, or distribute them in different modules, and import them explicitly, for better code readability and to avoid cluttering your namespace.

Whether you want to use functions or methods is up to you -- in many cases methods can be more easily extended or customized later, but sometimes method use can become excessive and create unnecessary dependencies
in your code.

A basic framework for your SitePage might be::

    from Page import Page


    class SitePage(Page):

        def respond(self, trans):
            if self.securePage():
                if not self.session().value('username', False):
                    self.respondLogIn()
                    return

        def securePage(self):
            """Override this method in your servlets to return True if the
            page should only be accessible to logged-in users -- by default
            pages are publicly viewable"""
            return False

        def respondLogin(self):
            # Here we should deal with logging in...
            pass

Obviously there are a lot of details to add in on your own which are specific to your application and the security and user model you are using.


Configuration
-------------

There are several configuration parameters through which you can alter how Webware behaves. They are described below, including their default values. Note that you can override the defaults by placing config files in the ``Configs/`` directory. A config file simply contains Python code assigning the settings you wish to override. For example::

    SessionStore = 'Memory'
    ShowDebugInfoOnErrors =  True

See the chapter on :ref:`configuration` for more information on settings.


Contexts
--------

Webware divides the world into *contexts*, each of which is a directory with its own files and servlets. Webware will only serve files out of its list of known contexts.

Some of the contexts you will find out of the box are ``Examples``, ``Documentation`` and ``Admin``. When viewing either an example or admin page, you will see a sidebar that links to all the contexts.

Another way to look at contexts is a means for "directory partitioning". If you have two distinct web applications (for example, ``PythonTutor`` and ``DayTrader``), you will likely put each of these in their own context. In this configuration, both web applications would be served by the same Application instance. Note that there may be also reasons to run multiple Application instances for serving your web applications. For instance, this would allow you to start and stop them independently, run them under different users to give them different permissions, or partition resources like number of threads individually among the web applications.

Instead of adding your own contexts you may wish to use the ``webware make`` command, which will partition your application from the Webware installation.

To add a new context, add to the ``Contexts`` dictionary of ``Application.config``. The key is the name of the context as it appears in the URL and the value is the path (absolute or relative to the application working directory). Often the name of the context and the name of the directory will be the same::

     'DayTrader': '/All/Web/Apps/DayTrader',

The URL to access DayTrader would then be something like: ``http://localhost:8080/DayTrader/``

The special name ``default`` is reserved to specify what context is served when none is specified (as in ``http://localhost:8080/``). Upon installation, this is the ``Examples`` context, which is convenient during development since it provides links to all the other contexts.

Note that a context can contain an ``__init__.py`` which will be executed when the context is loaded at Application startup. You can put any kind of initialization code you deem appropriate there.


Plug-ins
--------

A plug-in is a software component that is loaded by Webware in order to provide additional functionality without necessarily having to modify Webware's source.

The most infamous plug-in is PSP (Python Server Pages) which ships with Webware.

Plug-ins often provide additional servlet factories, servlet subclasses, examples and documentation. Ultimately, it is the plug-in author's choice as to what to provide and in what manner.

Technically, plug-ins are Python packages that follow a few simple conventions in order to work with Webware. See the chapter on :ref:`plug-ins` for information about writing your own.


Sessions
--------

Webware provides a Session utility class for storing data on the server side that relates to an individual user's session with your site. The ``SessionStore`` setting determines where the data is stored and can currently be set to ``Dynamic``, ``File``, ``Memcached``, ``Memory``, ``Redis`` or ``Shelve``.

Storing to the Dynamic session store is the fastest solution and is the default. This session storage method keeps the most recently used sessions in memory, and moves older sessions to disk periodically. All sessions will be moved to disk when the server is stopped. Note that this storage mechanism cannot be used in a multi-process environment, i.e. when you're running multiple Applications instances in different processes in production.

There are two settings in ``Application.config`` relating to this Dynamic session store. ``MaxDynamicMemorySessions`` specifies the maximum number of sessions that can be in memory at any one time. ``DynamicSessionTimeout`` specifies after what period of time sessions will be moved from memory to file. (Note: this setting is unrelated to the ``SessionTimeout`` setting below. Sessions which are moved to disk by the Dynamic Session store are not deleted). Alternatively to the Dynamic store, you can try out the Shelve session store which stores the sessions in a database file using the Python shelve module.

If you are using more than one Application instance for load-balancing, the Memcached store will be interesting for you. Using the python-memcached interface, it is able to connect to a Memcached system and store all the session data there. This allows user requests to be freely moved from one server to another while keeping their sessions, because they are all connected to the same memcache. Alternatively, using the redis-py client, the application can also store sessions in a Redis database.

All on-disk session information is located in the ``Sessions`` subdirectory of the application working directory.

Also, the ``SessionTimeout`` setting lets you set the number of minutes of inactivity before a user's session becomes invalid and is deleted. The default is 60. The Session Timeout value can also be changed dynamically on a per session basis.


Actions
-------

Suppose you have a web page with a form and one or more buttons. Normally, when the form is submitted, a method such as Servlet's ``respondToPost()`` or Page's ``writeBody()``, will be
invoked. However, you may find it more useful to bind the button to a specific method of your servlet such as ``new()``, ``remove()`` etc. to implement the command, and reserve ``writeBody()`` for displaying the page and the form that invokes these methods. Note that your "command methods" can then invoke ``writeBody()`` after performing their task.

The *action* feature of ``Page`` let's you do this. The process goes like this:

1. Add buttons to your HTML form of type ``submit`` and name ``_action_``. For example::

        <input name="_action_" type="submit" value="New">
        <input name="_action_" type="submit" value="Delete">

2. Alternately, name the submit button ``_action_methodName``. For example::

        <input name="_action_New" type="submit" value="Create New Item">

3. Add an ``actions()`` method to your class to state which actions are valid. (If Webware didn't force you to do this, someone could potentially submit data that would cause any method of your servlet to be run). For example::

       def actions(self):
           return SuperClass.actions(self) + ['New', 'Delete']

4. Now you implement your action methods.

The ``ListBox`` example shows the use of actions (in ``Examples/ListBox.py``).

Note that if you proceed as in 1., you can add a ``methodNameForAction()`` method to your class transforming the value from the submit button (its label) to a valid method name. This will be needed, for instance, if there is a blank in the label on the button. However, usually it's simpler to proceed as in 2. in such cases.


Naming Conventions
------------------

Cookies and form values that are named with surrounding underscores (such as ``_sid_`` and ``_action_``) are generally reserved by Webware and various plugins and extensions for their own internal purposes. If you refrain from using surrounding underscores in your own names, then (a) you won't accidentally clobber an already existing internal name and (b) when new names are introduced by future versions of Webware, they won't break your application.


Errors and Uncaught Exceptions
------------------------------

One of the conveniences provided by Webware is the handling of uncaught exceptions. The response to an uncaught exception is:

* Log the time, error, script name and traceback to standard output.
* Display a web page containing an apologetic message to the user.
* Save a technical web page with debugging information so that developers can look at it after-the-fact. These HTML-based error messages are stored one-per-file, if the ``SaveErrorMessages`` setting is true (the default). They are stored in the directory named by the ``ErrorMessagesDir`` (defaults to ``"ErrorMsgs"``).
* Add an entry to the error log, found by default in ``Logs/Errors.csv``.
* E-mail the error message if the ``EmailErrors`` setting is true, using the settings ``ErrorEmailServer`` and ``ErrorEmailHeaders``. See :ref:`configuration` for more information. You should definitely set these options when deploying a web site.

Archived error messages can be browsed through the administration_ page.

Error handling behavior can be configured as described in :ref:`configuration`.


Activity Log
------------

Three options let you control:

* Whether or not to log activity (``LogActivity``, defaults to 0, i.e. off)
* The name of the file to store the log (``ActivityLogFilename``, defaults to ``Activity.csv``)
* The fields to store in the log (``ActivityLogColumns``) </ul>

See the chapter on :ref:`configuration` for more information.


Administration
--------------

Webware has a built-in administration page that you can access via the ``Admin`` context. You can see a list of all contexts in the sidebar of any ``Example`` or ``Admin`` page.

The admin pages allows you to view Webware's configuration, logs, and servlet cache, and perform actions such as clearing the cache or reloading selected modules.

More sensitive pages that give control over the application require a user name and password, the username is ``admin``, and you can set the password with the ``AdminPassword`` setting in the ``Application.config`` file.

The administration scripts provide further examples of writing pages with Webware, so you may wish to examine their source in the ``Admin`` context.


Debugging
---------

Development Mode
~~~~~~~~~~~~~~~~

When creating the Application instance, it takes a ``development`` flag as argument that defines whether it should run in "development mode" or "production mode". By default, if no such flag is passed, Webware checks whether the environment varibale ``WEBWARE_DEVELOPMENT`` is set and not empty. When you run the development server using the ``webware serve`` command, the flag is automatically set, so you are running in "development mode", unless you add the ``--prod`` option on the command line. The development flag is also available with the name ``Development`` in the ``Application.config`` file and used to make some reasonable case distinctions depending on whether the application is running in development mode. For instance, debugging information is only shown in development mode.

print
~~~~~

The most common technique is the infamous ``print`` statement which has been replaced with a ``print()`` function in Python 3. The results of ``print()`` calls go to the console where the WSGI server was started (not to the HTML page as would happen with CGI). If you specify ``AppLogFilename`` in ``Application.config``, this will cause the standard output and error to be redirected to this file.

For convenient debugging, the default ``Application.config`` file already uses the following conditional setting::

    AppLogFilename = None if Development else 'Application.log'

This will prevent standard output and error from being redirected to the log file in development mode, which makes it easier to find debugging output, and also makes it possible to use ``pdb`` (see below).

Prefixing the debugging output with a special tag (such as ``>>``) is useful because it stands out on the console and you can search for the tag in source code to remove the print statements after they are no longer useful. For example::

    print('>> fields =', self.request().fields())

Raising Exceptions
~~~~~~~~~~~~~~~~~~

Uncaught exceptions are trapped at the application level where a useful error page is saved with information such as the traceback, environment, fields, etc. In development mode, you will see this error page directly. In production, you can examine the saved page, and you can also configure the application to automatically e-mail you this information.

When an application isn't behaving correctly, raising an exception can be useful because of the additional information that comes with it. Exceptions can be coupled with messages, thereby turning them into
more powerful versions of the ``print()`` call. For example::

    raise Exception(f'self = {self}')

While this is totally useful during development, giving away too much internal information is also a security risk, so you should make sure that the application is configured properly and no such debugging output is ever shown in production.

Reloading the Development Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a servlet's source code changes, it is reloaded. However, ancestor classes of servlets, library modules and configuration files are not. You may wish to enable the auto-reloading feature when running the development server, by adding the ``-r`` or ``--reload`` option to the ``webware serve command`` in order to mitigate this problem.

In any case, when having problems, consider restarting the development server (or the WSGI server you are running in production).

Another option is to use the AppControl page of the ``Admin`` context to clear the servlet instance and class cache (see `Administration`_).

Assertions
~~~~~~~~~~

Assertions are used to ensure that the internal conditions of the application are as expected. An assertion is equivalent to an ``if`` statement coupled with an exception. For example::

    assert shoppingCart.total() >= 0, \
        f'shopping cart total is {shoppingCart.total()}'

Debugging using PDB
~~~~~~~~~~~~~~~~~~~
To use Python's built-in debugger ``pdb``, see the tip above about setting ``AppLogFilename`` for convenient debugging.

To have Webware automatically put you into pdb when an exception occurs, set this in your ``Application.config`` file::

    EnterDebuggerOnException = Development

A quick and easy way to debug a particular section of code is to add these lines at that point in the code::

    import pdb
    pdb.set_trace()

Debugging in an IDE
~~~~~~~~~~~~~~~~~~~

You can also use PyCharm or other Python IDEs to debug a Webware application. To do this, first configure the IDE to use the virtual environment where you installed Webware for Python.

Then, create the following script ``serve.py`` on the top level of your application working directory::

    #!/usr/bin/python3

    from webware.Scripts.WebwareCLI import main

    main(['serve'])

Now run this file in your IDE in debug mode. For instance, in PyCharm, right-click on ``serve.py`` and select "Debug 'serve'".

Some IDEs like PyCharm can also debug remote processes. This could be useful to debug a test or production server.


Bootstrap Webware from Command line
-----------------------------------

You may be in a situation where you want to execute some part of your Webware applicaton from the command line, for example to implement a cron job or maintenance script. In these situations you probably don't want to instantiate a full-fledged `Application` -- some of the downsides are that doing so would cause standard output and standard error to be redirected to the log file, and that it sets up the session sweeper, task manager, etc. But you may still need access to plugins such as MiscUtils, MiddleKit, which you may not be able to import directly.

Here is a lightweight approach which allows you to bootstrap Webware and plugins::

   import webware
   app = webware.mockAppWithPlugins()

   # now plugins are available...
   import MiscUtils
   import MiddleKit


How do I Develop an App?
------------------------

The answer to that question might not seem clear after being deluged with all the details. Here's a summary:

* Make sure you can run the development server. See the :ref:`quickstart` for more information.

* Go through the :ref:`beginner-tutorial`.

* Read the source to the examples (in the ``Examples`` subdirectory), then modify one of them to get your toes wet.

* Create your own new example from scratch. Ninety-nine percent of the time you will be subclassing the ``Page`` class.

* Familiarize yourself with the class docs in order to take advantage of classes like Page, HTTPRequest, HTTPResponse and Session.

* With this additional knowledge, create more sophisticated pages.

* If you need to secure your pages using a login screen, you'll want to look at the SecurePage, LoginPage, and SecureCountVisits examples in ``Examples``. You'll need to modify them to suit your particular needs.


