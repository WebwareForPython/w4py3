"""HTTPStatusCodes.py

Dictionary of HTTP status codes.
"""

from http import HTTPStatus

__all__ = [
    'HTTPStatusCodeList', 'HTTPStatusCodes', 'htmlTableOfHTTPStatusCodes']

# pylint: disable=not-an-iterable
HTTPStatusCodeList = [
    (code.value, code.name, code.description) for code in HTTPStatus]

HTTPStatusCodeListColumnNames = ('Code', 'Identifier', 'Description')

# The HTTPStatusCodes can be indexed by either their status code number or
# by a textual identifier. The result is a dictionary with keys code,
# identifier, and description.
HTTPStatusCodes = {}

# Construct HTTPStatusCodes dictionary
for code, identifier, description in HTTPStatusCodeList:
    d = dict(code=code, identifier=identifier, description=description,
             # the following tow exist for backward compatibility only:
             htmlMsg=description, asciiMsg=description)
    HTTPStatusCodes[code] = d
    HTTPStatusCodes[identifier] = d


def htmlTableOfHTTPStatusCodes(
        codes=None,
        tableArgs='', rowArgs='style="vertical-align:top"',
        colArgs='', headingArgs=''):
    """Return an HTML table with HTTP status codes.

    Returns an HTML string containing all the status code information
    as provided by this module. It's highly recommended that if you
    pass arguments to this function, that you do so by keyword.
    """
    if codes is None:
        codes = HTTPStatusCodeList
    tableArgs = ' ' + tableArgs.lstrip() if tableArgs else ''
    rowArgs = ' ' + rowArgs.lstrip() if rowArgs else ''
    headingArgs = ' ' + headingArgs.lstrip() if headingArgs else ''
    colArgs = ' ' + colArgs.lstrip() if colArgs else ''
    res = [f'<table{tableArgs}>', '<tr>']
    res.extend(f'<th{headingArgs}>{heading}</th>'
               for heading in HTTPStatusCodeListColumnNames)
    res.append('</tr>')
    for code, identifier, description in codes:
        res.append(
            f'<tr{rowArgs}><td{colArgs}>{code}</td>'
            f'<td{colArgs}>{identifier}</td><td{colArgs}>{description}</td>'
            '</tr>')
    res.append('</table>')
    return '\n'.join(res)


# Old (deprecated) alias
HTMLTableOfHTTPStatusCodes = htmlTableOfHTTPStatusCodes


if __name__ == '__main__':
    print('''<html>
<head>
    <title>HTTP Status Codes</title>
</head>
<body>
{}
</body>
</html>'''.format(htmlTableOfHTTPStatusCodes()))
