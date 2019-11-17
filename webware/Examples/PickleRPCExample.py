from operator import truediv
from functools import reduce

from PickleRPCServlet import PickleRPCServlet


class PickleRPCExample(PickleRPCServlet):
    """Example XML-RPC servlet.

    To try it out, use something like the following:

    >>> from MiscUtils.PickleRPC import Server
    >>> server = Server('http://localhost:8080/Examples/PickleRPCExample')
    >>> server.multiply(10,20)
    200
    >>> server.add(10,20)
    30

    You'll get an exception if you try to call divide, because that
    method is not listed in exposedMethods.
    """

    def exposedMethods(self):
        return ['multiply', 'add']

    def multiply(self, x, y):
        return x * y

    def add(self, x, y):
        return x + y

    def divide(self, *args):
        return reduce(truediv, args)
