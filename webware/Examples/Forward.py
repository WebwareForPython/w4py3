from .ExamplePage import ExamplePage


class Forward(ExamplePage):

    def writeContent(self):
        trans = self.transaction()
        resp = self.response()
        resp.write(
            "<p>This is the <em>Forward</em> servlet speaking. I am now"
            " going to include the output of the <em>IncludeMe</em> servlet"
            " via Application's <code>includeURL()</code> method:</p>")
        trans.application().includeURL(trans, 'IncludeMe')
