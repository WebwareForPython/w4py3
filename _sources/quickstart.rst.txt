.. _quickstart:

Quickstart
==========

In this chapter we will show how you can create and run a "hello world" application with Webware for Python 3, and try out the example servlets provided with Webware. In the next chapter, we will then go into a little bit more detail and create a slightly more complex application.

We assume you have already installed Webware for Python 3 into a virtual environment as explained in the chapter on :ref:`installation`.


The Webware CLI
---------------

Webware for Python 3 comes with a command line tool named "webware" that helps creating a new projects and starting a development web server. You can run ``webware`` with the ``--help`` option to see the available subcommands::

    webware --help

Remember that you need to activate the virtual environment where you installed Webware for Python 3 first if you haven't installed it globally.


Creating a Working Directory
----------------------------

You can use the subcommand ``make`` to start making a new Webware for Python application. This subcommand will create a new Webware for Python 3 application working directory with subdirectories for your Webware contexts, configuration, etc. and will also generate some boilerplate files to get you started. Again, use the ``--help`` option to see all available options::

    webware make --help

Let's start a simple "hello world" project using the ``make`` command::

    webware make HelloWorld

You should see some output on the console explaining what has been created for your. Particularly, you should now have a subdirectory "HelloWorld" in your current directory.

Each Webware application consists of one ore more "contexts", which correspond to different URL prefixes. Some contexts such as the "example" and "admin" contexts are already provided with Webware for Python by default.


Running the Webware Examples
----------------------------

You need to ``cd`` into the newly created application working directory first::

    cd HelloWorld

Now you can run the application with the following command::

    webware serve -b

The "serve" subcommand will start the development server, and the ``-b`` option will open your standard web browser with the base URL of the application -- by default this is ``http://localhost:8080/``. You should see a simple web page with the heading "Welcome to Webware for Python!" in your browser.

You should also a link to the "Exmples" context located at the URL ``http://localhost:8080/Examples/``. This context features several example servlets which you can select in the navigation side bar on the left side. Note that some of the examples need additional packages which should be installed as "extras" as explained in the chapter on :ref:`installation`.

Try one of the example now, e.g. the `CountVisits <http://localhost:8080/Examples/CountVisits>`_ servlet. This example demonstrates how to use Webware Sessions to keep application state. In the navigation bar you will also find a link to `view the source of CountVisits <http://localhost:8080/Examples/View?filename=CountVisits.py>`_. You will find that the source code for this servlet is very simple. It inherits from the ``ExamplePage`` servlet.


Using the Admin Context
-----------------------

Besides the "Examples" context, Webware for Python also provides an "Admin" context out of the box. By default it is located at the URL ``http://localhost:8080/Admin/``. You will notice an error message that says you first need to add an admin password using the ``AdminPassword`` setting in the ``Application.config`` configuration file.

You will find the configuration file in the ``Configs`` subdirectory of your application working directory. The configuration file defines all settings for the running Webware application using standard Python syntax. Try changing the ``AdminPassword`` defined at the top. You will notice that if you reload the admin context in your browser, you will still see the message about a missing admin password. You need to restart the application in order to make the changed application configuration effective. To do so, stop the running Webware application in your console with the Ctrl-C key combination, and start it again.

You can use the ``-r`` option to automatically restart the development server when files used in your application are changed::

    webware serve -r

The ``serve`` subcommands has a few more options which you can see by running it with the ``--help`` option::

    webware serve --help

After adding an admin password, you should be able to log in to the admin context using the user name "admin" and the admin password you selected.

In the navigation bar on the left side you now see several admin servlets. For example, the "Plug-ins" servlet lists all the Webware for Python plug-ins currently installed.


A "Hello World" Example
-----------------------

The ``make`` subcommand also created a subdirectory ``MyContext`` that serves as the default context for your application. You can rename this context in the ``Application.config`` file, or give it a different name with the ``-c`` option of the ``make`` subcommand. Let's leave the name for now -- since it is the default context, you do not need to pass it in the URL.

A newly created default context already contains one servlet ``Main.py``. Again, you don't need to pass this name in the URL, because it is the default name for the directory index, defined in the ``DirectoryFile`` setting of the application configuration file.

Let's add another very simple servlet ``HelloWorld.py`` to our default context. But first, let's add a link to this servlet to the ``Main`` servlet. Open the ``MyContext/Main.py`` file in your editor and add the following line at the bottom of the method ``writeContent()``::

    self.writeln('<ul><li><a href="HelloWorld">Hello, World!</a></li></ul>')

Everything that you pass to the ``writeln()`` method is written onto the current page. This is the main method you will be using in Webware for Python to create dynamic HTML pages. You can also use the ``write()`` method which does the same without appending a new-line character at the end. This approach is very similar to writing CGI applications. However, the servlets are kept in memory and not reloaded every time you visit a page, so Webware for Python is much more efficient. Also, servlets classes allow a much better structuring of your application using object oriented programming.

When you navigate to the start page of your application, you should now already see this link. For now, you will get an "Error 404" when trying to click on this link. In order to make it operational, save the following file as ``MyContext/HelloWorld.py`` in your application working directory::

    from Page import Page

    class HelloWorld(Page):

        def title(self):
            return 'Hello World Example'

        def writeContent(self):
            self.writeln('<h1>Hello, World!</h1>')

Now the link on the start page should work and you should see "Hello World!" on your page and whatever more you want to write in the `writeContent()` method above.

If you want to change the style of the page, use different colors or larger letters, you should use the ``writeStyleSheet()`` method to define an inline style sheet or link to a static CSS file. For example, try adding the following method to your `HelloWorld` class above::

        def writeStyleSheet(self):
            self.writeln('''<style>
    h1 {
        color: blue;
        font-size: 40px;
        font-family: sans-serif;
        text-align: center;
    }
    </style>''')
