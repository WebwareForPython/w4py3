import os

from MiscUtils.DataTable import DataTable

from .AdminSecurity import AdminSecurity


class DumpCSV(AdminSecurity):

    def filename(self):
        """Overridden by subclasses to specify what filename to show."""
        raise NotImplementedError

    def awake(self, transaction):
        AdminSecurity.awake(self, transaction)
        self._filename = self.filename()

    def shortFilename(self):
        return os.path.splitext(os.path.split(self._filename)[1])[0]

    def title(self):
        return 'View ' + self.shortFilename()

    def writeContent(self):
        if not os.path.exists(self._filename):
            self.writeln('<p>File does not exist.</p>')
            return
        table = DataTable(self._filename)
        plural = '' if len(table) == 1 else 's'
        self.writeln(f'<p>{len(table)} row{plural}</p>')
        self.writeln('<table class="NiceTable">')
        # Head row gets special formatting
        self._headings = [col.name().strip() for col in table.headings()]
        self._numCols = len(self._headings)
        self.writeln('<tr>')
        for value in self._headings:
            self.writeln('<th>', value, '</th>')
        self.writeln('</tr>')
        # Data rows
        for rowIndex, row in enumerate(table, 1):
            self.writeln('<tr>')
            for colIndex, value in enumerate(row):
                if colIndex >= self._numCols:
                    break  # skip surplus columns
                self.writeln('<td>',
                             self.cellContents(rowIndex, colIndex, value),
                             '</td>')
            self.writeln('</tr>')
        self.writeln('</table>')

    def cellContents(self, _rowIndex, _colIndex, value):
        """Hook for subclasses to customize the contents of a cell.

        Based on any criteria (including location).
        """
        return value
