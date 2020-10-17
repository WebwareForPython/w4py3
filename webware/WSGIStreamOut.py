"""This module defines a class for writing responses using WSGI."""


class InvalidCommandSequence(ConnectionError):
    """Invalid command sequence error"""


class WSGIStreamOut:
    """This is a response stream to the client using WSGI.

    The key attributes of this class are:

    `_startResponse`:
       The start_response() function that is part of the WSGI protocol.
    `_autoCommit`:
        If True, the stream will automatically start sending data
        once it has accumulated `_bufferSize` data. This means that
        it will ask the response to commit itself, without developer
        interaction. By default, this is set to False.
    `_bufferSize`:
        The size of the data buffer. This is only used when autocommit
        is True. If not using autocommit, the whole response is
        buffered and sent in one shot when the servlet is done.
    `_useWrite`:
        Whether the write callable that is returned by start_response()
        shall be used to deliver the response.
    `flush()`:
        Send the accumulated response data now. Will ask the `Response`
        to commit if it hasn't already done so.
    """

    def __init__(self, startResponse,
                 autoCommit=False, bufferSize=8192,
                 useWrite=True, encoding='utf-8'):
        self._startResponse = startResponse
        self._autoCommit = autoCommit
        self._bufferSize = bufferSize
        self._useWrite = useWrite
        self._encoding = encoding
        self._committed = False
        self._needCommit = False
        self._buffer = b''
        self._chunks = []
        self._chunkLen = 0
        self._closed = False
        self._write = None
        self._iterable = []

    def startResponse(self, status, headers):
        """Start the response with the given status and headers."""
        if self._write or self._committed or self._closed:
            raise InvalidCommandSequence
        try:
            write = self._startResponse(status, headers)
            if self._useWrite:
                if write:
                    self._write = write
                else:
                    self._useWrite = False
                    raise ValueError(
                        'WSGI server does not support write().'
                        ' Try the setting WSGIWrite=False.')
        except Exception as e:
            print("Response Start Error:", e)
            raise ConnectionAbortedError from e

    def autoCommit(self):
        """Get the auto commit mode."""
        return self._autoCommit

    def setAutoCommit(self, autoCommit=True):
        """Set the auto commit mode."""
        self._autoCommit = bool(autoCommit)

    def bufferSize(self):
        """Get the buffer size."""
        return self._bufferSize

    def setBufferSize(self, bufferSize=8192):
        """Set the buffer size."""
        self._bufferSize = int(bufferSize)

    def flush(self):
        """Flush stream."""
        if self._closed:
            raise ConnectionAbortedError
        if not self._committed:
            if self._autoCommit:
                self._needCommit = True
            return
        if self._useWrite:
            if not self._write:
                raise InvalidCommandSequence
            write = self._write
        else:
            write = self._iterable.append
        try:
            self._buffer += b''.join(self._chunks)
        finally:
            self._chunks = []
            self._chunkLen = 0
        sent = 0
        buffer = self._buffer
        resLen = len(buffer)
        bufferSize = self._bufferSize
        while sent < resLen:
            try:
                write(buffer[sent:sent + bufferSize])
            except Exception as e:
                print("StreamOut Error:", e)
                self._closed = True
                raise ConnectionAbortedError from e
            sent += bufferSize
        self.pop(sent)

    def buffer(self):
        """Return accumulated data which has not yet been flushed.

        We want to be able to get at this data without having to call
        flush() first, so that we can (for example) integrate automatic
        HTML validation.
        """
        if self._buffer:  # if flush has been called, return what was flushed
            return self._buffer
        # otherwise return the buffered chunks
        return b''.join(self._chunks)

    def clear(self):
        """Try to clear any accumulated response data.

        Will fail if the response is already committed.
        """
        if self._committed:
            raise InvalidCommandSequence
        self._buffer = b''
        self._chunks = []
        self._chunkLen = 0

    def close(self):
        """Close this buffer. No more data may be sent."""
        self.flush()
        self._closed = True
        self._committed = True
        self._autoCommit = True
        self._write = None

    def closed(self):
        """Check whether we are closed to new data."""
        return self._closed

    def size(self):
        """Return the current size of the data held here."""
        return self._chunkLen + len(self._buffer)

    def prepend(self, output):
        """Add the output to the front of the response buffer.

        The output may be a byte string or a anything that can be converted
        to a string and encoded to a byte string using the output encoding.

        Invalid if we are already committed.
        """
        if self._committed or self._closed:
            raise InvalidCommandSequence
        if not isinstance(output, bytes):
            if not isinstance(output, str):
                output = str(output)
            output = output.encode(self._encoding)
        if self._buffer:
            self._buffer = output + self._buffer
        else:
            self._chunks.insert(0, output)
            self._chunkLen += len(output)

    def pop(self, count):
        """Remove count bytes from the front of the buffer."""
        self._buffer = self._buffer[count:]

    def committed(self):
        """Check whether the outptu is already committed"""
        return self._committed

    def needCommit(self):
        """Request for commitment.

        Called by the `HTTPResponse` instance that is using this instance
        to ask if the response needs to be prepared to be delivered.
        The response should then commit its headers, etc.
        """
        return self._needCommit

    def commit(self, autoCommit=True):
        """Called by the Response to tell us to go.

        If `_autoCommit` is True, then we will be placed into autoCommit mode.
        """
        self._committed = True
        self._autoCommit = autoCommit
        self.flush()

    def iterable(self):
        """Return the WSGI iterable."""
        return self._iterable

    def write(self, output):
        """Write output to the buffer.

        The output may be a byte string or a anything that can be converted
        to a string and encoded to a byte string using the output encoding.
        """
        if self._closed:
            raise ConnectionAbortedError
        if not isinstance(output, bytes):
            if not isinstance(output, str):
                output = str(output)
            output = output.encode(self._encoding)
        self._chunks.append(output)
        self._chunkLen += len(output)
        if self._autoCommit and self._chunkLen > self._bufferSize:
            self.flush()
