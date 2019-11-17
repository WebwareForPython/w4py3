import unittest

from io import BytesIO

from SessionStore import SessionStore

from .Application import Application
from .Session import Session


class TestSessionStore(unittest.TestCase):

    _storeClass = SessionStore

    _app = Application()

    def setUp(self):
        Session._lastExpired = None
        self._store = self._storeClass(self._app)

    def testApplication(self):
        self.assertEqual(self._store.application(), self._app)

    def testEncodeDecode(self):
        session = Session()
        f = BytesIO()
        self._store.encoder()(session, f)
        output = f.getvalue()
        f.close()
        self.assertTrue(isinstance(output, bytes))
        f = BytesIO(output)
        output = self._store.decoder()(f)
        f.close()
        self.assertTrue(type(output) is type(session))
        self.assertEqual(output._data, session._data)

    def testSetEncoderDecoder(self):
        def encoder(obj, f):
            return f.write(repr(obj).encode('ascii'))

        def decoder(f):
            return eval(f.read().decode('ascii'))

        self._store.setEncoderDecoder(encoder, decoder)
        self.assertEqual(self._store.encoder(), encoder)
        self.assertEqual(self._store.decoder(), decoder)
