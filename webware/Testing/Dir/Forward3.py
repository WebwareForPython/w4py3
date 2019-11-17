from HTTPServlet import HTTPServlet


class Forward3(HTTPServlet):

    def respond(self, transaction):
        transaction.application().forward(
            transaction,
            '../Forward3Target' + transaction.request().extraURLPath())
