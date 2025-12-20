.. _style-guidelines:

Style Guidelines
================


Introduction
------------

Style refers to various aspects of coding including indentation practices, naming conventions, use of design patterns, treatment of constants, etc. One of the goals of Webware war to maintain fairly consistent coding style with respect to certain basics as described in this document.

This document is therefore important for those who develop Webware itself or who wish to contribute code, although ordinary users may still find it interesting and useful in understanding the Webware APIs.

Please keep in mind that Webware for Python was developed when modern Python features like properties and style guidelines such as PEP8 did not yet exist. Therefore the API and code style used in Webware for Python may look a bit antiquated today. However, we decided to keep the old API in Webware for Python 3, and still follow most of the original style guidelines, in order to stay backward compatible and make migration of existing Webware for Python apps as painless as possible.


Syntax and Naming
-----------------

Methods and Attributes
~~~~~~~~~~~~~~~~~~~~~~

Methods and attributes are an important topic because they are used so frequently and therefore have an impact on using the classes, learning them, remembering them, etc.

The first thing that is important to understand is that Webware is constructed in an object-oriented fashion, including full encapsulation of object attributes. In other words, you communicate and use objects completely via their methods (except that classes and subclasses access their own attributes &ndash; somebody's got to).

The primary advantages of using methods are:

* Method implementations can be changed with minimal impact on the users of the class.
*  Subclasses can customize methods to suit their needs and still be used in the usual fashion (as defined by the superclass).

In the case of a method that returns a value, that value may manifest in several ways:

1. Stored as attribute.
2. Stored as an attribute, only on demand (e.g., lazy and cached).
3. Computed upon every request.
4. Delegated to another object.

By requiring that object access is done solely through methods, the implementer of the class is free to switch between the techniques above.

Keeping that in mind, it is apparent that naming conventions are needed for attributes, the methods that return them and the methods that set them. Let's suppose the basic "thing" is ``status``. The convention then is:

*  ``_status`` - the attribute
*  ``status()`` - the retrieval method
*  ``setStatus()`` - the setter method

The underscore that precedes the attribute denotes that it is semi-private and allows for a cleanly named retrieval method. The ``status()`` and ``setStatus()`` convention originated many years ago with Smalltalk and proved successful with that language as well as others, including Objective-C.

Some styles prefix the retrieval method with ``get``, but Webware does not for the sake of brevity and because there are methods for which it is not always clear if a ``get`` prefix would make sense.

Methods that return a Boolean are prefixed with ``is`` or ``has`` to make their semantics more obvious. Examples include ``request.isSecure()``, ``user.isActive()`` and ``response.hasHeader()``.

Method Categories
~~~~~~~~~~~~~~~~~

Webware classes divide their methods into logical groups called categories purely for organizational purposes. This often helps in understanding the interface of a class, especially when looking at its summary.

Upon installation, Webware generates HTML summaries for each Python source file. See the summary of HTTPResponse for an example.

By convention, a category is named with a comment beginning with `# region` and ending with `# endregion`. IDEs such as PyCharm will recognize these sections as foldable blocks.

Abbreviations
~~~~~~~~~~~~~

Using abbreviations is a common coding practice to reduce typing and make lines shorter. However, removing random characters to abbreviate is a poor way to go about this. For example, ``transaction`` could be abbreviated as ``trnsact`` or ``trnsactn``, but which letters are left out is not obvious or easy to remember.

The typical technique in Webware is to use the first whole syllable of the word. For example, ``trans`` is easy to remember, pronounce and type.

Attributes and methods that return the number of some kind of object are quite common. Suppose that the objects in questions are requests. Possible styles include ``numRequests``, ``numberOfRequests``, ``requestCount`` and so on. Webware uses the first style in all cases, for consistency::

    numRequests


If there is a corresponding attribute, it should have the same name (prefixed by an underscore).

Compound Names
~~~~~~~~~~~~~~

Identifiers often consist of multiple names. There are three major styles for handling compound names:

1.  ``serverSidePath`` - the Webware convention
2.  ``serversidepath``
3.  ``server_side_path``

Python itself used all three styles in the past (``isSet``, ``getattr``, ``has_key``), but Webware uses only the first which is more readable than the second and easier to type that the third.

This rule also applies to class names such as ``HTTPRequest`` and ``ServletFactory``.

Component Names
~~~~~~~~~~~~~~~

Names of object-oriented Webware components are often suffixed with **Kit**, as in **UserKit** and **MiddleKit**.

The occasional component that serves as a collective library (rather than an OO framework) is suffixed with **Utils**, as in *MiscUtils* and *WebUtils*.

Rules
~~~~~

We follow PEP 8 and usual Python conventions with these exceptions (for historical reasons and to remain backward compatible):

* Filenames are capitalized
* Method names are camelCase
* Attributes start with an underscore
* Getters and Setters for these attributes are ordinary methods.
* Setters use a "set" prefix, but getters do nt use a "get" prefix.


Structure and Patterns
----------------------

Classes
~~~~~~~

Webware overwhelmingly uses classes rather than collections of functions for several reasons:

*  Classes allow for subclassing and therefore, a proven method of software extension and customization.
*  Classes allow for creating multiple instances (or objects) to be used in various ways. Examples include caching created objects for increased performance and creating multi-threaded servers.
*  Classes can provide for and encourage encapsulation of data, which gives implementers more freedom to improve their software without breaking what depends on it.

By using classes, all three options above are available to the developer on an on-going basis. By using collections of functions, none of the above are readily available.

Note that making classes in Python is extraordinarily easy. Doing so requires one line::

    class Foo(SuperFoo):

and the use of ``self`` when accessing attributes and methods. The difference in time between creating a class with several methods vs. a set of several functions is essentially zero.

Configuration Files
~~~~~~~~~~~~~~~~~~~

Specific numbers and strings often appear in source code for determining things such as the size of a cache, the duration before timeout, the name of the server and so on. Rather than place these values directly in source, Webware provides configuration files that are easily discerned and edited by users, without requiring a walk through the source.

Webware uses ordinary Python dictionaries for configuration files for several reasons:

* Those who know Python will already understand the syntax.
*  Python dictionaries can be quickly and easily read (via Python's ``eval()`` function).
*  Dictionaries can contain nested structures such as lists and other dictionaries, providing a richer configuration language.

By convention, these configuration files:

*  Contain a Python dictionary.
*  Use a ``.config`` extension.
*  Capitalize their keys.
*  Are named after the class that reads them.
*  Are located in a ``Configs/`` subdirectory or in the same directory as the program.

Webware provides a ``Configurable`` mix-in class that is used to read configuration files. It allows subclasses to say ``self.setting('Something')`` so that the use of configuration information is easy and recognizable throughout the code.

Accessing Named Objects
~~~~~~~~~~~~~~~~~~~~~~~

Several classes in Webware store dictionaries of objects keyed by their name. ``HTTPRequest`` is one such class which stores a dictionary of form fields. The convention for providing an interface to this information is as follows::

    # region Fields
    def field(self, name, default=_NoDefault):
    def hasField(self, name):
    def fields(self):


A typical use would be::

    req.field('city')

which returns the field value of the given name or raises an exception if there is none. Like the ``get()`` method of Python's dictionary type, a second parameter can be specified which will be returned if the value is not found::

    req.field('city', None)


``req.hasField('city')`` is a convenience method that returns ``True`` if the value exists, ``False`` otherwise.

``req.fields()`` returns the entire dictionary so that users have complete access to the full suite of dictionary methods such as ``keys()``, ``values()``, ``items()``, etc. Users of this method are trusted not to modify the dictionary in any way. A paranoid class may choose to return a copy of the dictionary to help reduce abuse (although Webware classes normally do not for performance reasons).

In cases where the user of the class should be able to modify the named objects, the following methods are provided::

    def setValue(self, name, value):
    def delValue(self, name):

Often Python programmers will provide dictionary-style access to their objects by implementing ``__getitem__`` so that users may say::

    req['city']

Webware generally avoids this approach for two reasons. The first and most important is that Webware classes often have more than one set of named objects. For example, HTTPRequest has both fields and cookies. HTTPResponse has both cookies and headers. These objects have their own namespaces, making the semantics of ``obj['name']`` ambiguous. Also, the occasional class that has only one dictionary could potentially have more in the future.

The second reason is the readability provided by expressions such as ``response.cookie(name)`` which states clearly what is being asked for.

In those cases where objects provide dictionary-like access, the class is typically a lightweight container that is naturally thought of in terms of its dictionary components. Usually these classes inherit from ``dict``.

Components
~~~~~~~~~~

Webware consists of multiple components that follow particular conventions, not only for the sake of consistency, but also to enable scripts to manipulate them (such as generating documentation upon installation).

Example components include PSP, TaskKit and MiscUtils.

These conventions are not yet formally documented, however if you quickly browse through a couple components, some conventions about directory structure and source code become apparent.

Also, if a component serves as a Webware plug-in, then there are additional conventions for them to follow in order to work correctly. See the chapter on :ref:`plug-ins` for details.

Breaking the Rules
~~~~~~~~~~~~~~~~~~

Of course, there are times when the rules are broken for good reason. To quote a cliché: "Part of being an expert is knowing when to break the rules."

But regarding style, Webware developers do this very infrequently for the reasons stated in the introduction.
