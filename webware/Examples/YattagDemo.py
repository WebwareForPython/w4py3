try:
    from yattag import Doc
except ImportError:
    Doc = None

from .ExamplePage import ExamplePage


class YattagDemo(ExamplePage):
    """Demo for using the Yattag library."""

    defaults = {
        'subject': 'Just testing',
        'message': 'You just won the lottery!'
    }

    spamWords = 'earn free income lottery money offer price'.split()

    def isSpam(self, text):
        text = text.lower()
        for word in self.spamWords:
            if word in text:
                return True
        return False

    def writeContent(self):
        self.writeln('<h1>Using Webware with Yattag</h1>')
        self.writeln(
            '<p>Yattag is a Python library that can be used in Webware'
            ' applications to generate HTML programmatically.</p>')
        if Doc:
            self.writeln(self.demoForm())
        else:
            self.writeln(
                '<p>Please <a href="https://www.yattag.org/download-install">'
                ' install yattag</a> in order to view this demo.</p>')

    def demoForm(self):
        defaults = self.defaults.copy()
        errors = {}
        request = self.request()
        if request.hasField('message'):
            subject = self.request().field('subject')
            defaults['subject'] = subject
            if not subject:
                errors['subject'] = 'Please add the subject of your message.'
            elif self.isSpam(subject):
                errors['subject'] = 'Your subject looks like spam!'
            message = self.request().field('message')
            defaults['message'] = message
            if not message:
                errors['message'] = 'You did not enter a message!'
            elif self.isSpam(message):
                errors['message'] = 'Your message looks like spam!'
        else:
            subject = message = None

        doc, tag, text = Doc(defaults=defaults, errors=errors).tagtext()

        if message and not errors:

            with tag('p', klass='success'):
                text('Congratulations! You have sent the following message:')
            with tag('div', klass='output'):
                with tag('p'):
                    with tag('strong'):
                        text(subject)
                with tag('p'):
                    text(message)
            with tag('a', href='YattagDemo'):
                text('Try sending another message.')

        else:

            with tag('h2'):
                text('Demo contact form')

            with tag('form', action="YattagDemo"):
                doc.input(name='subject', type='text', size=80)
                with doc.textarea(
                        name='message', cols=80, rows=8):
                    pass
                doc.stag('input', type='submit', value='Send my message')

        return doc.getvalue()

    def writeStyleSheet(self):
        super().writeStyleSheet()
        if Doc:
            style = """
#Content form input, #Content form textarea {
    display: block; margin: 1em 0; padding: 2pt;
}
#Content form input.error, #Content form textarea.error {
    border: 1px solid red !important;
    box-shadow: 0 0 3px red important;
}
#Content form span.error {
    color: red;
}
#Content p.success {
    color: green;
}
#Content .output {
margin: 2em;
padding: 0.5em 1em;
border: 1px solid #cce;
}
            """
            doc, tag, text = Doc().tagtext()
            with tag('style'):
                text(style)

            self.writeln(doc.getvalue())
