from HTTPServlet import HTTPServlet


class Forward2(HTTPServlet):

    def respond(self, transaction):
        transaction.application().forward(
            transaction,
            'Dir/Forward2Target' + transaction.request().extraURLPath())
