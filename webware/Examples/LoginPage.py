from MiscUtils.Funcs import uniqueId
from .ExamplePage import ExamplePage


class LoginPage(ExamplePage):
    """A log-in screen for the example pages."""

    def title(self):
        return 'Log In'

    def htBodyArgs(self):
        return super().htBodyArgs() + (
            ' onload="document.loginForm.username.focus();"')

    def writeContent(self):
        self.writeln(
            '<div style="margin-left:auto;margin-right:auto;width:20em">'
            '<p>&nbsp;</p>')
        request = self.request()
        extra = request.field('extra', None)
        if (not extra and request.isSessionExpired()
                and not request.hasField('logout')):
            extra = 'You have been automatically logged out due to inactivity.'
        if extra:
            self.writeln(
                f'<p style="color:#339">{self.htmlEncode(extra)}</p>')
        if self.session().hasValue('loginId'):
            loginId = self.session().value('loginId')
        else:
            # Create a "unique" login id and put it in the form as well as
            # in the session. Login will only be allowed if they match.
            loginId = uniqueId(self)
            self.session().setValue('loginId', loginId)
        action = request.field('action', '')
        if action:
            action = f' action="{action}"'
        self.writeln(f'''<p>Please log in to view the example.
The username and password is <kbd>alice</kbd> or <kbd>bob</kbd>.</p>
<form method="post" id="loginForm"{action}>
<table style="background-color:#cce;border:1px solid #33c;width:20em">
<tr><td style="text-align:right"><label for="username">Username:</label></td>
<td><input type="text" id="username" name="username" value="admin"></td></tr>
<tr><td style="text-align:right"><label for="password">Password:</label></td>
<td><input type="password" id="password" name="password" value=""></td></tr>
<tr><td colspan="2" style="text-align:right">
<input type="submit" name="login" value="Login"></td></tr>
</table>
<input type="hidden" name="loginId" value="{loginId}">''')
        # Forward any passed in values to the user's intended page
        # after successful login, except for the special values
        # used by the login mechanism itself:
        enc = self.htmlEncode
        for name, value in request.fields().items():
            if name not in ('login', 'logout', 'loginId',
                            'username', 'password', 'extra'):
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    self.writeln('<input type="hidden"'
                                 f' name="{enc(name)}" value="{enc(v)}">')
        self.writeln('</form>\n<p>&nbsp;</p></div>')
