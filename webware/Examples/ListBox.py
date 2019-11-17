from .ExamplePage import ExamplePage

debug = False


class ListBox(ExamplePage):
    """List box example.

    This page provides a list box interface with controls
    for changing its size and adding and removing items.

    The source is a good example of how to use awake() and actions.

    It also shows how to avoid repeated execution on refresh/reload.
    """

    def awake(self, transaction):
        ExamplePage.awake(self, transaction)
        session = self.session()
        if session.hasValue('vars'):
            self._vars = session.value('vars')
        else:
            self._vars = dict(
                items=[], height=10, width=250,
                newCount=1, formCount=1)
            session.setValue('vars', self._vars)
        self._error = None

    def writeContent(self):
        enc, wr = self.htmlEncode, self.writeln
        wr('<div style="text-align:center">')
        if debug:
            wr('<p>fields = {}</p>'.format(enc(str(self.request().fields()))))
            wr('<p>vars = {}</p>'.format(enc(str(self._vars))))
        # Intro text is provided by our class' doc string:
        intro = self.__class__.__doc__.strip().split('\n\n')
        wr('<h2>{}</h2>'.format(intro.pop(0)))
        for s in intro:
            wr('<p>{}</p>'.format('<br>'.join(
                s.strip() for s in s.splitlines())))
        wr('<p style="color:red">{}</p>'.format(self._error or '&nbsp;'))
        wr('''
<form action="ListBox" method="post">
<input name="formCount" type="hidden" value="{formCount}">
<select multiple name="items" size="{height}"
style="width:{width}pt;text-align:center">
'''.format(**self._vars))
        index = 0
        for item in self._vars['items']:
            wr('<option value="{}">{}</option>'.format(
                index, enc(item['name'])))
            index += 1
        if not index:
            wr('<option value="" disabled>--- empty ---</option>')
        wr('''
</select>
<p>
<input name="_action_new" type="submit" value="New">
<input name="_action_delete" type="submit" value="Delete">
&nbsp; &nbsp; &nbsp;
<input name="_action_taller" type="submit" value="Taller">
<input name="_action_shorter" type="submit" value="Shorter">
&nbsp; &nbsp; &nbsp;
<input name="_action_wider" type="submit" value="Wider">
<input name="_action_narrower" type="submit" value="Narrower">
</p>
</form>
</div>
''')

    @staticmethod
    def heightChange():
        return 1

    @staticmethod
    def widthChange():
        return 30

    # Commands

    def new(self):
        """Add a new item to the list box."""
        self._vars['items'].append(dict(
            name='New item {}'.format(self._vars['newCount'])))
        self._vars['newCount'] += 1
        self.writeBody()

    def delete(self):
        """Delete the selected items in the list box."""
        req = self.request()
        if req.hasField('items'):
            indices = req.field('items')
            if not isinstance(indices, list):
                indices = [indices]
            try:
                indices = list(map(int, indices))  # convert strings to ints
            except ValueError:
                indices = []
            # remove the objects:
            for index in sorted(indices, reverse=True):
                del self._vars['items'][index]
        else:
            self._error = 'You must select a row to delete.'
        self.writeBody()

    def taller(self):
        self._vars['height'] += self.heightChange()
        self.writeBody()

    def shorter(self):
        if self._vars['height'] > 2:
            self._vars['height'] -= self.heightChange()
        self.writeBody()

    def wider(self):
        self._vars['width'] += self.widthChange()
        self.writeBody()

    def narrower(self):
        if self._vars['width'] >= 60:
            self._vars['width'] -= self.widthChange()
        self.writeBody()

    # Actions

    def actions(self):
        acts = ExamplePage.actions(self)
        # check whether form is valid (no repeated execution)
        try:
            formCount = int(self.request().field('formCount'))
        except (KeyError, ValueError):
            formCount = 0
        if formCount == self._vars['formCount']:
            acts.extend([
                'new', 'delete', 'taller', 'shorter', 'wider', 'narrower'])
            self._vars['formCount'] += 1
        return acts
