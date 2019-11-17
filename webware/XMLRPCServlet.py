"""XML-RPC servlet base class

Written by Geoffrey Talvola

See Examples/XMLRPCExample.py for sample usage.
"""

import sys
import traceback
import xmlrpc.client

from RPCServlet import RPCServlet


class XMLRPCServlet(RPCServlet):
    """XMLRPCServlet is a base class for XML-RPC servlets.

    See Examples/XMLRPCExample.py for sample usage.

    For more Pythonic convenience at the cost of language independence,
    see PickleRPCServlet.
    """

    # Set to False if you do not want to allow None to be marshalled
    # as part of a response.
    allow_none = True

    def respondToPost(self, transaction):
        """Respond to a Post request.

        This is similar to the xmlrpcserver.py example from the xmlrpc
        library distribution, only it's been adapted to work within a
        Webware servlet.
        """
        try:
            # get arguments
            data = transaction.request().rawInput(rewind=1).read()
            encoding = _getXmlDeclAttr(data, "encoding")
            params, method = xmlrpc.client.loads(data)

            # generate response
            try:
                # This first test helps us to support PythonWin, which uses
                # repeated calls to __methods__.__getitem__ to determine the
                # allowed methods of an object.
                if method == '__methods__.__getitem__':
                    response = self.exposedMethods()[params[0]]
                else:
                    response = self.call(method, *params)
                if not isinstance(response, tuple):
                    response = (response,)
            except xmlrpc.client.Fault as fault:
                response = xmlrpc.client.dumps(
                    fault, encoding=encoding, allow_none=self.allow_none)
                self.sendOK('text/xml', response, transaction)
                self.handleException(transaction)
            except Exception as e:
                fault = self.resultForException(e, transaction)
                response = xmlrpc.client.dumps(
                    xmlrpc.client.Fault(1, fault),
                    encoding=encoding, allow_none=self.allow_none)
                self.sendOK('text/xml', response, transaction)
                self.handleException(transaction)
            else:
                response = xmlrpc.client.dumps(
                    response, methodresponse=1,
                    encoding=encoding, allow_none=self.allow_none)
                self.sendOK('text/xml', response, transaction)
        except Exception:
            # internal error, report as HTTP server error
            print('XMLRPCServlet internal error')
            print(''.join(traceback.format_exception(
                sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
            transaction.response().setStatus(500, 'Server Error')
            self.handleException(transaction)


# Helper functions:

def _getXmlDeclAttr(xml, attName):
    """Get attribute value from xml declaration (<?xml ... ?>)."""
    s = xml[6:xml.find("?>")]  # 'version = "1.0" encoding = "Cp1251"'
    p = s.find(attName)
    if p < 0:
        return None
    s = s[p + len(attName):]  # '= "Cp1251"'
    s = s[s.find('=') + 1:].strip()  # '"Cp1251"'
    return s[1:s.find(s[0], 1)]  # 'Cp1251'
