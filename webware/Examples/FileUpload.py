from .ExamplePage import ExamplePage


class FileUpload(ExamplePage):
    """This servlet shows how to handle uploaded files.

    The process is fairly self explanatory. You use a form like the one below
    in the writeContent method. When the form is uploaded, the request field
    with the name you gave to the file selector form item will be an instance
    of the FieldStorage class from the standard Python module "cgi". The key
    attributes of this class are shown in the example below. The most important
    things are filename, which gives the name of the file that was uploaded,
    and file, which is an open file handle to the uploaded file. The uploaded
    file is temporarily stored in a temp file created by the standard module.
    You'll need to do something with the data in this file. The temp file will
    be automatically deleted. If you want to save the data in the uploaded file
    read it out and write it to a new file, database, whatever.
    """

    def title(self):
        return "File Upload Example"

    def writeContent(self):
        self.writeln("<h1>Upload Test</h1>")
        try:
            f = self.request().field('filename')
            contents = f.file.read()
        except Exception:
            output = f'''<p>{self.htmlEncode(self.__doc__)}</p>
<form action="FileUpload" method="post" enctype="multipart/form-data">
<input type="file" name="filename">
<input type="submit" value="Upload File">
</form>'''
        else:
            try:
                contentString = contents.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    contentString = contents.decode('latin-1')
                except UnicodeDecodeError:
                    contentString = contents.decode('ascii', 'replace')
            contentString = self.htmlEncode(contentString.strip())
            output = f'''<h4>Here's the file you submitted:</h4>
<table>
<tr><th>name</th><td><strong>{f.filename}</strong></td></tr>
<tr><th>type</th><td>{f.type}</td></tr>
<tr><th>type_options</th><td>{f.type_options}</td></tr>
<tr><th>disposition</th><td>{f.disposition}</td></tr>
<tr><th>disposition_options</th><td>{f.disposition_options}</td></tr>
<tr><th>headers</th><td>{f.headers}</td></tr>
<tr><th>size</th><td>{len(contents)} bytes</td></tr>
<tr><th style="vertical-align:top">contents</th>
<td><pre style="font-size:small;margin:0">{contentString}</pre></td></tr>
</table>'''
        self.writeln(output)
