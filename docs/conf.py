# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../webware'))

# import some requirements as dummy modules
# in order to avoid import errors when auto generating reference docs
from Tests.TestSessions import redis, memcache


# -- Project information -----------------------------------------------------

project = 'Webware for Python 3'
copyright = '1999-2021, Christoph Zwerschke et al'
author = 'Christoph Zwerschke et al.'

# The short X.Y version
version = '3.0'
# The full version, including alpha/beta/rc tags
release = '3.0.2'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# AutoDoc configuration
autoclass_content = "class"
autodoc_default_options = {
    'members': True,
    'inherited-members': True,
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True
}
autosummary_generate = True

# ignore certain warnings
# (references to some of the Python built-in types do not resolve correctly)
nitpicky = True
nitpick_ignore = [('py:class', t) for t in (
    'cgi.FieldStorage', 'html.parser.HTMLParser',
    'threading.Thread', 'xmlrpc.client.ProtocolError')]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']
html_static_path = ['css']
