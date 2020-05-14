#
# Ajax "Suggest" Example
#
# Written by Robert Forkel based on
# https://webwareforpython.github.io/w4py-olde-wiki/ajaxinwebware.html
# and http://www.dynamicajax.com/fr/AJAX_Suggest_Tutorial-271_290_312.html,
# with minor changes made by Christoph Zwerschke.
#

from random import randint

from .AjaxPage import AjaxPage

maxSuggestions = 10

# Create some random "magic words":
maxLetters, maxWords = 5, 5000
magicWords = [''.join(chr(randint(97, 122)) for j in range(maxLetters))
              for i in range(maxWords)]


class AjaxSuggest(AjaxPage):

    _clientPolling = None  # we have no long-running queries

    def writeJavaScript(self):
        AjaxPage.writeJavaScript(self)
        self.writeln(
            '<script src="ajaxsuggest.js"></script>')

    def writeStyleSheet(self):
        AjaxPage.writeStyleSheet(self)
        self.writeln(
            '<link rel="stylesheet" href="ajaxsuggest.css">')

    def htBodyArgs(self):
        return AjaxPage.htBodyArgs(self) + ' onload="initPage();"'

    def writeContent(self):
        self.writeln('<h2>Ajax "Suggest" Example</h2>')
        if self.request().hasField('query'):
            query = self.htmlEncode(self.request().field('query'))
            self.writeln(f'''
<p>You have just entered the word <b class="in_red">"{query}"</b>.</p>
<p>If you like, you can try again:</p>''')
        else:
            self.writeln('''
<p>This example uses Ajax techniques to make suggestions
based on your input as you type.</p>
<p>Of course, you need a modern web browser with
JavaScript enabled in order for this to work.</p>
<p>Start typing in some lowercase letters,
and get random words starting with these characters suggested:</p>''')
        self.writeln('''<form><div>
<input type="text" name="query" id="query"
 onkeyup="getSuggestions();" autocomplete="off">
<input type="submit" value="Submit"></div><div class="hide" id="suggestions">
</div></form>''')

    def exposedMethods(self):
        """Register the suggest method for use with Ajax."""
        return ['suggest']

    def suggest(self, prefix):
        """We return a JavaScript function call as string.

        The JavaScript function we want called is `handleSuggestions`
        and we pass an array of strings starting with prefix.

        Note: to pass more general Python objects to the client side,
        use Python's JSON encoder.
        """
        words = [w for w in magicWords if w.startswith(prefix)] or ['none']
        wordList = ",".join(map(repr, words[:maxSuggestions]))
        return f"handleSuggestions([{wordList}]);"
