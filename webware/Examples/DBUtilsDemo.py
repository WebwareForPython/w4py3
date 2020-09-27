from collections import Counter

from MiscUtils.Configurable import Configurable
from .ExamplePage import ExamplePage


class DBConfig(Configurable):
    """Database configuration."""

    def defaultConfig(self):
        return {
            'dbapi': 'sqlite3',
            'database': 'demo.db',
            # 'dbapi': 'pg',
            # 'database': 'demo',
            # 'user': 'demo',
            # 'password': 'demo',
            'mincached': 5,
            'maxcached': 25
        }

    def configFilename(self):
        return 'Configs/Database.config'


# the database tables used in this example:
tables = (
    '''seminars (
        id varchar(4) primary key,
        title varchar(64) unique not null,
        cost money,
        places_left smallint)''',
    '''attendees (
        name varchar(64) not null,
        seminar varchar(4),
        paid boolean,
        primary key(name, seminar),
        foreign key (seminar) references seminars(id) on delete cascade)''')


class DBUtilsDemo(ExamplePage):
    """Example page for the DBUtils package."""

    # Initialize the buttons
    _actions = []
    _buttons = []
    for action in (
            'create tables', 'list seminars', 'list attendees',
            'add seminar', 'add attendee'):
        value = action.capitalize()
        action = action.split()
        action[1] = action[1].capitalize()
        action = ''.join(action)
        _actions.append(action)
        _buttons.append(
            f'<input name="_action_{action}" type="submit" value="{value}">')
    _buttons = tuple(_buttons)

    def initDb(self):
        """Create an instance of the DBUtils class.

        You can also do this in the contextInitialize() function
        in the __init__.py script of your application context.
        """
        app = self.application()
        try:
            dbPool = app.dbPool
        except AttributeError:
            # If a database connection pool has not yet been created,
            # create one and store it in the application as a singleton.
            config = DBConfig().config()
            if config.get('maxcached', None) is None:
                dbModName = 'persistent'
            else:
                dbModName = 'pooled'
            dbClsName = dbModName.capitalize()
            dbApiName = config.pop('dbapi', 'pg')
            if dbApiName == 'pg':  # use the PyGreSQL classic DB API
                dbModName += '_pg'
                dbClsName += 'Pg'
                if 'database' in config:
                    config['dbname'] = config['database']
                    del config['database']
                if 'password' in config:
                    config['passwd'] = config['password']
                    del config['password']
            else:  # use a DB-API 2 compliant module
                dbModName += '_db'
                dbClsName += 'DB'
            app.dbApi = app.dbPool = app.dbStatus = None
            try:
                app.dbApi = __import__(dbApiName)
                dbmod = getattr(__import__('dbutils.' + dbModName), dbModName)
                if dbApiName != 'pg':
                    config['creator'] = app.dbApi
                app.dbPool = getattr(dbmod, dbClsName)(**config)
                if hasattr(app.dbPool, 'close'):
                    app.addShutDownHandler(app.dbPool.close)
            except Exception as error:
                app.dbStatus = str(error)
            dbPool = app.dbPool
        self.dbApi = app.dbApi
        self.dbPool = dbPool
        self.dbStatus = app.dbStatus
        self.hasQuery = dbPool and dbPool.__class__.__name__.endswith('Pg')

    def title(self):
        return "DBUtils Demo"

    def actions(self):
        return super().actions() + self._actions

    def awake(self, transaction):
        super().awake(transaction)
        self.initDb()
        self._output = []

    def postAction(self, actionName):
        self.writeBody()
        del self._output
        super().postAction(actionName)

    def output(self, s):
        self._output.append(s)

    def outputMsg(self, msg, error=False):
        color = 'red' if error else 'green'
        self._output.append(f'<p style="color:{color}">{msg}</p>')

    def connection(self, shareable=True):
        if self.dbStatus:
            error = self.dbStatus
        else:
            try:
                pooledDb = self.dbPool.__class__.__name__ == 'PooledDB'
                return self.dbPool.connection(
                    shareable) if pooledDb else self.dbPool.connection()
            except self.dbApi.Error as error:
                error = str(error)
            except Exception:
                error = 'Cannot connect to the database.'
        self.outputMsg(error, True)

    def dedicatedConnection(self):
        return self.connection(False)

    def fixParamStyle(self, query):
        """Adapt parameter style to tbe used DB-API."""
        paramstyle = getattr(self.dbApi, 'paramstyle', 'format')
        if paramstyle in ('format', 'pyformat'):
            query = query.replace('?', '%s')
        return query

    def createTables(self):
        db = self.dedicatedConnection()
        if not db:
            return
        for table in tables:
            self._output.append(
                f'<p>Creating the following table:</p><pre>{table}</pre>')
            ddl = 'create table ' + table
            try:
                if self.hasQuery:
                    db.query(ddl)
                else:
                    db.cursor().execute(ddl)
                    db.commit()
            except self.dbApi.Error as error:
                if self.dbApi.__name__ != 'pg':
                    db.rollback()
                self.outputMsg(error, True)
            else:
                self.outputMsg('The table was successfully created.')
        db.close()

    def listSeminars(self):
        ids = self.request().field('id', None)
        if ids:
            if not isinstance(ids, list):
                ids = [ids]
            cmd = 'delete from seminars where id in ({})'.format(
                self.fixParamStyle(','.join('?' * len(ids))))
            db = self.dedicatedConnection()
            if not db:
                return
            try:
                if self.hasQuery:
                    db.query('begin')
                    db.query_formatted(cmd, ids)
                    db.query('end')
                else:
                    db.cursor().execute(cmd, ids)
                    db.commit()
            except self.dbApi.Error as error:
                try:
                    if self.hasQuery:
                        db.query('end')
                    else:
                        db.rollback()
                except Exception:
                    pass
                self.outputMsg(error, True)
                return
            else:
                self.outputMsg(f'Entries deleted: {len(ids)}')
        db = self.connection()
        if not db:
            return
        query = ('select id, title, cost, places_left'
                 ' from seminars order by title')
        try:
            if self.hasQuery:
                result = db.query(query).getresult()
            else:
                cursor = db.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
        except self.dbApi.Error as error:
            self.outputMsg(error, True)
            return
        if not result:
            self.outputMsg('There are no seminars in the database.', True)
            return
        wr = self.output
        button = self._buttons[1].replace('List seminars', 'Delete')
        wr('<h4>List of seminars in the database:</h4>')
        wr('<form action=""><table class="NiceTable">'
           '<tr><th>ID</th><th>Seminar title</th><th>Cost</th>'
           f'<th>Places left</th><th>{button}</th></tr>')
        for seminar, title, cost, places in result:
            if places is None:
                places = 'unlimited'
            if not cost:
                cost = 'free'
            wr(f'<tr><td>{seminar}</td><td>{title}</td>'
               f'<td align="right">{cost}</td><td align="right">{places}</td>'
               '<td align="center"><input type="checkbox" name="id"'
               f' value="{seminar}"></td></tr>')
        wr('</table></form>')

    def listAttendees(self):
        ids = self.request().field('id', None)
        if ids:
            if not isinstance(ids, list):
                ids = [ids]
            fixParams = self.fixParamStyle
            places = Counter(ids)
            cmds = [('delete from attendees'
                     " where seminar||':'||name in ({})".format(
                        fixParams(','.join('?' * len(ids)))), ids),
                    *((fixParams('update seminars'
                                 ' set places_left=places_left+? where id=?'),
                       (n, i.split(':', 1)[0])) for i, n in places.items())]
            db = self.dedicatedConnection()
            if not db:
                return
            try:
                if self.hasQuery:
                    db.query('begin')
                    for cmd, values in cmds:
                        db.query_formatted(cmd, values)
                    db.query('end')
                else:
                    for cmd, values in cmds:
                        db.cursor().execute(cmd, values)
                    db.commit()
            except self.dbApi.Error as error:
                if self.hasQuery:
                    db.query('end')
                else:
                    db.rollback()
                self.outputMsg(error, True)
                return
            else:
                self.outputMsg(f'Entries deleted: {len(ids)}')
        db = self.connection()
        if not db:
            return
        query = ('select a.name, s.id, s.title,'
                 ' a.paid from attendees a,seminars s'
                 ' where s.id=a.seminar order by a.name, s.title')
        try:
            if self.hasQuery:
                result = db.query(query).getresult()
            else:
                cursor = db.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
        except self.dbApi.Error as error:
            self.outputMsg(error, True)
            return
        if not result:
            self.outputMsg('There are no attendees in the database.', True)
            return
        wr = self.output
        button = self._buttons[2].replace('List attendees', 'Delete')
        wr('<h4>List of attendees in the database:</h4>')
        wr('<form action="">'
           '<table class="NiceTable">'
           '<tr><th>Name</th><th>Seminar</th><th>Paid</th>'
           f'<th>{button}</th></tr>')
        for name, seminar, title, paid in result:
            fullId = f'{seminar}:{name}'
            paid = 'Yes' if paid else 'No'
            wr(f'<tr><td>{name}</td>'
               f'<td>{title}</td>'
               f'<td align="center">{paid}</td>'
               '<td align="center">'
               f'<input type="checkbox" name="id" value="{fullId}"></td></tr>')
        wr('</table></form>')

    def addSeminar(self):
        wr = self.output
        wr('<h4>Add a seminar entry to the database:</h4>')
        wr('<form action=""><table>'
           '<tr><th>ID</th><td><input name="id" type="text"'
           ' size="4" maxlength="4"></td></tr>'
           '<tr><th>Title</th><td><input name="title" type="text"'
           ' size="40" maxlength="64"></td></tr>'
           '<tr><th>Cost</th><td><input name="cost" type="text"'
           ' size="20" maxlength="20"></td></tr>'
           '<tr><th>Places</th><td><input name="places" type="text"'
           ' size="20" maxlength="20"></td></tr>'
           f'<tr><td colspan="2" align="right">{self._buttons[3]}</td></tr>'
           '</table></form>')
        request = self.request()
        if not request.hasField('id'):
            return
        values = [request.field(name, '').strip()
                  for name in ('id', 'title', 'cost', 'places')]
        if not values[0] or not values[1]:
            self.outputMsg('You must enter a seminar ID and a title!')
            return
        if not values[2]:
            values[2] = None
        if not values[3] or not values[3].isdigit():
            values[3] = None
        db = self.dedicatedConnection()
        if not db:
            return
        cmd = self.fixParamStyle('insert into seminars values (?,?,?,?)')
        try:
            if self.hasQuery:
                db.query('begin')
                db.query_formatted(cmd, values)
                db.query('end')
            else:
                db.cursor().execute(cmd, values)
                db.commit()
        except self.dbApi.Error as error:
            if self.hasQuery:
                db.query('end')
            else:
                db.rollback()
            self.outputMsg(error, True)
        else:
            self.outputMsg(f'"{values[1]}" added to seminars.')
        db.close()

    def addAttendee(self):
        db = self.connection()
        if not db:
            return
        query = ('select id, title from seminars'
                 ' where places_left is null or places_left>0 order by title')
        try:
            if self.hasQuery:
                result = db.query(query).getresult()
            else:
                cursor = db.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
        except self.dbApi.Error as error:
            self.outputMsg(error, True)
            return
        if not result:
            self.outputMsg('You have to define seminars first.')
            return
        sem = ''.join(('<select name="seminar" size="1">',
                       *(f'<option value="{id}">{title}</option>'
                         for id, title in result), '</select>'))
        wr = self.output
        wr('<h4>Add an attendee entry to the database:</h4>')
        wr('<form action=""><table>'
           '<tr><th>Name</th><td><input name="name" type="text" '
           'size="40" maxlength="64"></td></tr>'
           f'<tr><th>Seminar</th><td>{sem}</td></tr>'
           '<tr><th>Paid</th>'
           '<td><input type="radio" name="paid" value="1">Yes '
           '<input type="radio" name="paid" value="0" checked="checked">No'
           '</td></tr><tr><td colspan="2" align="right">'
           f'{self._buttons[4]}</td></tr></table></form>')
        request = self.request()
        if not request.hasField('name'):
            return
        values = []
        for name in ('name', 'seminar', 'paid'):
            values.append(request.field(name, '').strip())
        if not values[0] or not values[1]:
            self.outputMsg('You must enter a name and a seminar!')
            return
        db = self.dedicatedConnection()
        if not db:
            return
        fixParams = self.fixParamStyle
        try:
            if self.hasQuery:
                db.query('begin')
                cmd = fixParams(
                    'update seminars set places_left=places_left-1 where id=?')
                db.query_formatted(cmd, (values[1],))
                cmd = fixParams('select places_left from seminars where id=?')
                if (db.query_formatted(
                        cmd, (values[1],)).onescalar() or 0) < 0:
                    raise self.dbApi.Error("No more places left.")
                cmd = fixParams('insert into attendees values (?,?,?)')
                db.query_formatted(cmd, values)
                db.query('end')
            else:
                cursor = db.cursor()
                cmd = fixParams(
                    'update seminars set places_left=places_left-1 where id=?')
                cursor.execute(cmd, (values[1],))
                cmd = fixParams('select places_left from seminars where id=?')
                cursor.execute(cmd, (values[1],))
                if (cursor.fetchone()[0] or 0) < 0:
                    raise self.dbApi.Error("No more places left.")
                cmd = fixParams('insert into attendees values (?,?,?)')
                db.cursor().execute(cmd, values)
                cursor.close()
                db.commit()
        except self.dbApi.Error as error:
            if self.hasQuery:
                db.query('end')
            else:
                db.rollback()
            self.outputMsg(error, True)
        else:
            self.outputMsg(f'{values[0]} added to attendees.')
        db.close()

    def writeContent(self):
        wr = self.writeln
        if self._output:
            wr('\n'.join(self._output),
               '<p><a href="DBUtilsDemo">Back</a></p>')
        else:
            wr(f'<h2>Welcome to the {self.title()}!</h2>')
            wr('<p>This example shows how to use the'
               ' <a href="https://webwareforpython.github.io/DBUtils/">'
               'DBUtils</a> library with Webware for Python'
               ' as a safe and performant way to access a database.</p>')
            if self.dbPool and self.dbApi:
                wr(f'<h4>We are using {self.dbPool.__class__.__name__}'
                   f' with the {self.dbApi.__name__} database module.</h4>')
            else:
                wr('<p>No database module configured.</p>')
                wr(f'<p style="color:red">{self.dbStatus}</p>')
            wr(f'<p>Configuration: {DBConfig().config()}</p>')
            wr('<p>You can create a database configuration file to experiment'
               ' with different databases and DBUtils configurations.</p>')
            wr('<h3>Play with the demo database</h3>')
            wr('<p>This example uses a small demo database '
               'designed to track the attendees for a series of seminars '
               '(see <a href="http://www.linuxjournal.com/article/2605">"'
               'The Python DB-API"</a> by Andrew Kuchling).</p>')
            wr('<form action="">'
               '<p>{} (create the needed database tables first)</p>'
               '<p>{} {} (list all database entries)</p>'
               '<p>{} {} (add entries)</p>'
               '</form>'.format(*self._buttons))
