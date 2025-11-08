#!.venv/bin/python3

"""Run all unit tests for Webware for Python 3.

Essentially equivalent to the following commands:

    cd webware
    python -m unittest discover -fv -p "Test*.py"

Output is sent to stdout instead of stderr,
so that not all appears in red color when using tox.
"""

import sys
import os
import unittest


def main():
    """Run all unit tests for Webware for Python 3."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    webware_path = os.path.join(root_dir, "webware")
    if webware_path not in sys.path:
        sys.path.insert(0, webware_path)

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir='webware',
        pattern='Test*.py'
    )
    runner = unittest.TextTestRunner(
        stream=sys.stdout,
        verbosity=2
    )
    result = runner.run(suite)

    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
