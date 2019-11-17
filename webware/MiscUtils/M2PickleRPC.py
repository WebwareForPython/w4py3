"""M2Crypto-enhanced transport for PickleRPC

This lets you use M2Crypto for SSL encryption.

Based on m2xmlrpclib.py which is
Copyright (c) 1999-2002 Ng Pheng Siong. All rights reserved.
"""

from io import BytesIO

from M2Crypto import SSL, httpslib, m2urllib  # pylint: disable=import-error

from .PickleRPC import Transport

__version__ = 1  # version of M2PickleRPC


class M2Transport(Transport):

    user_agent = f"M2PickleRPC.py/{__version__} - {Transport.user_agent}"

    def __init__(self, ssl_context=None):
        if ssl_context is None:
            self.ssl_ctx = SSL.Context('sslv23')
        else:
            self.ssl_ctx = ssl_context

    def make_connection(self, host, port=None):
        if port is None:
            host, port = m2urllib.splitport(host)
        return httpslib.HTTPS(host, int(port), ssl_context=self.ssl_ctx)

    # Workarounds below are necessary because M2Crypto seems to
    # return from fileobject.read() early!  So we have to call it
    # over and over to get the full data.

    def parse_response(self, f):
        """Workaround M2Crypto issue mentioned above."""
        sio = BytesIO()
        while True:
            chunk = f.read()
            if not chunk:
                break
            sio.write(chunk)
        sio.seek(0)
        return Transport.parse_response(self, sio)

    def parse_response_gzip(self, f):
        """Workaround M2Crypto issue mentioned above."""
        sio = BytesIO()
        while True:
            chunk = f.read()
            if not chunk:
                break
            sio.write(chunk)
        sio.seek(0)
        return Transport.parse_response_gzip(self, sio)
