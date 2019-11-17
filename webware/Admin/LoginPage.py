from MiscUtils.Funcs import uniqueId

from .AdminPage import AdminPage


class LoginPage(AdminPage):
    """The log-in screen for the admin pages."""

    def writeContent(self):
        if self.loginDisabled():
            self.write(self.loginDisabled())
            return
        self.writeln(
            '<div style="margin-left:auto;margin-right:auto;width:20em">'
            '<p>&nbsp;</p>')
        extra = self.request().field('extra', None)
        if extra:
            self.writeln(f'<p style="color:#339">{self.htmlEncode(extra)}</p>')
        self.writeln('''<p>Please log in to view Administration Pages.
The username is <code>admin</code>. The password can be set in the
<code>Application.config</code> file in the <code>Configs</code> directory.</p>
<form method="post">
<table style="background-color:#cce;border:1px solid #33c;width:20em">
<tr><td style="text-align:right"><label for="username">Username:</label></td>
<td><input type="text" id="username" name="username" value="admin"></td></tr>
<tr><td style="text-align:right"><label for="password">Password:</label></td>
<td><input type="password" id="password" name="password" value=""></td></tr>
<tr><td colspan="2" style="text-align:right">
<input type="submit" name="login" value="Login"></td></tr>
</table>''')
        enc = self.htmlEncode
        for name, value in self.request().fields().items():
            if name not in ('login', 'logout', 'loginId',
                            'username', 'password', 'extra'):
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    self.writeln(f'<input type="hidden"'
                                 f' name="{enc(name)}" value="{enc(v)}">')
        if self.session().hasValue('loginId'):
            loginId = self.session().value('loginId')
        else:
            # Create a "unique" login id and put it in the form as well as
            # in the session. Login will only be allowed if they match.
            loginId = uniqueId(self)
            self.session().setValue('loginId', loginId)
        self.writeln(f'<input type="hidden" name="loginId" value="{loginId}">')
        self.writeln('</form>\n<p>&nbsp;</p></div>')
