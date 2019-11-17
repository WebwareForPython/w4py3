from .SecurePage import SecurePage


class SecureCountVisits(SecurePage):
    """Secured version of counting visits example."""

    def writeContent(self):
        count = self.session().value('secure_count', 0) + 1
        self.session().setValue('secure_count', count)
        self.writeln('<h3>Counting Visits on a Secured Page</h3>')
        if self.request().isSessionExpired():
            self.writeln('<p>Your session has expired.</p>')
        self.writeln(
            "<p>You've been here"
            ' <strong style="background-color:yellow">'
            f'&nbsp;{count:d}&nbsp;</strong>'
            f" time{'' if count == 1 else 's'}.</p>")
        reload = '<a href="javascript:location.reload()">reload</a>'
        revisit = '<a href="SecureCountVisits">revisit</a>'
        self.writeln(
            '<p>This page records your visits using a session object.'
            f' Every time you {reload} or {revisit} this page,'
            ' the counter will increase. If you close your browser,'
            ' then your session will end and you will see the counter'
            ' go back to 1 on your next visit.</p>')
        self.writeln(f'<p>Try hitting {reload} now.</p>')
        user = self.loggedInUser()
        if user:
            self.writeln(
                f'<p>Authenticated user is <strong>{user}</strong>.</p>')
        revisit = '<a href="SecureCountVisits">Revisit this page</a>'
        logout = '<a href="SecureCountVisits?logout=1">Logout</a>'
        self.writeln(f'<p>{revisit} | {logout}</p>')
