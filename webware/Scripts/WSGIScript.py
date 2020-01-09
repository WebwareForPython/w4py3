#!/usr/bin/env python3

"""WSGI script to be used with Webware for Python."""

import os
import sys

import webware

libDirs = []
workDir = None
development = None
settings = {}

webware.addToSearchPath()

for libDir in reversed(libDirs):
    if libDir != '.' and libDir not in sys.path:
        sys.path.insert(0, libDir)

if workDir is None:
    workDir = os.path.dirname(os.path.dirname(__file__))

if workDir:
    os.chdir(workDir)

if '.' in libDirs:
    sys.path.insert(0, workDir)

from Application import Application

application = Application(
    workDir, settings=settings, development=development)
