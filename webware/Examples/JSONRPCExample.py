#
# JSON-RPC example servlet contributed by Jean-Francois Pieronne
#

from JSONRPCServlet import JSONRPCServlet


class JSONRPCExample(JSONRPCServlet):
    """Example JSON-RPC servlet.

    To try it out, use the JSONRPCClient servlet.
    """

    def __init__(self):
        JSONRPCServlet.__init__(self)

    @staticmethod
    def echo(msg):
        return msg

    @staticmethod
    def reverse(msg):
        return msg[::-1]

    @staticmethod
    def uppercase(msg):
        return msg.upper()

    @staticmethod
    def lowercase(msg):
        return msg.lower()

    @staticmethod
    def exposedMethods():
        return ['echo', 'reverse', 'uppercase', 'lowercase']
