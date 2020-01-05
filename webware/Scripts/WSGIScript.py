#!/usr/bin/env python3

"""WSGI script to be used with Webware for Python."""

import os
import sys

libDirs = []
workDir = None
development = None
settings = {}

for libDir in libDirs:
    if libDir not in sys.path:
        sys.path.append(libDir)

if workDir is None:
    workDir = os.path.dirname(os.path.dirname(__file__))

if workDir:
    os.chdir(workDir)

import webware
webware.addToSearchPath()

from Application import Application

application = Application(
    workDir, settings=settings, development=development)
