from HTTPServlet import HTTPServlet


class Forward1(HTTPServlet):

    def respond(self, transaction):
        transaction.application().forward(
            transaction,
            'Forward1Target' + transaction.request().extraURLPath())
