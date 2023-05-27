.. _configuration:

Configuration
=============

Application.config
------------------

The settings for the Application and a number of components that use it as a central point of configuration, are specified in the ``Application.config`` file in the ``Configs`` directory of the application working directory.

General Settings
~~~~~~~~~~~~~~~~

``Contexts``:
    This dictionary maps context names to the directory holding the context content. Since the default contexts all reside in Webware, the paths are simple and relative. The context name appears as the first path component of a URL, otherwise ``Contexts['default']`` is used when none is specified. When creating your own application, you will add a key such as ``"MyApp"`` with a value such as ``"/home/apps/MyApp"``. That directory will then contain content such as Main.py, SomeServlet.py, SomePage.psp, etc. ``webware make`` will set up a context for your use as well. Default::

        {
            'default':   'Examples',
            'Admin':     'Admin',
            'Examples':  'Examples',
            'Docs':      'Docs',
            'Testing':   'Testing',
        }

``AdminPassword``:
    The password that, combined with the ``admin`` id, allows access to the ``AppControl`` page of the ``Admin`` context. Set interactively when ``install.py`` is run (no default value).
``PrintConfigAtStartUp``:
    Print the configuration to the console when the Application starts. Default: ``True`` (on).
``PlugIns``:
    Loads the plug-ins with the given names when starting the Application. Default: ``['MiscUtils', 'WebUtils', 'TaskKit', 'UserKit', 'PSP']``.
``CheckInterval``:
    The number of virtual instructions after which Python will check for thread switches, signal handlers, etc. This is passed directly to ``sys.setcheckinterval()`` if not set to ``None``. Default: ``None``.
``ResponseBufferSize``:
    Buffer size for the output response stream. This is only used when a servlet has set ``autoFlush`` to True using the ``flush()`` method of the Response. Otherwise, the whole response is buffered and sent in one shot when the servlet is done. Default: ``8192``.
``WSGIWrite``:
    If this is set to True, then the write() callable is used instead of passing the response as an iterable, which would be the standard WSGI mechanism. Default: ``True``.
``RegisterSignalHandler``:
    When the Application is regularly shut down, it tries to save its Sessions and stop the TaskManager. An atexit-handler will do this automatically. You can also shut down the Application manually by calling its ``shutDown()`` method. If this setting is set to True, then the Application will also register signal handlers to notice when it is shutdown and shut down cleanly. However, as the ``mod_wsgi`` documentation explains (see section on WSGIRestrictSignal_), "a well behaved Python WSGI application should not in general register any signal handlers of its own using ``signal.signal()``. The reason for this is that the web server which is hosting a WSGI application will more than likely register signal handlers of its own. If a WSGI application were to override such signal handlers it could interfere with the operation of the web server, preventing actions such as server shutdown and restart." Therefore, the default setting is: ``False``.

    .. _WSGIRestrictSignal: https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIRestrictSignal.html

Path Handling
~~~~~~~~~~~~~

These configuration settings control which files are exposed to users, which files are hidden, and some of how those files get chosen.

``DirectoryFile``:
    The list of basic filenames that Webware searches for when serving up a directory. Note that the extensions are absent since Webware will look for a file with any appropriate extension (``.py``., ``.html``, ``.psp``, etc). Default: ``["index", "Main"]``.
``ExtensionsForPSP``:
    This is the list of extensions for files to be parsed as PSP. Default: ``['.psp']``.
``ExtensionsToIgnore``:
    This is a list or set of extensions that Webware will ignore when autodetecting extensions. Note that this does not prevent Webware from serving such a file if the extension is given explicitly in a URL. Default: ``{'.pyc', '.pyo', '.py~', '.bak'}``.
``ExtensionsToServe``:
    This is a list of extensions that Webware will use exclusively when autodetecting extensions. Note that this does not prevent Webware from serving such a file if it is named explicitly in a URL. If no extensions are given all extensions will be served (usually anything but ``.py`` and ``.psp`` will be served as a static file). Default: ``[]``.
``UseCascadingExtensions``:
    If False, Webware will give a ``404 Not Found`` result if there is more than one file that could potentially match. If True, then Webware will use the ``ExtensionCascadeOrder`` setting to determine which option to serve. Default: ``True``.
``ExtensionCascadeOrder``:
    A list of extensions that Webware will choose, in order, when files of the same basename but different extensions are available. Note that this will have no effect if the extension is given in the URL. Default: ``[".psp", ".py", ".html"]``.
``FilesToHide``:
    A list or set of file patterns to protect from browsing. This affects all requests, and these files cannot be retrieved even when the extension is given explicitly. Default: ``{".*", "*~", "*bak", "*.tmpl", "*.pyc", "*.pyo", "*.config"}``.
``FilesToServe``:
    File patterns to serve from exclusively. If the file being served for a particular request does not match one of these patterns an ``HTTP 403 Forbidden`` error will be return. This affects all requests, not just requests with auto detected extensions. If set to ``[]`` then no restrictions are placed. Default: ``[]``.

Sessions
~~~~~~~~

``MemcachedNamespace``:
    The namespace used to prefix all keys from the Webware application when accessing Memcached servers for storing sessions. You should change this if you are using the same memcache for different applications. Default: ``'WebwareSession:'``.
``MemcachedOnIteration``:
    This setting determines how Webware behaves when attempting to iterate over the sessions or clear the session store, when using ``Memcached``. If you set it to ``Error``, this will raise an Exception, when set to ``Warning``, it will print a Warning, when set to ``None``, it will be ignored (the size of the session store will be always reported as zero). Default: ``Warning``.
``MemcachedServers``:
    This sets the list of Memcached servers used when setting ``SessionStore`` to ``Memcached``. Default: ``['localhost:11211']``.
``RedisNamespace``:
    The namespace used to prefix all keys from the Webware application when accessing Redis servers for storing sessions. You should change this if you are using the same Redis instance for different applications. Default: ``'WebwareSession:'``.
``RedisHost``:
    This sets the Redis host that shall be used when setting ``SessionStore`` to ``Redis``. Default: ``'localhost'``.
``RedisPort``:
    This sets the port for the Redis connection that shall be used when setting ``SessionStore`` to ``Redis``. Default: ``6379``.
``RedisDb``:
    This sets the database number for the Redis connection that shall be used when setting ``SessionStore`` to ``Redis``. Default: ``0``.
``RedisPassword``:
    This sets the password for the Redis connection that shall be used when setting ``SessionStore`` to ``Redis``. Default: ``None``.
``SessionModule``:
    Can be used to replace the standard Webware Session module with something else. Default: ``Session``
``SessionStore``:
    This setting determines which of five possible session stores is used by the Application: ``Dynamic``, ``File``, ``Memcached``, ``Memory``, ``Redis`` or ``Shelve``. The ``File`` store always gets sessions from disk and puts them back when finished. ``Memory`` always keeps all sessions in memory, but will periodically back them up to disk. ``Dynamic`` is a good cross between the two, which pushes excessive or inactive sessions out to disk. ``Shelve`` stores the sessions in a database file using the Python ``shelve`` module, ``Memcached`` stores them on a Memcached system using the ``python-memcached`` interface, and ``Redis`` stores them on a Redis system using the ``redis-py`` client. You can use a custom session store module as well. Default: ``Dynamic``.
``SessionStoreDir``:
    If ``SessionStore`` is set to ``File``, ``Dynamic`` or ``Shelve``, then this setting determines the directory where the files for the individual sessions or the shelve database will be stored. The path is interpreted as relative to the working directory (or Webware path, if you're not using a working directory), or you can specify an absolute path. Default: ``Sessions``.
``SessionTimeout``:
    Determines the amount of time (expressed in minutes) that passes before a user's session will timeout. When a session times out, all data associated with that session is lost. Default: ``60``.
``AlwaysSaveSessions``:
    If False, then sessions will only be saved if they have been changed. This is more efficient and avoids problems with concurrent requests made by the same user if sessions are not shared between these requests, as is the case for session stores other than ``Memory`` or ``Dynamic``. Note that in this case the last access time is not saved either, so sessions may time out if they are not altered. You can call ``setDirty()`` on sessions to force saving unaltered sessions in this case. If True, then sessions will always be saved. Default: ``True``.
``IgnoreInvalidSession``:
    If False, then an error message will be returned to the user if the user's session has timed out or doesn't exist. If True, then servlets will be processed with no session data. Default: ``True``.
``UseAutomaticPathSessions``:
    If True, then the Application will include the session ID in the URL by inserting a component of the form ``_SID_=8098302983`` into the URL, and will parse the URL to determine the session ID. This is useful for situations where you want to use sessions, but it has to work even if the users can't use cookies. If you use relative paths in your URLs, then you can ignore the presence of these sessions variables. The name of the field can be configured with the setting ``SessionName``. Default: ``False``.
``UseCookieSessions``:
    If True, then the application will store the session ID in a cookie with the name set in ``SessionName``, which is usually ``_SID_``. Default: ``True``.
``SessionCookiePath``:
    You can specify a path for the session cookie here. ``None`` means that the servlet path will be used, which is normally the best choice. If you rewrite the URL using different prefixes, you may have to specify a fixed prefix for all your URLs. Using the root path '/' will always work, but may have security issues if you are running less secure applications on the same server. Default: ``None``.
``SecureSessionCookie``:
    If True, then the Application will use a secure cookie for the session ID if the request was using an HTTPS connection. Default: ``True``.
``HttpOnlySessionCookie``:
    If True, then the Application will set the HttpOnly attribute on the session cookie . Default: ``True``.
``SameSiteSessionCookie``:
    If not ``None``, then the Application will set this value as the SameSite attribute on the session cookie . Default: ``Strict``.
``MaxDynamicMemorySessions``:
    The maximum number of dynamic memory sessions that will be retained in memory. When this number is exceeded, the least recently used, excess sessions will be pushed out to disk. This setting can be used to help control memory requirements, especially for busy sites. This is used only if the ``SessionStore`` is set to ``Dynamic``. Default: ``10000``.
``DynamicSessionTimeout``:
    The number of minutes of inactivity after which a session is pushed out to disk. This setting can be used to help control memory requirements, especially for busy sites. This is used only
    if the ``SessionStore`` is set to ``Dynamic``. Default: ``15``.
``SessionPrefix``:
    This setting can be used to prefix the session IDs with a string. Possible values are ``None`` (don't use a prefix), ``"hostname"`` (use the hostname as the prefix), or any other string (use that string as the prefix). You can use this for load balancing, where each Webware server uses a different prefix. You can then use mod_rewrite_ or other software for load-balancing to redirect each user back to the server they first accessed. This way the backend servers do not have to share session data. Default: ``None``.

    .. _mod_rewrite: https://httpd.apache.org/docs/current/mod/mod_rewrite.html

``SessionName``:
    This setting can be used to change the name of the field holding the session ID. When the session ID is stored in a cookie and there are applications running on different ports on the same host, you should choose different names for the session IDs, since the web browsers usually do not distinguish the ports when storing cookies (the port cookie-attribute introduced with RFC 2965 is not used). Default: ``_SID_``.
``ExtraPathInfo``:
    When enabled, this setting allows a servlet to be followed by additional path components which are accessible via HTTPRequest's ``extraURLPath()``. For subclasses of ``Page``, this would be ``self.request().extraURLPath()``. Default: ``False``.
``UnknownFileTypes``:
    This setting controls the manner in which Webware serves "unknown extensions" such as .html, .css, .js, .gif, .jpeg etc. The default setting specifies that the servlet matching the file is cached in memory. You may also specify that the contents of the files shall be cached in memory if they are not too large.

    If you are concerned about performance, use mod_rewrite_ to avoid accessing Webware for static content.

    The ``Technique`` setting can be switched to ``"redirectSansAdapter"``, but this is an experimental setting with some known problems.

    Default::

        {
            'ReuseServlets': True,  # cache servlets in memory
            'Technique': 'serveContent',  # or 'redirectSansAdapter'
            # If serving content:
            'CacheContent': False,  # set to True for caching file content
            'MaxCacheContentSize': 128*1024,  # cache files up to this size
            'ReadBufferSize': 32*1024  # read buffer size when serving files
        }

Caching
~~~~~~~

``CacheServletClasses``:
    When set to False, the Application will not cache the classes that are loaded for servlets. This is for development and debugging. You usually do not need this, as servlet modules are reloaded if the file is changed. Default: ``True`` (caching on).
``CacheServletInstances``:
    When set to False, the Application will not cache the instances that are created for servlets. This is for development and debugging. You usually do not need this, as servlet modules are reloaded and cached instances purged when the servlet file changes. Default: ``True`` (caching on).
``CacheDir``:
    This is the name of the directory where things like compiled PSP templates are cached. Webware creates a subdirectory for every plug-in in this directory. The path is interpreted as relative to the working directory (or Webware path, if you're not using a working directory), or you can specify an absolute path. Default: ``Cache``.
``ClearPSPCacheOnStart``:
    When set to False, the Application will allow PSP instances to persist from one application run to the next. If you have PSPs that take a long time to compile, this can give a speedup. Default: ``False`` (cache will persist).
``ReloadServletClasses``:
    During development of an application, servlet classes will be changed very frequently. The AutoReload mechanism could be used to detect such changes and to reload modules with changed servlet classes, but it would cause an application restart every time a servlet class is changed. So by default, modules with servlet classes are reloaded without restarting the server. This can potentially cause problems when other modules are dependent on the reloaded module because the dependent modules will not be reloaded. To allow reloading only using the AutoReload mechanism, you can set ``ReloadServletClasses`` to ``False`` in such cases. Default: ``True`` (quick and dirty reloading).

Errors
~~~~~~

``ShowDebugInfoOnErrors``:
    If True, then uncaught exceptions will not only display a message for the user, but debugging information for the developer as well. This includes the traceback, HTTP headers, form fields, environment and process ids. You will most likely want to turn this off when deploying the site for users. Default: ``True``.
``EnterDebuggerOnException``:
    If True, and if the AppServer is running from an interactive terminal, an uncaught exception will cause the application to enter the debugger, allowing the developer to call functions, investigate variables, etc. See the Python debugger (pdb) docs for more information. You will certainly want to turn this off when deploying the site. Default: ``False`` (off).
``IncludeEditLink``:
    If True, an "[edit]" link will be put next to each line in tracebacks. That link will point to a file of type ``application/x-webware-edit-file``, which you should configure your browser to run with ``bin/editfile.py``. If you set your favorite Python editor in ``editfile.py`` (e.g. ``editor = 'Vim'``), then it will automatically open the respective Python module with that editor and put the cursor on the erroneous line. Default: ``True``.
``IncludeFancyTraceback``:
    If True, then display a fancy, detailed traceback at the end of the error page. It will include the values of local variables in the traceback. This makes use of a modified version of ``cgitb.py`` which is included with Webware as ``CGITraceback.py``. The original version was written by Ka-Ping Yee. Default: ``False`` (off).
``FancyTracebackContext``:
    The number of lines of source code context to show if IncludeFancyTraceback is turned on. Default: ``5``.
``UserErrorMessage``:
    This is the error message that is displayed to the user when an uncaught exception escapes a servlet. Default: ``"The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!"``
``ErrorLogFilename``:
    The name of the file where exceptions are logged. Each entry contains the date and time, filename, pathname, exception name and data, and the HTML error message filename (assuming there is one). Default: ``Errors.csv``.
``SaveErrorMessages``:
    If True, then errors (e.g., uncaught exceptions) will produce an HTML file with both the user message and debugging information. Developers/administrators can view these files after the fact, to see the details of what went wrong. These error messages can take a surprising amount of space. Default: ``True`` (do save).
``ErrorMessagesDir``:
    This is the name of the directory where HTML error messages get stored. The path is interpreted as relative to the working directory, or you can specify an absolute path.Default: ``ErrorMsgs``.
``EmailErrors``:
    If True, error messages are e-mailed out according to the ErrorEmailServer and ErrorEmailHeaders settings. You must also set ``ErrorEmailServer`` and ``ErrorEmailHeaders``. Default: ``False`` (false/do not email).
``EmailErrorReportAsAttachment``:
    Set to True to make HTML error reports be emailed as text with an HTML attachment, or False to make the html the body of the message. Default: ``False`` (HTML in body).
``ErrorEmailServer``:
    The SMTP server to use for sending e-mail error messages, and, if required, the port, username and password, all separated by colons. For authentication via "SMTP after POP", you can furthermore append the name of a POP3 server, the port to be used and an ``SSL`` flag. Default: ``'localhost'``.
``ErrorEmailHeaders``:
    The e-mail headers used for e-mailing error messages. Be sure to configure ``"From"``, ``"To"`` and ``"Reply-To"`` before turning ``EmailErrors`` on. Default::

        {
            'From':         'webware@mydomain,
            'To':           ['webware@mydomain'],
            'Reply-To':     'webware@mydomain',
            'Content-Type': 'text/html',
            'Subject':      'Error'
        }

``ErrorPage``:
    You can use this to set up custom error pages for HTTP errors and any other exceptions raised in Webware servlets. Set it to the URL of a custom error page (any Webware servlet) to catch all kinds of exceptions. If you want to catch only particular errors, you can set it to a dictionary mapping the names of the corresponding exception classes to the URL to which these exceptions should be redirected. For instance::

       {
            'HTTPNotFound': '/Errors/NotFound',
            'CustomError':  '/Errors/Custom'
       }

    If you want to catch any exceptions except HTTP errors, you can set it to::

        {
            'Exception':     '/ErrorPage',
            'HTTPException': None
        }

    Whenever one of the configured exceptions is thrown in a servlet, you will be automatically forwarded to the corresponding error page servlet. More specifically defined exceptions overrule the more generally defined. You can even forward from one error page to another error page unless you are not creating loops. In an ``HTTPNotFound`` error page, the servlet needs to determine the erroneous URI with ``self.request().previousURI()``, since the ``uri()`` method returns the URI of the current servlet, which is the error page itself. When a custom error page is displayed, the standard error handler will not be called. So if you want to generate an error email or saved error report, you must do so explicitly in your error page servlet. Default: ``None`` (no custom error page).
``MaxValueLengthInExceptionReport``:
    Values in exception reports are truncated to this length, to avoid excessively long exception reports. Set this to ``None`` if you don't want any truncation. Default: ``500``.
``RPCExceptionReturn``:
    Determines how much detail an RPC servlet will return when an exception occurs on the server side. Can take the values, in order of increasing detail, ``"occurred"``, ``"exception"`` and ``"traceback"``. The first reports the string ``"unhandled exception``", the second prints the actual exception, and the third prints both the exception and accompanying traceback. All returns are always strings. Default: ``"traceback"``.
``ReportRPCExceptionsInWebware``:
    True means report exceptions in RPC servlets in the same way as exceptions in other servlets, i.e. in the logfiles, the error log, and/or by email. False means don't report the exceptions on the server side at all; this is useful if your RPC servlets are raising exceptions by design and you don't want to be notified. Default: ``True`` (do report exceptions).

Logging
~~~~~~~

``LogActivity``:
    If True, then the execution of each servlet is logged with useful information such as time, duration and whether or not an error occurred. Default: ``True``.
``ActivityLogFilenames``:
    This is the name of the file that servlet executions are logged to. This setting has no effect if ``LogActivity`` is False. The path can be relative to the Webware location, or an absolute path. Default: ``'Activity.csv'``.
``ActivityLogColumns``:
    Specifies the columns that will be stored in the activity log. Each column can refer to an object from the set [application, transaction, request, response, servlet, session] and then refer to its attributes using "dot notation". The attributes can be methods or instance attributes and can be qualified arbitrarily deep. Default: ``['request.remoteAddress', 'request.method', 'request.uri', 'response.size', 'servlet.name', 'request.timeStamp', 'transaction.duration', 'transaction.errorOccurred']``.
``AppLogFilename``:
    The Application redirects standard output and error to this file, if this is set in production mode. Default: ``'Application.log'``.
```LogDir``:
    The directory where log files should be stored. All log files without an explicit path will be put here. Default: ``'Logs'``.
``Verbose``:
    If True, then additional messages are printed while the Application runs, most notably information about each request such as size and response time. Default: ``True``.
``SilentURIs``:
    If ``Verbose`` is set to True, then you can use this setting to specify URIs for which you don't want to print any messages in the output of the Application. The value is expected to be a regular expression that is compared to the request URI. For instance, if you want to suppress output for images, JavaScript and CSS files, you can set ``SilentURIs`` to ``'\.(gif|jpg|jpeg|png|js|css)$'`` (though we do not recommend serving static files with Webware; it's much more efficient to deliver them directly from the Apache server). If set to ``None``, messages will be printed for all requests handled by Webware. Default: ``None``
