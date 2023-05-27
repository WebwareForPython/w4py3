.. _testing:

Testing
=======

In this section we want to give some advice on testing Webware applications and Webware itself.


Testing Webware itself
----------------------

The unit tests and end to end tests for Webware for Python can be found in the ``Tests`` subdirectories of the root ``webware`` package and its plug-ins. Webware also has a built-in context ``Testing`` that contains some special servlets for testing various functionality of Webware, which can be invoked manually, but will also be tested automatically as part of the end-to-end tests.

Before running the test suite, install Webware for Python into a virtual environment and activate that environment. While developing and testing Webware, it is recommended to install Webware in editable mode. To do this, unpack the source installation package of Webware for Python 3, and run this command in the directory containing the ``setup.py`` file::

    pip install -e .[tests]

Next, change into the directory containing the main Webware package::

    cd webware

To test everything, run::

    python -m unittest discover -p Test*.py

To test everything, and stop on the first failing test::

    python -m unittest discover -p Test*.py -f

To test everything, and print verbose output::

    python -m unittest discover -p Test*.py -v

To test only UserKit::

    python -m unittest discover -p Test*.py -vs UserKit

To test only the example servlets in the default context::

    python -m unittest discover -p TestExamples.py -vs Tests.TestEndToEnd

You can also use tox_ as a test runner. The Webware source package already contains a suitable tox.ini configuration file for running the unit tests with all supported Python versions, and also running a few additional code quality checks. Make sure to use current versions of _tox and _virtualenv when running the tests.

.. _tox: https://tox.readthedocs.io/en/latest/
.. _virtualenv: https://virtualenv.readthedocs.io/en/latest/

Testing Webware applications
----------------------------

We recommend writing tests for your Webware applications as well, using either Python's built-in unittest_ framework, or the excellent pytest_ testing tool.

You should create unit tests for your supporting code (your own library packages in your application working directory), and also end-to-end tests for the servlets that make up your web application (the contexts in your application working directory).

For writing end-to-end tests we recommend using the WebTest_ package. This allows testing your Webware applications end-to-end without the overhead of starting an HTTP server, by making use of the fact that Webware applications are WSGI compliant. Have a look at the existing tests for the built-in contexts in the Tests/TestEndToEnd directory of Webware for Python 3 in order to understand how you can make use of WebTest and structure your tests.

.. _unittest: https://docs.python.org/3/library/unittest.html
.. _pytest: https://docs.pytest.org/en/latest/
.. _WebTest: https://docs.pylonsproject.org/projects/webtest/en/latest/
