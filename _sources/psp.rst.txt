.. module:: PSP

.. _psp:

===
PSP
===

Summary
=======

Python Server Pages (PSP) provides the capability for producing dynamic web pages for use with the Webware Python Servlet engine simply by writing standard HTML. The HTML code is interspersed with special tags that indicate special actions that should be taken when the page is served. The general syntax for PSP has been based on the popular Java Server Pages specification used with the Java Servlet framework.

Since the Webware Servlets are analogous to Java Servlets, PSP provides a scripting language for use with it that includes all of the power of Python. You will find that PSP compares favorably to other server side web scripting languages, such as ASP, PHP and JSP.

Features of PSP include:

* Familiar Syntax (ASP, JSP, PHP)
* The power of Python as the scripting language
* Full access to the Webware Servlet API
* Flexible PSP Base Class framework
* Ability to add additional methods to the class produced by PSP

Feedback
========

The PSP for Webware project is fully open source. Help in all areas is encouraged and appreciated. Comments should be directed to the Webware Discussion mailing list. This is a relatively low volume list and you are encouraged to join the list if you wish to participate in the development of PSP or Webware, or if you plan on developing an application using the framework.

General Overview
================

The general process for creating PSP files is similar to creating an HTML page. Simply create a standard HTML page, interspersed with the special PSP tags that your needs require. The file should be saved with an extension of ``.psp``. Place this file in a directory that is served by Webware. When a request comes in for this page, it will be dynamically compiled into a Webware servlet class, and an instance of this class will be instantiated to serve requests for that page.

There are two general types of PSP tags, ``<%...%>`` and ``<psp:...>``. Each of these tags have special characteristics, described below.

Whether or not you will need to include standard HTML tags in the start of your PSP page, such as ``<html>``, ``<head>`` etc. depends on the base class you choose for your PSP class. The default setup does not output any of those tags automatically.

PSP Tags
========

The following tags are supported by the current PSP implementation.

Expression Tag -- ``<%= expression %>``
---------------------------------------

The expression tag simply evaluates some Python code and inserts its text representation into the HTML response. You may include anything that will evaluate to a value that can be represented as a string inside the tag.

**Example**::

    The current time is <%= time.time() >


When the PSP parsing engine encounters Expression tags, it wraps the contents in a call to the Python ``str()`` function. Multiple lines are not supported in a PSP expression tag.

Script Tag -- ``<% script code %>``
-----------------------------------

The script tag is used to enclose Python code that should be run by the Webware Servlet runner when requests are processed by the Servlet which this PSP page produces. Any valid Python code can be used in Script tags. Inside a script tag, indentation is up to the author, and is used just like in regular Python (more info on blocks below). The PSP Engine actually just outputs the strings in a Script tag into the method body that is being produced by this PSP page.

**Example**::

    <% for i in range(5):
        res.write("<b>This is number" + str(i) + "</b><br>") %>

The Python code within script tags has access to all local and class variables declared in the PSP page, as well as to all variables of the enclosing class of this PSP page.

Special local variables that will be available in all PSP pages are:

``req``
  The HTTRequest object for this page.

``res``
  The HTTPResponse object for this page.
  The HTTPResponse object includes the *write* method that is used to output HTML to the client.

``trans``
  The Transaction object for this client request.
  The Transaction object provides access to the objects involved in servicing this client request.

Python Code Blocks that span PSP Script Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python code structure, which uses whitespace to signify blocks of code, presents a special challenge in PSP pages. In order to allow for readable HTML code that does not impose restrictions on straight HTML within PSP pages, PSP uses a special syntax to handle Python blocks that span script tags.

Automatic Blocks
~~~~~~~~~~~~~~~~

Any script tag with Python code that ends with a colon (:) is considered to begin a block. A comment tag may follow the colon. After this tag, any following HTML is considered to be part of the block begun within the previous script tag. To end the block, insert a new script tag with the word "end" as the only statement.

**Example of Script/HTML block**::

    <% for i in range(5): %>  # the blocks starts here, no need for indenting the following HTML
    <tr><td><%= i%></td></tr>
    <% end %> The "end" statement ends the block

These blocks can be nested, with no need for special indentation, and each script tag that only contains a solitary end statement will reduce the block indent by one.

Manual Blocks
~~~~~~~~~~~~~

It is also possible to force a block of HTML statements to be included in a block. You might want to do this if your start a loop of some kind in a script tag, but need the first line of the loop to also be inside the script tag. In this case, the automatic indenting described above wouldn't notice the block, because the last line in the script tag wouldn't be a ":". In this case, you need to end the script tag with ``$%>``. When a script tag ends with ``$%>``, the PSP Parser will indent the following HTML at the same level as the last line of the script tag. To end this level of indentation, just start another script tag. Easy.

**Example of Manual Indention Script/HTML block**::

    <% for i in range(5):
        icubed = i*i $%>  # The following lines of straight HTML will be included in the same block this line is on
      <tr><td><%= icubed%></td></tr>
    <% pass %>  # Any new script statement resets the HTML indentation level

You could also start a new script block that just continues at the same indentation level that the HTML and the previous script block were at.

Braces
~~~~~~

PSP also supports using braces to handle indentation. This goes against the grain of Python, we know, but is useful for this specific application. To use this feature, specify it as you indentation style in a page directive, like so::

    <%@page indentType="braces" %>

Now use braces to signify the start and end of blocks. The braces can span multiple script tags. No automatic indentation will occur. However, you must use braces for all blocks! Tabs and spaces at the start of lines will be ignored and removed!

**Example**::

    This is <i>Straight HTML</i><br>
    <%
      for i in range(5): { %>  # Now I'm starting a block for this loop
      z = i*i
    %>
    <!-- Now I'm ending the scripting tag that started the block,
    but the following lines are still in the block -->
    More straight HTML. But this is inside the loop started above.<br>
    My i value is now <%= i %><br>
    Now I will process it again.<br>
    <%
      v = z*z
    %>
    Now it is <%=v %>
    <% } %>  # End the block

File and Class Level Code -- ``<psp:file>`` and ``<psp:class>``
---------------------------------------------------------------

The file and class level script tag allows you to write Python code at the file (module) level or class level. For example, at the file level, you might do imports statements, and some initialization that occurs only when the PSP file is loaded the first time. You can even define other classes that are used in your PSP file.

**Example**::

    <psp:file>
      # Since this is at the module level, _log is only defined once for this file
      import logging
      _log = logging.getLogger( __name__ )
    </psp:file>
    <html>
      <% _log.debug('Okay, Ive been called.') %>
      <p>Write stuff here.</p>
    </html>

At the class level you can define methods using ordinary Python syntax instead of the <psp:method > syntax below.

**Example**::

    <psp:class>
      def writeNavBar(self):
        for uri, title in self.menuPages():
          self.write( "<a href="%s">%s</a>" % (uri, title) )
    </psp:class>

Indentation is adjusted within the file and class blocks. Just make your indentation consistent with the block, and PSP will adjust the whole block to be properly indented for either the class or the file. For example file level Python would normally have no indentation. But in PSP pages, you might want some indentation to show it is inside of the ``<psp:file>...</psp:file>`` tags. That is no problem, PSP will adjust accordingly.

There is one special case with adding methods via the ``<psp:class>`` tag. The ``awake()`` method requires special handling, so you should always use the ``<psp:method>`` tag below if you want to override the ``awake()`` method.

Method Tag -- ``<psp:method ...>``
----------------------------------

The Method tag is used to declare new methods of the Servlet class this page is producing. It will generally be more effective to place method declarations in a Servlet class and then have the PSP page inherit from that class, but this tag is here for quick methods. The Method tag may also be useful for over-riding the default functionality of a base class method, as opposed to creating a Servlet class with only a slight change from another.

The syntax for PSP methods is a little different from that of other tags. The PSP Method declaration uses a compound tag. There is a beginning tag ``<psp:method name="methname" params="param1, param2">`` that designates the start of the method definition and defines the method name and the names of its parameters. The text following this tag is the actual Python code for the method. This is standard Python code, with indentation used to mark blocks and no raw HTML support. It is not necessary to start the method definition with indentation, the first level of indention is provided by PSP.

To end the method definition block, the close tag ``</psp:method>`` is used.

**Example**::

    <psp:method name="MyClassMethod" params="var1, var2">
      import string
      return string.join((var1,var2),'')
    </psp:method>

This is a silly function that just joins two strings. Please note that it is not necessary to declare the self parameter as one of the function's parameters. This will be done automatically in the code that PSP generates.

A PSP:Method can be declared anywhere in the psp sourcefile and will be available throughout the PSP file through the standard ``self.PSPMethodName(parameters)`` syntax.

Include Tag -- ``<psp:include ...>``
------------------------------------

The include tag pauses processing on the page and immediately passes the request on the the specified URL. The output of that URL will be inserted into the output stream, and then processing will continue on the original page. The main parameter is ``path``, which should be set to the path to the resources to be included. This will be relative to the current page, unless the path is specified as absolute by having the first character as "/". The path parameter can point to any valid url on this Webware application. This functionality is accomplished using the Webware Application's forwardRequestFast function, which means that the current Request, Response and Session objects will also be used by the URL to which this request is sent.

**Example**::

    <psp:include path="myfile.html">

Insert Tag -- ``<psp:insert ...>``
----------------------------------

The insert tag inserts a file into the output stream that the psp page will produce, but does not parse that included file for psp content. The main parameter is ``file``, which should be set to the filename to be inserted. If the filename starts with a "/", it is assumed to be an absolute path. If it doesn't start with a "/", the file path is assumed to be relative to the psp file. The contents of the insert file will not be escaped in any way except for triple-double-quotes (&quot;&quot;&quot;), which will be escaped.

At every request of this servlet, this file will be read from disk and sent along with the rest of the output of the page.

This tag accepts one additional parameter, "static", which can be set to "True" or "1". Setting this attribute to True will cause the inserted file's contents to be embedded in the PSP class at generation time. Any subsequent changes to the file will not be seen by the servlet.

**Example**::

    <psp:insert file="myfile.html">

Directives
==========

Directives are not output into the HTML output, but instead tell the PSP parser to do something special. Directives have at least two elements, the type of directive, and one or more parameters in the form of ``param="value"`` pairs.

Supported Directives include:

Page Directive -- ``<%@ page ... %>``
-------------------------------------

The page directive tells the PSP parser about special requirements of this page, or sets some optional output options for this page. Directives set in ``page`` apply to the elements in the current PSP source file and to any included files.

Supported Page parameters:

* ``imports`` --
  The imports attribute of the page directive tells the PSP parser to import certain Python modules into the PSP class source file.

  The format of this directive is as follows:

  **Example**: ``<%@ page imports="sys,os"%>``

  The value of the imports parameter may have multiple, comma separated items.

  ``from X import Y`` is supported by separating the source package from the object to be imported with a colon (:), like this:

  **Example**: ``<%@ page imports="os:path" %>``

  This will import the path object from the os module.

  Please note the ``=`` sign used in this directive. Those who are used to Python might try to skip it.

* ``extends`` --
  The extends attribute of the page tells the PSP parser what base class this Servlet should be derived from.

  The PSP servlet produced by parsing the PSP file will inherit all of the attributes and methods of the base class.

  The Servlet will have access to each of those attributes and methods. They will still need to be accessed using the "self" syntax of Python.

  **Example**: ``<%@ page extends="MyPSPBaseClass"%>``

  This is a very powerful feature of PSP and Webware. The developer can code a series of Servlets that have common functionality for a series of pages, and then use PSP and the extends attribute to change only the pieces of that base servlet that are specific to a certain page. In conjunction with the ``method`` page attribute, described below, and/or the ``<psp:method ...>`` tag, entire sites can be based on a few custom PSP base classes. The default base class is ``PSPPage.py``, which is inherited from the standard Webware ``Page.py`` servlet.

  You can also have your PSP inherit from multiple base classes. To do this, separate the base classes using commas, for example ``<%@ page extends="BaseClass1,BaseClass2"%>``. If you use a base class in ``<%@ page extends="..."%>`` that is not specifically imported in a ``<%@ page imports="..."%>`` directive, the base class will be assumed to follow the servlet convention of being in a file of the same name as the base class plus the ".py" extension.

* ``method`` --
  The ``method`` attribute of the ``page`` directive tells the PSP parser which method of the base class the HTML of this PSP page should be placed in and override.

  **Example**: ``<%@ page method="WriteHTML"%>``

  Standard methods are ``WriteHTML``, of the standard ``HTTPServlet`` class, and ``writeBody``, of the ``Page`` and ``PSPPage`` classes. The default is ``writeBody``. However, depending on the base class you choose for your PSP class, you may want to override some other method.

* ``isThreadSafe`` --
  The ``isThreadSafe`` attribute of ``page`` tells the PSP parser whether the class it is producing can be utilized by multiple threads simultaneously. This is analogous to the ``isThreadSafe`` function in Webware servlets.

  **Example**: ``<%@ page isThreadSafe="yes"%>``

  Valid values are "yes" and "no". The default is "no".

* ``isInstanceSafe`` --
  The ``isInstanceSafe`` attribute of the ``page`` directive tells the PSP parser   whether one instance of the class being produced may be used multiple times. This is analogous to the isInstanceSafe function of Webware Servlets.

  **Example**: ``<%@ page isInstanceSafe="yes"%>``

  Valid values are "yes" and "no". The default is "yes".

* ``indentType`` --
  The ``indentType`` attribute of the ``page`` directive tells the parser how to handle block indention in the Python sourcefile it creates. The ``indentType`` attribute sets whether the sourcefile will be indented with tabs or spaces, or braces. Valid values are "tabs", "spaces" or "braces". If this is set to "spaces", see ``indentSpaces`` for setting the number of spaces to be used (also, see blocks, below). The default is "spaces".

  **Example**: ``<%@ page indentType="tabs"%>``

  This is a bit of a tricky item, because many editors will automatically replace tabs with spaces in their output, without the user realizing it. If you are having trouble with complex blocks, look at that first.

* ``indentSpaces`` --
  Sets the number of spaces to be used for indentation when ``indentType`` is set to spaces. The default is "4".

  **Example**: ``<%@ page indentSpaces="8" %>``

* ``gobbleWhitespace`` --
  The ``gobblewhitespace`` attribute of the ``page`` directive tells the PSP parser whether it can safely assume that whitespace characters that it finds between two script tags can be safely ignored. This is a special case directive. It applies when there are two script tags of some kind, and there is only whitespace characters between the two tags. If there is only whitespace, the parser will ignore the whitespace. This is necessary for multipart blocks to function correctly. For example, if you are writing an if/else block, you would have your first script block that starts the if, and then you would end that block and start a new script block that contains the else portion. If there is any whitespace between these two script blocks, and ``gobbleWhitespace`` is turned off, then the parser will add a write statement between the two blocks to output the whitespace into the page. The problem is that the write statement will have the indentation level of the start of the if block. So when the else statement starts, it will not be properly associated with the preceding if, and you'll get an error.

  If you do need whitespace between two script blocks, use the ``&nbsp;`` code.

  **Example**: ``<%@ page gobbleWhitspace="No"%>``

  Valid values are "yes" and "no". The default is "yes".

* ``formatter`` --
  The ``formatter`` attribute of the ``page`` directive can be used to specify an alternative formatter function for ``<%= ... %>`` expression blocks. The default value is ``str``. You might want to use this if certain types need to be formatted in a certain way across an entire page; for example, if you want all integers to be formatted with commas like "1,234,567" you could make that happen by specifying a custom formatter.

  **Example**::

        <%@ page imports="MyUtils" %>
        <%@ page formatter="MyUtils.myFormatter" %>

Include Directive -- ``<%@ include ... %>``
-------------------------------------------

The include directive tells the parser to insert another file at this point in the page and to parse it for psp content. It is generally no problem to include an html file this way. However, if you do not want your include file to be parsed, you may use the ``<psp:include ...>`` tag described above.

**Example**::

    <%@ include file="myfile.txt"%>

Other Tags
==========

* **Declaration** (``<%! ... %>``) -- No need for this tag. Simply use script tags to declare local variables.
* **Forwarding** functionality is now available in Webware, but no tag based support has been added to PSP yet.

Developers
==========

The original author of PSP is Jay Love and the project was later maintained by Jay and Geoff Talvola. The contributions of the entire Webware community have been invaluable in improving this software.

Some architectural aspects of PSP were inspired by the Jakarta Project.
