"""NamedValueAccess.py

NamedValueAccess provides functions for accessing Python objects by keys and
named attributes. A 'key' is a single identifier such as 'foo'. A 'name' could
be a key, or a qualified key, such as 'foo.bar.boo'. Names are generally more
convenient and powerful, while the key-oriented function is more efficient and
provide the atomic functionality that the name-oriented function is built upon.

CREDIT

Chuck Esterbrook <echuck@mindspring.com>
Tavis Rudd <tavis@calrudd.com>
"""

from MiscUtils import NoDefault


class NamedValueAccessError(LookupError):
    """General named value access error."""


class ValueForKeyError(NamedValueAccessError):
    """No value for key found error."""


def valueForKey(obj, key, default=NoDefault):
    """Get the value of the object named by the given key.

    This method returns the value with the following precedence:
      1. Methods before non-methods
      2. Attributes before keys (__getitem__)
      3. Public things before private things
         (private being denoted by a preceding underscore)

    Suppose key is 'foo', then this method returns one of these:
      * obj.foo()
      * obj._foo()
      * obj.foo
      * obj._foo
      * obj['foo']
      * default  # only if specified

    If all of these fail, a ValueForKeyError is raised.

    NOTES

      * valueForKey() works on dictionaries and dictionary-like objects.
      * See valueForName() which is a more advanced version of this
        function that allows multiple, qualified keys.
    """

    if obj is None:
        raise TypeError('We do not accept None as object')

    if not isinstance(key, str):
        raise TypeError('We only accept strings for keys')

    attr = None
    unknown = False
    if isinstance(obj, dict):
        if default is NoDefault:
            try:
                return obj[key]
            except KeyError:
                raise ValueForKeyError(key) from None
        else:
            return obj.get(key, default)
    else:
        try:
            cls = obj.__class__
        except AttributeError:
            # happens for classes themselves
            cls = method = None
        else:
            method = getattr(cls, key, None)
        if not method:
            underKey = '_' + key
            method = getattr(cls, underKey, None) if cls else None
            if not method:
                attr = getattr(obj, key, NoDefault)
                if attr is NoDefault:
                    attr = getattr(obj, underKey, NoDefault)
                    if attr is NoDefault and cls is not None:
                        getitem = getattr(cls, '__getitem__', None)
                        if getitem:
                            try:
                                getitem(obj, key)
                            except KeyError:
                                unknown = True

    if not unknown:
        if method:
            return method(obj)
        if attr is not NoDefault:
            return attr

    if default is not NoDefault:
        return default

    raise ValueForKeyError(key)


def valueForName(obj, name, default=NoDefault):
    """Get the value of the object that is named.

    The name can use dotted notation to traverse through a network/graph
    of objects. Since this function relies on valueForKey() for each
    individual component of the name, you should be familiar with the
    semantics of that notation.

    Example: valueForName(obj, 'department.manager.salary')
    """
    for name in name.split('.'):
        obj = valueForKey(obj, name, default)
        if obj is default:
            break
    return obj
