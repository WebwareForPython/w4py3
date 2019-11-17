from .ExamplePage import ExamplePage


class CustomError(Exception):
    pass


class Error(ExamplePage):

    def title(self):
        return 'Error raising Example'

    def writeContent(self):
        error = self.request().field('error', None)
        if error:
            msg = 'You clicked that button!'
            if error.startswith('String'):
                error = msg
            elif error.startswith('Custom'):
                error = CustomError(msg)
            elif error.startswith('System'):
                error = SystemError(msg)
            else:
                error = RuntimeError(msg)
            self.writeln('<p>About to raise an error...</p>')
            raise error
        self.writeln('''<h1>Error Test</h1>
<form action="Error" method="post">
<p><select name="error" size="1">
<option selected>Runtime Error</option>
<option>System Error</option>
<option>Custom Error</option>
</select>
<input type="submit" value="Don't click this button!"></p>
</form>''')
