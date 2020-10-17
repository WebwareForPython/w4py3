.. _overview:

Overview
========


Synopsis
--------

Webware for Python is a framework for developing object-oriented, web-based applications.

The project had been initiated in 1999 by Chuck Esterbrook with the goal of creating the ultimate web development suite for Python, and it soon got a lot of attraction. Jay Love, Geoff Talvola and Ian Bicking were other early contributors and core developers.

They created a mature and stable web framework that has been used in production for a long time by a variety of people in different environments. Since then, a lot of other web frameworks for Python emerged and have taken the lead, such as Django, Flask or Pyramid, while Webware for Python got less attention. Webware for Python was still available, maintained and slightly improved by Christoph Zwerschke, and happily used here and there, but did not change much over the years.

Since Webware for Python was based on Python 2, for which support ended 20 years later at the end of 2019, but there were still Webware for Python applications in the wild running happily after 2020, Christoph Zwerschke created a Python 3 based edition of the project called `Webware for Python 3`_.


Design Points and Changes
-------------------------

`Webware for Python 3`_ kept the following ideas and key goals from the `original project`_:

* **Simplicity**. Webware's code is quite simple and easy to understand if you feel the need to extend it.
* **Servlets**. Similar to Java servlets, they provide a familiar basis for the construction of web applications.
* **Robustness**. A crash of one page will not crash the server. Exception reports are logged and easy to read when developing.
* **Object-programming programming** (making good use of multiple inheritance and the template method pattern).
* **Extensibility** via plug-ins.
* **Python Server Pages** (PSP, similar to ASP, PHP and JSP) as a built-in plug-in.
* Built-in plug-ins for **Task scheduling** and **User management**.
* Excellent **documentation** and numerous **examples**.

Another key goal of the original project was to provide a "Pythonic" API, instead of simply copying Java APIs. However, the project was created when Python 2 was still in its infancy, lacking many modern features and conventions such as PEP-8. Therefore, the Webware for Python API is a bit different from what is considered "Pythonic" nowadays. Particularly, it uses getters and setters instead of properties (but without the "get" prefix for getters), and camelCase method names instead of snake_case. In order to facilitate migration of existing projects, Webware for Python 3 kept this old API, even though it is not in line with PEP-8 and could be simplified by using properties. Modernizing the API will be a goal for a possible third edition of Webware for Python, as well as using the Python logging facility which did not yet exist when Webware for Python was created and is still done via printing to the standard output.

The plug-in architecture has also been kept in Webware for Python 3, but now implemented in a more modern way using entry points for discovering plug-ins. Old plug-ins are not compatible, but can be adapted quite easily. The old Webware for Python installer has been replaced by a standard setup.py based installation.

The most incisive change in Webware for Python 3 is the discontinuation of the threaded application server that was part of the built-in "WebKit" plug-in and actually one of the strong-points of Webware for Python. However, a threaded application based architecture may not be the best option anymore for Python in the age of multi-core processors due to the global interpreter lock (`GIL`_), and maintaining the application server based architecture would have also meant to maintain the various adapters such as ``mod_webkit`` and the start scripts for the application server for various operating systems. This did not appear to be feasible. At the same time, Python nowadays already provides a standardized way for web frameworks to deploy web applications with the Python Web Server Gateway Interface (`WSGI`_). By making the already existing Application class of Webware for Python usable as a WSGI application object, Webware applications can now be deployed in a standardized way using any WSGI compliant web server, and the necessity for operating as an application server itself has been removed. Webware for Python 3 applications deployed using ``mod_wsgi`` are even performing better and can be scaled in more ways than applications for the original Webware for Python that have been deployed using ``mod_webkit`` which used to be the deployment option with the best performance. During development, the waitress_ WSGI server is used to serve the application, replacing the old built-in HTTP server. As a structural simplification that goes along with the removal of the WebKit application server, the contents of the WebKit plug-in are now available at the top level of Webware for Python 3, and WebKit ceased to exist as a separate plug-in.

The second incisive change in Webware for Python 3 is the removal of the "MiddleKit" as a built-in plug-in. This plug-in served as a middle tier between the data storage and the web interface, something that nowadays is usually done with an object relational mapper (ORM_) such as SQLAlchemy_. MiddleKit was a powerful component that many users liked and used in production, but was also pretty complex, with adapters to various databases, and therefore hard to maintain. It made sense to swap it out and provide `MiddleKit for Webware for Python 3`_ as a separate, external plug-in on GitHub. Also removed were the "CGIWrapper", "COMKit" and "KidKit" built-in plug-ins, because they have become obsolete or outdated. The other built-in plug-ins were less complex than MiddleKit and were kept as built-in plug-ins of Webware for Python 3. Particularly, "PSP, "UserKit" and "TaskKit" are still available in Webware for Python 3.

To facilitate web development with Webware for Python 3, a ``webware`` console script has been added that can be used to create working directories for new application and start the development server. This script replaces the old ``MakeAppWorkDir`` and ``AppServer`` scripts. When creating a new working directory, a WSGI script will also be created that can be used to attach the application to a web server.

The documentation contexts of the various plug-ins have been replaced by a common Sphinx based documentation provided in the top-level ``docs`` directory. The tests are still contained in ``Tests`` subdirectories at the top and plug-in levels, but the test suite has been expanded and is using the unittest framework consistently. The twill_ tests have also been replaced by unit tests based using WebTest_. They make sure that all servlets in the examples and testing contexts work as expected. Since Webware for Python 3 uses WSGI, WebTest can now also be used to test applications built with Webware for Python 3.

Otherwise, not much has been changed, so that migrating existing Webware for Python applications to Webware for Python 3 should be straight forward. Of course, you still need to migrate your Webware applications from `Python 2 to Python 3`_, but meanwhile a lot of tools and guidelines have been provided that help making this process as painless as possible.

See the :ref:`list-of-changes` and the :ref:`migration-guide` for more detailed information.


Download and Installation
-------------------------

See the chapter on :ref:`installation` for instructions how to download and install Webware for Python 3.


Documentation
-------------

This documentation is available online via `GitHub Pages`_ and via `Read the Docs`_.


Feedback, Contributing and Support
----------------------------------

You can use the `discussion mailing list`_ to give feedback, discuss features and get help using Webware.

You can also report issues_ and send in `pull requests`_ using the `GitHub project page`_ of Webware for Python 3.

You can keep up on new releases through the very low traffic `announcement mailing list`_ or subscribing to `releases`_ on GitHub.

.. _Webware for Python 3: https://webwareforpython.github.io/w4py3/
.. _original project: https://webwareforpython.github.io/w4py/
.. _waitress: https://docs.pylonsproject.org/projects/waitress/
.. _gil: https://realpython.com/python-gil/
.. _wsgi: https://www.fullstackpython.com/wsgi-servers.html
.. _ORM: https://en.wikipedia.org/wiki/Object-relational_mapping
.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _MiddleKit for Webware for Python 3: https://github.com/WebwareForPython/w4py3-middlekit
.. _twill: https://twill-tools.github.io/twill/
.. _WebTest: https://docs.pylonsproject.org/projects/webtest/en/latest/
.. _Python 2 to Python 3: https://docs.python.org/3/howto/pyporting.html
.. _discussion mailing list: https://sourceforge.net/projects/webware/lists/webware-discuss
.. _announcement mailing list: https://sourceforge.net/projects/webware/lists/webware-announce
.. _GitHub project page: https://github.com/WebwareForPython/w4py3
.. _GitHub pages: https://webwareforpython.github.io/w4py3/
.. _Read the Docs: https://webware-for-python-3.readthedocs.io/
.. _issues: https://github.com/WebwareForPython/w4py3/issues
.. _pull requests: https://github.com/WebwareForPython/w4py3/pulls
.. _releases: https://github.com/WebwareForPython/w4py3/releases
