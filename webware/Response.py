"""An abstract response"""

from time import time

from MiscUtils import AbstractError


class Response:
    """The abstract response class.

    Response is a base class that offers the following:

      * A time stamp (indicating when the response was finished)
      * An output stream

    Response is an abstract class; developers typically use HTTPResponse.
    """

    # region Init

    def __init__(self, trans, strmOut):
        self._strmOut = strmOut
        self._transaction = trans

    # endregion Init

    # region End time

    def endTime(self):
        return self._endTime

    def recordEndTime(self):
        """Record the end time of the response.

        Stores the current time as the end time of the response. This should
        be invoked at the end of deliver(). It may also be invoked by the
        application for those responses that never deliver due to an error.
        """
        self._endTime = time()

    # endregion End time

    # region Output

    def write(self, output):
        raise AbstractError(self.__class__)

    def isCommitted(self):
        raise AbstractError(self.__class__)

    def deliver(self):
        raise AbstractError(self.__class__)

    def reset(self):
        raise AbstractError(self.__class__)

    def streamOut(self):
        return self._strmOut

    # endregion Output

    # region Cleanup

    def clearTransaction(self):
        del self._transaction

    # endregion Cleanup

    # region Exception reports

    _exceptionReportAttrNames = ['endTime']

    def writeExceptionReport(self, handler):
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self._exceptionReportAttrNames)

    # endregion Exception reports
