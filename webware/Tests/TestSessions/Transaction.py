""""Mock Webware Transaction class."""

from .Application import Application


class Transaction:

    def __init__(self):
        self._application = Application()

    def application(self):
        return self._application
