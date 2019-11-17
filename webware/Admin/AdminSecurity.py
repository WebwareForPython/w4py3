from .AdminPage import AdminPage


class AdminSecurity(AdminPage):

    # Set this to False if you want to allow everyone to access secure pages
    # with no login required. This should instead come from a config file.
    _requireLogin = True

    def writeHTML(self):
        session = self.session()
        request = self.request()
        trans = self.transaction()
        app = self.application()
        # Are they logging in?
        if (request.hasField('login')
                and request.hasField('username')
                and request.hasField('password')):
            # They are logging in. Get login id and clear session:
            loginId = session.value('loginId', None)
            session.values().clear()
            # Check if this is a valid user/password
            username = request.field('username')
            password = request.field('password')
            if (self.isValidUserAndPassword(username, password)
                    and request.field('loginId', 'noLogin') == loginId):
                # Success; log them in and send the page:
                session.setValue('authenticated_user_admin', username)
                AdminPage.writeHTML(self)
            else:
                # Failed login attempt; have them try again:
                request.fields()['extra'] = (
                    'Login failed. Please try again.'
                    ' (And make sure cookies are enabled.)')
                app.forward(trans, 'LoginPage')
        # Are they logging out?
        elif request.hasField('logout'):
            # They are logging out. Clear all session variables:
            session.values().clear()
            request.fields()['extra'] = 'You have been logged out.'
            app.forward(trans, 'LoginPage')
        # Are they already logged in?
        elif not self._requireLogin or session.value(
                'authenticated_user_admin', None):
            # They are already logged in; write the HTML for this page:
            AdminPage.writeHTML(self)
        else:
            # They need to log in.
            app.forward(trans, 'LoginPage')

    def isValidUserAndPassword(self, username, password):
        # Replace this with a database lookup, or whatever you're using
        # for authentication...
        adminPassword = self.application().setting('AdminPassword')
        return (username == 'admin' and adminPassword and
                password == adminPassword)
