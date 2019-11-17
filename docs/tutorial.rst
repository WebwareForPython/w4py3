.. _beginner-tutorial:

Beginner Tutorial
=================

In this tutorial we will show how to write a very simple Webware application.

Again, we assume that you have Webware for Python 3 already installed in a virtual environment, and activate the virtual environment as explained in the chapter on :ref:`Installation`.


Creating a Working Directory
----------------------------

We'll first set up a directory dedicated to your application, the so-called "application working directory". Change into your home directory or wherever you want to create that working directory. We recommend creating the virtual environment and the application working directory as siblings in a dedicated base directory, which can be the home directory of a dedicated user that acts as "owner" of the application. Then run this command::

    webware make -c Context -l Lib WebwareTest

You'll now have a directory "WebwareTest" in the current directory. Inside this directory will be several subdirectories and a couple files. The directories of interest are ``Context`` (that you specified with ``-c context``) where you'll be putting your servlets; ``Configs`` that holds some configuration files; and ``Lib`` where you can put your non-servlet code.

For more information about the working directory and setting up the file structure for your application, see :ref:`application-development`.


Changing the Webware Configuration
----------------------------------

For the most part the configuration is fine, but we'll make a couple changes to make it easier to develop. For more information on configuration see the chapter on :ref:`Configuration`.

One change you may want to make to allow you to use more interesting URLs. In ``Application.config``, change the ``ExtraPathInfo`` setting from ``False`` (the default) to ``True``::

    ExtraPathInfo = True

Otherwise the settings should be appropriate already for our purposes.


Creating and Understanding the Servlet
--------------------------------------

Webware's core concept for serving pages is the *servlet*. This is a class that creates a response given a request.

The core classes to understanding the servlet are ``Servlet``, ``HTTPServlet``, and ``Page``. Also of interest would be the request (``Request`` and ``HTTPRequest``) and the response (``Response`` and ``HTTPResponse``)
-- the ``HTTP-`` versions of these classes are more interesting. There is also a ``Transaction`` object, which is solely a container for the request and response.

While there are several levels you can work on while creating your servlet, in this tutorial we will work solely with subclassing the ``Page`` class. This class defines a more high-level interface, appropriate for generating HTML (though it can be used with any content type). It also provides a number of convenience methods.


A Brief Introduction to the Servlet
-----------------------------------

Each servlet is a plain Python class. There is no Webware magic (except perhaps for the level one *import module based on URL* spell). :ref:`psp` has more magic, but that's a topic for another chapter.

An extremely simple servlet might look like::

    from Page import Page

    class MyServlet(Page):

        def title(self):
            return 'My Sample Servlet'

        def writeContent(self):
            self.write('Hello world!')

This would be placed in a file ``MyServlet.py``. Webware will create a pool of ``MyServlet`` instances, which will be reused. Servlets "write" the text of the response, like you see in the ``writeContent()`` method above.

Webware calls the servlet like this:

* An unused servlet is taken from the pool, or another servlet is created.
* ``awake(transaction)`` is called. This is a good place to set up data for your servlet. You can put information in instance variables for use later on. But be warned -- those instance variables will hang around potentially for a long time if you don't delete them later (in ``sleep``).
* Several low-level methods are called, which Page isolates you from. We will ignore these.
* ``writeHTML()`` is called. ``Page`` implements this just fine, but you can override it if you want total control, or if you want to output something other than HTML.
* ``writeDocType()`` would write something like ``<!DOCTYPE html>``.
* The <head> section of the page is written. ``title()`` gives the title, and you probably want to override it.
* ``writeStyleSheet()`` is called, if you want to write that or anything else in the ``<head>`` section.
* The ``<body>`` tag is written. Have ``htBodyArgs()`` return anything you want in the ``<body>`` tag (like ``onLoad="loadImages()"``).
* ``writeBodyParts()`` is called, which you may want to override if you want to create a template for other servlets.
* ``writeContent()`` should write the main content for the page. This is where you do most of your display work.
* The response is packaged up, the headers put on the front, cookies handled, and it's sent to the browser. This is all done for you.
* ``sleep(transaction)`` is called. This is where you should clean up anything you might have set up earlier -- open files, open database connections, etc. Often it's empty. Note that ``sleep()`` is called even if an exception was raised at any point in the servlet processing, so it should (if necessary) check that each resource was in fact acquired before trying to release it.
* The servlet is placed back into the pool, to be used again. This only happens after the transaction is complete -- the servlet won't get reused any earlier.

You only have to override the portions that you want to. It is not uncommon to only override the ``writeContent()`` method in a servlet, for instance.

You'll notice a file ``Context/Main.py`` in your working directory. You can look at it to get a feel for what a servlet might look like. (As an aside, a servlet called ``Main`` or ``index`` will be used analogous to the ``index.html`` file). You can look at it for a place to start experimenting, but here we'll work on developing an entire (small) application, introducing the other concepts as we go along.


A Photo Album
-------------

If you look online, you'll see a huge number of web applications available for an online photo album. The world needs one more!

You will need the `Pillow`_ library installed for this example. If you installed Webware for Python 3 with the "examples" or "test" option, as recommended in the chapter on :ref:`installation`, this should be already the case. First we'll use this library to find the sizes of the images, and later we will use it to create thumbnails.

.. _Pillow: https://python-pillow.org/

We'll develop the application in two iterations.

Iteration 1: Displaying files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For simplicity, we will store image files in a subdirectory ``Pics`` of the default context directory ``WebwareTest/Context`` and let the development server deliver the files. In a production environment, you would place the ``Pics`` directory outside of the context and let the web server deliver the files directly.

For the first iteration, we'll display files that you upload by hand to the ``Pics`` directory.

We do this with two servlets -- one servlet ``Main.py`` to show the entire album, and another ``View.py`` for individual pictures. Place these two servlets in the default context directory. First, ``Main.py`` (replacing the example servlet that has already been crated)::

    import os

    from PIL import Image  # this is from the Pillow library

    from Page import Page  # the base class for web pages

    dir = os.path.join(os.path.dirname(__file__), 'Pics')


    class Main(Page):

        def title(self):
            # It's nice to give a real title, otherwise "Main" would be used.
            return 'Photo Album'

        def writeContent(self):
            # We'll format these simply, one thumbnail per line:
            for filename in os.listdir(dir):
                im = Image.open(os.path.join(dir, filename))
                w, h = im.size
                # Here we figure out the scaled-down size of the image,
                # so that we preserve the aspect ratio. We'll use fake
                # thumbnails, where the image is scaled down by the browser.
                w, h = int(round(w * 100 / h)), 100
                # Note that we are just using f-strings to generate the HTML.
                # There's other ways, but this works well enough.
                # We're linking to the View servlet which we'll show later.
                # Notice we use urlencode -- otherwise we'll encounter bugs if
                # there are file names with spaces or other problematic chars.
                url = self.urlEncode(filename)
                self.writeln(f'<p><a href="View?filename={url}">'
                    f'<img src="Pics/{url}" width="{w}" height="{h}"></a></p>')

The servlet ``View.py`` takes one URL parameter of ``filename``. You can get the value of a URL parameter like ``self.request().field('filename')`` or, if you want a default value, you can use ``self.request().field('filename', defaultValue)``. In the likely case you don't want to write ``self.request()`` before retrieving each value, do::

    req = self.request()
    self.write(req.field('username'))

If you need the request only once, you can write it even more compactly::

    field = self.request().field
    self.write(field('username'))

So here is our complete ``View`` servlet::

    import os

    from PIL import Image

    from Page import Page

    dir = os.path.join(os.path.dirname(__file__), 'Pics')


    class View(Page):

        def title(self):
            return 'View: ' + self.htmlEncode(self.request().field('filename'))

        def writeContent(self):
            filename = self.request().field('filename')
            im = Image.open(os.path.join(dir, filename))
            wr = self.writeln
            wr('<div style="text-align:center">')
            wr(f'<h4>{filename}</h4>')
            url = self.urlEncode(filename)
            w, h = im.size
            wr(f'<img src="Pics/{url}" width="{w}" height="{h}">')
            wr('<p><a href="Main">Return to Index</a></p>')
            wr('</div>')


Iteration 2: Uploading Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

That was fairly simple -- but usually you want to upload files, potentially through a web interface. Along the way we'll add thumbnail generation using Pillow, and slightly improve the image index.

We'll generate thumbnails kind of on demand, so you can still upload files manually -- thumbnails will be put in the directory ``Thumbs`` and have ``-tn`` appended to the name just to avoid confusion::

    import os

    from PIL import Image

    from Page import Page

    baseDir = os.path.dirname(__file__)
    picsDir = os.path.join(baseDir, 'Pics')
    thumbsDir = os.path.join(baseDir, 'Thumbs')


    class Main(Page):

        def title(self):
            return 'Photo Album'

        def writeContent(self):
            # The heading:
            self.writeln(f'<h1 style="text-align:center">{self.title()}</h1>')
            # We'll format these in a table, two columns wide
            self.writeln('<table width="100%">')
            col = 0  # will be 0 for the left and 1 for the right column
            filenames = os.listdir(picsDir)
            # We'll sort the files, case-insensitive
            filenames.sort(key=lambda filename: filename.lower())
            for filename in filenames:
                if not col:  # left column
                    self.write('<tr style="text-align:center">')
                thumbFilename = os.path.splitext(filename)
                thumbFilename = '{}-tn{}'.format(*thumbFilename)
                if not os.path.exists(os.path.join(thumbsDir, thumbFilename)):
                    # No thumbnail exists -- we have to generate one
                    if not os.path.exists(thumbsDir):
                        # Not even the Thumbs directory exists -- make it
                        os.mkdir(thumbsDir)
                    im = Image.open(os.path.join(picsDir, filename))
                    im.thumbnail((250, 100))
                    im.save(os.path.join(thumbsDir, thumbFilename))
                else:
                    im = Image.open(os.path.join(thumbsDir, thumbFilename))
                url = self.urlEncode(filename)
                w, h = im.size
                size = os.stat(os.path.join(picsDir, filename)).st_size
                self.writeln(f'<td><p><a href="View?filename={url}">'
                    f'<img src="Pics/{url}" width="{w}" height="{h}"></a></p>'
                    f'<p>Filename: {filename}<br>Size: {size} Bytes</p>')
                if col:  # right column
                    self.writeln('</tr>')
                col = not col
            self.write('</table>')
            self.write('<p style="text-align:center">'
                '<a href="Upload">Upload an image</a></p>')

In a real application, you would probably style the image more nicely using CSS, maybe using a flexbox or grid layout instead of using a table. You can add a CSS style sheet for this purpose with the ``writeStyleSheet()`` method.

The ``View`` servlet we'll leave just like it was.

We'll add an ``Upload`` servlet. Notice we use ``enctype="multipart/form-data"`` in the ``<form>`` tag -- this is an HTMLism for file uploading (otherwise
you'll just get the filename and not the file contents). Finally, when the form is finished and we have uploaded the image, we redirect them to the viewing
page by using ``self.response().sendRedirect(url)``::

    import os

    from Page import Page

    dir = os.path.join(os.path.dirname(__file__), 'Pics')


    class Upload(Page):

        def writeContent(self):
            if self.request().hasField('imageFile'):
                self.doUpload()
                return

            self.writeln('''
            <h3>Upload your image:</h3>
            <form action="Upload" method="post" enctype="multipart/form-data">
            <input type="file" name="imageFile">
            <input type="submit" value="Upload">
            </form>''')

        def doUpload(self):
            file = self.request().field('imageFile')
            # Because it's a file upload, we don't get a string back.
            # So to get the value we do this:
            filename, contents = file.filename, file.value
            open(os.path.join(dir, filename), 'wb').write(contents)
            url = 'View?filename=' + self.urlEncode(filename)
            self.response().sendRedirect(url)

Using the "upload" button it should now be possible to upload images to the ``Pics`` directory.
