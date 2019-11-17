#!/usr/bin/env python3

"""The Webware command line interface"""

import argparse

from .MakeAppWorkDir import addArguments as addMakeArguments, make
from .WaitressServer import addArguments as addServeArguments, serve
from ..Properties import version as versionTuple
from ..MiscUtils.PropertiesObject import versionString


def main(args=None):
    """Evaluate the command line arguments and execute subcommand."""
    version = versionString(versionTuple)
    parser = argparse.ArgumentParser(description="Webware CLI")
    parser.add_argument('-v', '--version', action='version',
                        version=f'Webware for Python {version}')
    subparsers = parser.add_subparsers(
        dest='command', title="Webware subcommands",
        help="name of the subcommand")
    serveParser = subparsers.add_parser(
        'serve', help="Serve a Webware application using waitress")
    addServeArguments(serveParser)
    makeParser = subparsers.add_parser(
        'make', help="Make a Webware application working directory")
    addMakeArguments(makeParser)
    args = parser.parse_args(args)
    command = args.command
    del args.command
    if command == 'make':
        make(args)
    elif command == 'serve':
        serve(args)


if __name__ == '__main__':
    main()
