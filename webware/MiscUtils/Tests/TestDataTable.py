import os
import unittest

from io import StringIO

from MiscUtils.DataTable import DataTable, DataTableError, TableColumn

cannotReadExcel = not DataTable.canReadExcel()


class TestTableColumn(unittest.TestCase):

    def testWithType(self):
        c = TableColumn('foo:int')
        self.assertEqual(c.name(), 'foo')
        self.assertTrue(c.type() is int)

    def testWithoutType(self):
        c = TableColumn('bar')
        self.assertEqual(c.name(), 'bar')
        self.assertTrue(c.type() is None)

    def testWrongSpec(self):
        self.assertRaises(DataTableError, TableColumn, 'foo:bar')
        self.assertRaises(DataTableError, TableColumn, 'foo:bar:baz')

    def testValueForRawValue(self):
        c = TableColumn('foo:int')
        self.assertEqual(c.valueForRawValue(''), 0)
        self.assertEqual(c.valueForRawValue('1'), 1)
        self.assertEqual(c.valueForRawValue(2), 2)
        self.assertEqual(c.valueForRawValue(2.5), 2)
        c = TableColumn('bar:str')
        self.assertEqual(c.valueForRawValue(''), '')
        self.assertEqual(c.valueForRawValue('1'), '1')
        self.assertEqual(c.valueForRawValue(2), '2')
        self.assertEqual(c.valueForRawValue('x'), 'x')
        c = TableColumn('bar:float')
        self.assertEqual(c.valueForRawValue(''), 0.0)
        self.assertEqual(c.valueForRawValue('1'), 1.0)
        self.assertEqual(c.valueForRawValue('1.5'), 1.5)
        self.assertEqual(c.valueForRawValue(2.5), 2.5)
        self.assertEqual(c.valueForRawValue(3), 3.0)


class Record:

    def __init__(self, **record):
        self.record = record

    def hasValueForKey(self, key):
        return key in self.record

    def valueForKey(self, key, default=None):
        return self.record.get(key, default)


class TestDataTable(unittest.TestCase):

    def _testSource(self, name, src, headings, data):
        dataTable = DataTable()
        lines = src.splitlines()
        dataTable.readLines(lines)
        self.assertEqual([c.name() for c in dataTable.headings()], headings)
        for i, values in enumerate(dataTable):
            match = data[i]
            asList = values.asList()
            self.assertEqual(
                asList, match,
                f'{name}: Row {i}: Expected {match!r}, but got {asList!r}')

    def testBasicWithPickle(self):
        DataTable.usePickleCache = True
        self._testBasic()
        self._testBasic()

    def testBasicWithoutPickle(self):
        DataTable.usePickleCache = False
        self._testBasic()

    def _testBasic(self):
        """Simple tests..."""

        # Create table
        t = DataTable()

        # Headings 1
        t = DataTable()
        t.setHeadings([
            TableColumn('name'), TableColumn('age:int'),
            TableColumn('rating:float')])

        # Headings 2
        t = DataTable()
        t.setHeadings(['name', 'age:int', 'rating:float'])

        # Adding and accessing data
        data = [
            ['John', '26', '7.25'],
            ['Mary', 32, 8.5],
            dict(name='Fred', age=28, rating=9.0),
            Record(name='Wilma', age=27, rating=9.5)
        ]
        for obj in data:
            t.append(obj)
        self.assertEqual(t[-4]['name'], 'John')
        self.assertEqual(t[-3]['name'], 'Mary')
        self.assertEqual(t[-2]['name'], 'Fred')
        self.assertEqual(t[-1]['name'], 'Wilma')
        self.assertEqual(
            t[-4].asDict(),
            {'name': 'John', 'age': 26, 'rating': 7.25})
        self.assertEqual(t[-3].asList(), data[-3])
        self.assertEqual(t[-2].asDict(), data[-2])
        self.assertEqual(t[-1].asList(), ['Wilma', 27, 9.5])

        # Printing
        # print(t)

        # Writing file (CSV)
        answer = '''\
name,age,rating
John,26,7.25
Mary,32,8.5
Fred,28,9.0
Wilma,27,9.5
'''
        out = StringIO()
        t.writeFile(out)
        results = out.getvalue()
        self.assertEqual(results, answer,
                         f'\n{results!r}\n{answer!r}\n')

        # Accessing rows
        for row in t:
            self.assertEqual(row['name'], row[0])
            self.assertEqual(row['age'], row[1])
            self.assertEqual(row['rating'], row[2])
            self.assertEqual(sum(1 for item in row), 3)

        # Default type
        t = DataTable(defaultType='int')
        t.setHeadings(list('xyz'))
        t.append([1, 2, 3])
        t.append([4, 5, 6])
        self.assertEqual(t[0]['x'] - t[1]['z'], -5)

    def testBasics(self):
        # Basics
        src = '''\
"x","y,y",z
a,b,c
a,b,"c,d"
"a,b",c,d
"a","b","c"
"a",b,"c"
"a,b,c"
"","",""
"a","",
'''
        headings = ['x', 'y,y', 'z']
        data = [
            ['a', 'b', 'c'],
            ['a', 'b', 'c,d'],
            ['a,b', 'c', 'd'],
            ['a', 'b', 'c'],
            ['a', 'b', 'c'],
            ['a,b,c', '', ''],
            ['', '', ''],
            ['a', '', '']
        ]
        self._testSource('Basics', src, headings, data)

        # Comments
        src = '''\
a:int,b:int
1,2
#3,4
5,6
'''
        headings = ['a', 'b']
        data = [
            [1, 2],
            [5, 6],
        ]
        self._testSource('Comments', src, headings, data)

        # Multiline records
        src = '''\
a
"""Hi
there"""
'''
        headings = ['a']
        data = [
            ['"Hi\nthere"'],
        ]
        self._testSource('Multiline records', src, headings, data)

        # MiddleKit enums
        src = '''\
Class,Attribute,Type,Extras
#Foo,
,what,enum,"Enums=""foo, bar"""
,what,enum,"Enums='foo, bar'"
'''
        headings = 'Class,Attribute,Type,Extras'.split(',')
        data = [
            ['', 'what', 'enum', 'Enums="foo, bar"'],
            ['', 'what', 'enum', "Enums='foo, bar'"],
        ]
        self._testSource('MK enums', src, headings, data)

        # Unfinished multiline record
        try:
            DataTable().readString('a\n"1\n')
        except DataTableError:
            pass  # just what we were expecting
        else:
            raise Exception(
                'Failed to raise exception for unfinished multiline record')

    def testDefaultUsePickleCache(self):
        t = DataTable()
        self.assertIs(t._usePickleCache, True)

    def testCsvWithPickle(self):
        self._testCsv(removePickleCache=False)
        self._testCsv()

    def testCsvWithoutPickle(self):
        self._testCsv(usePickleCache=False)

    def _testCsv(self, usePickleCache=True, removePickleCache=True):
        csvFile = os.path.join(os.path.dirname(__file__), 'Sample.csv')
        try:
            t = DataTable(csvFile, usePickleCache=usePickleCache)
        finally:
            pickleFile = csvFile + '.pickle.cache'
            self.assertIs(os.path.exists(pickleFile), usePickleCache)
            if usePickleCache and removePickleCache:
                os.remove(pickleFile)
        self.assertEqual(t[0][0], 'Video', t[0])

    @unittest.skipIf(cannotReadExcel, "Cannot read Excel files")
    def testExcelWithPickle(self):
        self._testExcel(removePickleCache=False)
        self._testExcel()

    @unittest.skipIf(cannotReadExcel, "Cannot read Excel files")
    def testExcelWithoutPickle(self):
        self._testExcel(usePickleCache=False)

    def _testExcel(self, usePickleCache=True, removePickleCache=True):
        self.assertTrue(DataTable.canReadExcel())
        xlsFile = os.path.join(os.path.dirname(__file__), 'Sample.xls')
        try:
            t = DataTable(xlsFile, usePickleCache=usePickleCache)
        finally:
            pickleFile = xlsFile + '.pickle.cache'
            self.assertIs(os.path.exists(pickleFile), usePickleCache)
            if usePickleCache and removePickleCache:
                os.remove(pickleFile)
        self.assertEqual(t[0][0], 1.0, t[0])
