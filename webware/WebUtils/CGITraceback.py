"""More comprehensive traceback formatting for Python scripts.

Original version know as cgitb written By Ka-Ping Yee <ping@lfw.org>
Modified for Webware by Ian Bicking <ianb@colorstudy.com>
"""

import inspect
import keyword
import linecache
import os
import pydoc
import sys
import tokenize
from types import MethodType

pyhtml = pydoc.html
escape = pyhtml.escape

DefaultOptions = {
    'table': 'background-color:#f0f0f0',
    'default': 'color:#000',
    'row.location': 'color:#009',
    'row.code': 'color:#900',
    'header': 'color:#fff;background-color:#999',
    'subheader': 'color:#000;background-color:#f0f0f0;font-size:10pt',
    'code.accent': 'background-color:#ffc',
    'code.unaccent': 'color:#999;font-size:10pt',
}


def breaker():
    return (
        '<body style="background-color:#f0f0ff">' +
        '<span style="color:#F0F0FF;font-size:small"> > </span> ' +
        '</table>' * 5)


def html(context=5, options=None):
    if options:
        opt = DefaultOptions.copy()
        opt.update(options)
    else:
        opt = DefaultOptions

    etype, evalue = sys.exc_info()[:2]
    if not isinstance(etype, str):
        etype = etype.__name__
    inspect_trace = inspect.trace(context)

    javascript = """
    <script>
    function tag(s) { return '<'+s+'>'; }
    function popup_repr(title, value) {
        w = window.open('', '_blank',
            'directories=no,height=240,width=480,location=no,menubar=yes,'
            +'resizable=yes,scrollbars=yes,status=no,toolbar=no');
        if (!w) return true;
        w.document.open();
        w.document.write(tag('html')+tag('head')
            +tag('title')+title+tag('/title')+tag('/head')
            +tag('body style="background-color:#fff"')
            +tag('h3')+title+':'+tag('/h3')
            +tag('p')+tag('code')+value+tag('/code')+tag('/p')+tag('form')+
            tag('input type="button" onClick="window.close()" value="Close"')
            +tag('/form')+tag('/body')+tag('/html'));
        w.document.close();
        return false;
    }
    </script>
    """

    traceback_summary = []

    for frame, filename, lineno, func, lines, index in reversed(inspect_trace):
        if filename:
            filename = os.path.abspath(filename)
        else:
            filename = 'not found'
        traceback_summary.append(
            '<a href="#{}:{}" style="{}">{}</a>:'
            '<code style="font-family:Courier,sans-serif">{}</code>'.format(
                filename.replace('/', '-').replace('\\', '-'), lineno,
                opt['header'], os.path.splitext(os.path.basename(filename))[0],
                '{:5d}'.format(lineno).replace(' ', '&nbsp;')))

    head = (
        '<table style="width:100%;{}">'
        '<tr><td style="text-align:left;vertical-align:top">'
        '<strong style="font-size:x-large">{}</strong>: {}</td><td rowspan'
        '="2" style="text-align:right;vertical-align:top">{}</td></tr>'
        '<tr><td style="vertical-align:top;background-color:#fff">\n'
        '<p style="{}">A problem occurred while running a Python script.</p>'
        '<p style="{}">Here is the sequence of function calls leading up to'
        ' the error, with the most recent (innermost) call first.</p>\n'
        '</td></tr></table>\n'.format(
            opt['header'], etype, escape(str(evalue)),
            '<br>\n'.join(traceback_summary), opt['default'], opt['default']))

    indent = '<code><small>{}</small>&nbsp;</code>'.format('&nbsp;' * 5)
    traceback = []
    for frame, filename, lineno, func, lines, index in reversed(inspect_trace):
        if filename:
            filename = os.path.abspath(filename)
        else:
            filename = 'not found'
        try:
            file_list = filename.split('/')
            display_file = '/'.join(
                file_list[file_list.index('Webware') + 1:])
        except ValueError:
            display_file = filename
        if display_file[-3:] == '.py':
            display_file = display_file[:-3]
        link = '<a id="{}:{}"></a><a href="file:{}">{}</a>'.format(
            filename.replace('/', '-').replace('\\', '-'),
            lineno, filename.replace('\\', '/'), escape(display_file))
        args, varargs, varkw, locals = inspect.getargvalues(frame)
        if func == '?':
            call = ''
        else:
            call = 'in <strong>{}</strong>'.format(
                func + inspect.formatargvalues(
                    args, varargs, varkw, locals,
                    formatvalue=lambda value: '=' + html_repr(value)))

        names = []
        dotted = [0, []]

        def tokeneater():
            if type_ == tokenize.OP and token == '.':
                dotted[0] = 1
            if type_ == tokenize.NAME and token not in keyword.kwlist:
                if dotted[0]:
                    dotted[0] = 0
                    dotted[1].append(token)
                    if token not in names:
                        names.append(dotted[1][:])
                elif token not in names:
                    if token != 'self':
                        names.append(token)
                    dotted[1] = [token]
            if type_ == tokenize.NEWLINE:
                raise IndexError

        def linereader():
            nonlocal lineno
            line = linecache.getline(filename, lineno)
            line = line.encode('utf-8')
            lineno += 1
            return line

        for type_, token, _start, _end, _line in tokenize.tokenize(linereader):
            try:
                tokeneater()
            except IndexError:
                break

        lvals = []
        for name in names:
            if isinstance(name, list):
                if name[0] in locals or name[0] in frame.f_globals:
                    name_list, name = name, name[0]
                    if name_list[0] in locals:
                        value = locals[name_list[0]]
                    else:
                        value = frame.f_globals[name_list[0]]
                        name = f'<em>global</em> {name}'
                    for subname in name_list[1:]:
                        if hasattr(value, subname):
                            value = getattr(value, subname)
                            name += '.' + subname
                        else:
                            name += f'.(unknown: {name})'
                            break
                    name = f'<strong>{name}</strong>'
                    if isinstance(value, MethodType):
                        value = None
                    else:
                        value = html_repr(value)
            elif name in frame.f_code.co_varnames:
                if name in locals:
                    value = html_repr(locals[name])
                else:
                    value = '<em>undefined</em>'
                name = f'<strong>{name}</strong>'
            else:
                if name in frame.f_globals:
                    value = html_repr(frame.f_globals[name])
                else:
                    value = '<em>undefined</em>'
                name = f'<em>global</em> <strong>{name}</strong>'
            if value is not None:
                lvals.append(f'{name}&nbsp;= {value}')
        if lvals:
            lvals = ', '.join(lvals)
            lvals = indent + '<span style="{}">{}</span><br>\n'.format(
                opt['code.unaccent'], lvals)
        else:
            lvals = ''

        level = (
            '<br><table style="width:100%;{}">'
            '<tr><td>{} {}</td></tr></table>'.format(
                opt['subheader'], link, call))
        excerpt = []
        try:
            i = lineno - index
        except TypeError:
            i = lineno
        lines = lines or ['file not found']
        for line in lines:
            number = '&nbsp;' * (5-len(str(i))) + str(i)
            number = '<span style="{}">{}</span>'.format(
                opt['code.unaccent'], number)
            line = '<code>{}&nbsp;{}</code>'.format(
                number, pyhtml.preformat(line))
            if i == lineno:
                line = (
                    '<table style="width:100%;{}">'
                    '<tr><td>{}</td></tr></table>'.format(
                        opt['code.accent'], line))
            excerpt.append('\n' + line)
            if i == lineno:
                excerpt.append(lvals)
            i += 1
        traceback.append(level + '\n'.join(excerpt))

    exception = '<p><strong>{}</strong>: {}\n'.format(
        etype, escape(str(evalue)))
    attribs = []
    if evalue is not None:
        for name in dir(evalue):
            if name.startswith('__'):
                continue
            value = html_repr(getattr(evalue, name))
            attribs.append(f'<br>{indent}{name}&nbsp;= {value}\n')
    return (javascript + head + ''.join(traceback) +
            exception + ''.join(attribs) + '</p>\n')


def handler():
    print(breaker())
    print(html())


def html_repr(value):
    html_repr_instance = pyhtml._repr_instance
    enc_value = pyhtml.repr(value)
    if len(enc_value) > html_repr_instance.maxstring:
        plain_value = escape(repr(value))
        return (
            '{} <a href="#" onClick="return popup_repr('
            "'Full representation','{}')"
            '" title="Full representation">(complete)</a>'.format(
                enc_value, escape(plain_value).replace(
                    "'", "\\'").replace('"', '&quot;')))
    else:
        return enc_value
