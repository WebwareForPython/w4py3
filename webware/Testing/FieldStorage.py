
from SidebarPage import SidebarPage


class FieldStorage(SidebarPage):
    """Test the FieldStorage class.

    Webware uses a modified FieldStorage class that parses GET parameters
    even in a POST request. However, the parameter names must be different.
    A GET parameters with the same name as a POST parameter is ignored,
    these values are not appended. In other words, POST parameters always
    override GET parameters with the same name.
    """

    def cornerTitle(self):
        return 'Testing'

    def writeContent(self):
        request = self.request()
        method = request.method()
        fields = request.fields()
        wr = self.writeln
        if method == 'GET' and not fields:
            getFields = [
                ('getfield1', 'getvalue1'),
                ('getfield2', 'getvalue21'), ('getfield2', 'getvalue22'),
                ('dualfield1', 'getdual1'),
                ('dualfield2', 'getdual21'), ('dualfield2', 'getdual22'),
                ('getempty', '')
            ]
            postFields = [
                ('postfield1', 'postvalue1'),
                ('postfield2', 'postvalue21'), ('postfield2', 'postvalue22'),
                ('dualfield1', 'postdual1'),
                ('dualfield2', 'postdual21'), ('dualfield2', 'postdual22'),
                ('postempty', '')
            ]
            wr('<p>The Webware FieldStorage class can be tested here.</p>')
            wr('<form action="FieldStorage?{}" method="POST">'.format(
                '&amp;'.join('{}={}'.format(*field) for field in getFields)))
            wr('<p>Please press the button to run the test:')
            for field in postFields:
                wr('<input type="hidden" name="{}" value="{}">'.format(*field))
            wr('<input type="submit" name="testbutton" value="Submit">')
            wr('</p></form>')
        else:
            errors = []
            error = errors.append
            if method != 'POST':
                error(f'The method is {method} instead of POST')
            if len(fields) != 9:
                error(f'We got {len(fields)} instead of 9 fields')
            if not request.hasField('testbutton'):
                error('We did not get the submit button')
            elif request.field('testbutton') != 'Submit':
                error('The submit button field got a wrong value')
            if not request.hasField('getempty'):
                error('We did not get the empty GET parameter')
            elif request.field('getempty') != '':
                error('The empty GET field got a non-empty value')
            if not request.hasField('postempty'):
                error('We did not get the empty POST parameter')
            elif request.field('postempty') != '':
                error('The empty POST field got a non-empty value')
            if not request.hasField('getfield1'):
                error('The first GET parameter has not been passed')
            elif request.field('getfield1') != 'getvalue1':
                error('The first GET field got a wrong value')
            if not request.hasField('postfield1'):
                error('The first POST parameter has not been passed')
            elif request.field('postfield1') != 'postvalue1':
                error('The first POST field got a wrong value')
            if not request.hasField('getfield2'):
                error('The second GET parameter has not been passed')
            elif request.field('getfield2') != ['getvalue21', 'getvalue22']:
                error('The second GET field got a wrong value')
            if not request.hasField('postfield2'):
                error('The second POST parameter has not been passed')
            elif request.field('postfield2') != ['postvalue21', 'postvalue22']:
                error('The second POST field got a wrong value')
            if not request.hasField('dualfield1'):
                error('The first dual parameter has not been passed')
            elif request.field('dualfield1') == 'getdual1':
                error('The first dual field was not overridden via POST')
            elif request.field('dualfield1') in (
                    ['getdual1', 'postdual1'], ['postdual1', 'getdual1']):
                error('The first dual field'
                      ' was extended instead of overridden via POST')
            elif request.field('dualfield1') != 'postdual1':
                error('The first dual field got a wrong value')
            if not request.hasField('dualfield2'):
                error('The second dual parameter has not been passed')
            elif request.field('dualfield2') == ['getdual21', 'getdual22']:
                error('The second dual field was not overridden via POST')
            elif request.field('dualfield2') in (
                    ['getdual21', 'getdual22', 'postdual21', 'postdual22'],
                    ['postdual21', 'postdual22', 'getdual21', 'getdual22']):
                error('The second dual field'
                      ' was extended instead of overridden via POST')
            elif request.field('dualfield2') != ['postdual21', 'postdual22']:
                error('The second dual field got a wrong value')
            if errors:
                wr('<p>FieldStorage does <em>not</em> work as expected:</p>')
                wr('<ul>')
                for error in errors:
                    wr(f'<li>{error}.</li>')
                wr('</ul>')
            else:
                wr('<p>Everything ok, FieldStorage works as expected.</p>')
            wr('<p><a href="./">Back to the test cases overview.</a></p>')
