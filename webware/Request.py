"""An abstract request"""

from MiscUtils import AbstractError
from MiscUtils.Funcs import asclocaltime


class Request:
    """The abstract request class.

    Request is a base class that offers the following:

      * A time stamp (indicating when the request was made)
      * An input stream
      * Remote request information (address, name)
      * Local host information (address, name, port)
      * A security indicator

    Request is an abstract class; developers typically use HTTPRequest.
    """

    # region Init

    def __init__(self):
        """Initialize the request.

        Subclasses are responsible for invoking super
        and initializing self._time.
        """
        self._transaction = None

    # endregion Init

    # region Access

    def time(self):
        return self._time  # pylint: disable=no-member

    def timeStamp(self):
        """Return time() as human readable string for logging and debugging."""
        return asclocaltime(self.time())

    # endregion Access

    # region Input

    def input(self):
        """Return a file-style object that the contents can be read from."""
        # This is bogus. Disregard for now.

    # endregion Input

    # region Remote info

    def remoteAddress(self):
        """Get the remote address.

        Returns a string containing the Internet Protocol (IP) address
        of the client that sent the request.
        """
        raise AbstractError(self.__class__)

    def remoteName(self):
        """Get the remote name.

        Returns the fully qualified name of the client that sent the request,
        or the IP address of the client if the name cannot be determined.
        """
        raise AbstractError(self.__class__)

    # endregion Remote info

    # region Local info

    def localAddress(self):
        """Get local address.

        Returns a string containing the Internet Protocol (IP) address
        of the local host (e.g., the server) that received the request.
        """
        raise AbstractError(self.__class__)

    @staticmethod
    def localName():
        """Get local name.

        Returns the fully qualified name of the local host (e.g., the server)
        that received the request.
        """
        return 'localhost'

    def localPort(self):
        """Get local port.

        Returns the port of the local host (e.g., the server)
        that received the request.
        """
        raise AbstractError(self.__class__)

    # endregion Local info

    # region Security

    @staticmethod
    def isSecure():
        """Check whether this is a secure channel.

        Returns true if request was made using a secure channel,
        such as HTTPS. This currently always returns false,
        since secure channels are not yet supported.
        """
        return False

    # endregion Security

    # region Transactions

    def responseClass(self):
        """Get the corresponding response class."""
        raise AbstractError(self.__class__)

    def setTransaction(self, trans):
        """Set a transaction container."""
        self._transaction = trans

    def transaction(self):
        """Get the transaction container."""
        return self._transaction

    # endregion Transactions

    # region Cleanup

    def clearTransaction(self):
        del self._transaction

    # endregion Cleanup

    # region Exception reports

    _exceptionReportAttrNames = []

    def writeExceptionReport(self, handler):
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self._exceptionReportAttrNames)

    # endregion Exception reports
