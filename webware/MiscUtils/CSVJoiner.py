"""CSVJoiner.py

A helper function for joining CSV fields.
"""


def joinCSVFields(fields):
    """Create a CSV record by joining its fields.

    Returns a CSV record (e.g. a string) from a sequence of fields.
    Fields containing commands (,) or double quotes (") are quoted,
    and double quotes are escaped ("").
    The terminating newline is *not* included.
    """
    newFields = []
    for field in fields:
        if not isinstance(field, str):
            raise UnicodeDecodeError('CSV fields should be strings')
        if '"' in field:
            newField = '"{}"'.format(field.replace('"', '""'))
        elif ',' in field or '\n' in field or '\r' in field:
            newField = f'"{field}"'
        else:
            newField = field
        newFields.append(newField)
    return ','.join(newFields)
