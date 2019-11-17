#!/usr/bin/env python3

"""Helper script for the feature provided by the IncludeEditLink setting."""

import os
import sys
from email import message_from_file
from subprocess import run

editor = 'Vim'  # your favorite editor

defaultArgs = [editor, ' +{line}', '{filename}']

# add an entry for your favorite editor here if it does not already exist
editorArgs = {
    'Emacs':
        ['gnuclient', '+{line}',  '{filename}'],
    'Geany':
        ['geany',  '-l', '{line}', '{filename}'],
    'Geany (Windows)':
        ['C:/Program Files (x86)/Geany/bin/geany.exe',
         '-l', '{line}', '{filename}'],
    'gedit':
        ['gedit', '+{line}', '{filename}'],
    'jEdit':
        ['jedit', '{filename}', '+line:{line}'],
    'jEdit (Windows)':
        ['C:/Program Files/jEdit/jedit.exe', '{filename}', '+line:{line}'],
    'Kate':
        ['kate', '-u', '-l', '{line}', '{filename}'],
    'Komodo':
        ['komodo', '-l', '{line}', '{filename}'],
    'KWrite':
        ['kwrite', '--line', '{line}', '{filename}'],
    'Notepad++ (Windows)':
        ['C:/Program Files/Notepad++/notepad++.exe', '-n{line}', '{filename}'],
    'PSPad (Windows)':
        ['C:/Program Files (x86)/PSPad editor/PSPad.exe',
         '-{line}', '{filename}'],
    'SciTE':
        ['scite', '{filename}', '-goto:{line}'],
    'SciTE (Windows)':
        ['C:/wscite/SciTE.exe', '{filename}', '-goto:{line}'],
    'Sublime Text (Windows)':
        ['C:/Program Files/Sublime Text 3/subl.exe', '{filename}:{line}'],
    'Vim':
        ['gvim', '+{line}', '{filename}'],
}


def transform(params):
    """Transform EditFile parameters.

    As an example, if you are under Windows and your edit file
    has a Unix filename, then it is transformed to a UNC path.
    """
    filename = params['filename']
    if os.sep == '\\' and filename.startswith('/'):
        filename = os.path.normpath(filename[1:])
        hostname = params['hostname'].split(':', 1)[0]
        smbPath = fr'\\{hostname}\root'
        filename = os.path.join(smbPath, filename)
        params['filename'] = filename
    return params


def openFile(params):
    """Open editor with file specified in parameters."""
    params = {key.lower(): value for key, value in params.items()}
    params = transform(params)
    args = editorArgs.get(editor, defaultArgs)
    args[1:] = [arg.format(**params) for arg in args[1:]]
    print(' '.join(args))
    run(args)


def parseFile(filename):
    """Parse the Webware EditFile."""
    openFile(message_from_file(open(filename)))


if __name__ == '__main__':
    parseFile(sys.argv[1])
