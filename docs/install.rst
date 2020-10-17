.. _installation:

Installation
============


Python Version
--------------

Webware for Python 3 requires at least Python version 3.6.


Create a Virtual Environment
----------------------------

Though you can install Webware for Python 3 into your global Python environment, we recommend creating a separate virtual environment for every Webware for Python 3 project.

To create such a virtual environment in the ``.venv`` subdirectory of the current directory, run the following command::

    python3 -m venv .venv

If you are using Windows, may may need to run the following instead::

    py -3 -m venv .venv


Activate the Virtual Environment
--------------------------------

To activate the virtual environment, you need to execute the "activate" command of the virtual environment like this::

    . .venv/bin/activate

Or, if your are using Windows, the "activate" command can be executed like this::

    .venv\Scripts\activate


Installation with Pip
----------------------

With the virtual environment activated, you can now download and install Webware for Python 3 in one step using the following command::

    pip install "Webware-for-Python>=3"

For developing with Webware for Python, you will probably also install "extras" as explained below.


Installing "Extras"
-------------------

When installing Webware for Python 3, the following "extras" can optionally be installed as well:

* "dev": extras for developing Webware applications
* "examples": extras for running all Webware examples
* "test": extras needed to test all functions of Webware

On your development machine, we recommend installing the full "test" environment which also includes the other two environments. To do that, you need to specify the "Extras" name in square brackets when installing Webware for Python 3::

    pip install "Webware-for-Python[tests]>=3"


Installation from Source
------------------------

Alternatively, you can also download_ Webware for Python 3 from PyPI, and run the ``setup.py`` command in the tar.gz archive like this::

    setup.py install

You will then have to also install the "extra" requirements manually, though. Have a look at the setup.py file to see the list of required packages.

.. _download: https://pypi.org/project/Webware-for-Python/


Check the Installed Version
---------------------------

In order to check that Webware has been installed properly, run the command line tool ``webware`` with the ``--version`` option::

    webware --version

This should show the version of Webware for Python 3 that you have installed. Keep in mind that the virtual environment into which you installed Webware for Python 3 needs to be activated before you run the "webware" command.
