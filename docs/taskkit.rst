.. module:: TaskKit

.. _taskkit:

TaskKit
=======

TaskKit provides a framework for the scheduling and management of tasks which can be triggered periodically or at specific times. Tasks can also be forced to execute immediately, set on hold or rescheduled with a different period (even dynamically).

To understand how TaskKit works, please read the following quick start article and have a look at the :ref:`reference documentation <ref-taskkit>`. Also, in the "Task" subdirectory of Webware, you will find a real world use of this kit.


Scheduling with Python and Webware
----------------------------------

The Webware for Python web application framework comes with a scheduling plug-in called TaskKit. This quick start guide describes how to use it in your daily work with Webware and also with normal Python programs (slightly updated version of an article contributed by Tom Schwaller in March 2001).

Scheduling periodic tasks is a very common activity for users of a modern operating system. System administrators for example know very well how to start new ``cron`` jobs or the corresponding Windows analogues. So, why does a web application framework like Webware need its own scheduling framework? The answer is simple: Because it knows better how to react to a failed job, has access to internal data structures, which otherwise would have to be exposed to the outside world and last but not least it needs scheduling capabilities anyway (e.g. for session sweeping and other memory cleaning operations).

Webware is developed with the object oriented scripting language Python, so it seemed natural to write a general purpose Python based scheduling framework. One could think that this problem is already solved (remember the Python slogan: batteries included), but strange enough there has not much work been done in this area. The two standard Python modules ``sched.py`` and ``bisect.py`` are way too simple, not really object oriented and also not multithreaded. This was the reason to develop a new scheduling framework, which can not only be used with Webware but also with general purpose Python programs. Unfortunately scheduling has an annoying side effect. The more you delve into the subject the more it becomes difficult.

After some test implementations I discovered the Java scheduling framework of the "Ganymede" network directory management system and took it as a model for the Python implementation. Like any other Webware plug-in the TaskKit is self contained and can be used in other Python projects. This modularity is one of the real strengths of Webware and in sharp contrast to Zope where people tend to think in Zope and not in Python terms. In a perfect world one should be able to use web wrappers (for Zope, Webware, Quixote, ...) around clearly designed Python classes and not be forced to use one framework. Time will tell if this is just a dream or if people will reinvent the "Python wheels" over and over again.


Tasks
-----

The TaskKit implements the three classes ``Scheduler, TaskHandler`` and ``Task``. Let's begin with the simplest one, i.e. Task. It's an abstract base class, from which you have to derive your own task classes by overriding the ``run()``-method like in the following example::

    from time import strftime, localtime
    from TaskKit.Task import Task

    class SimpleTask(Task):

        def run(self):
            print self.name(), strftime("%H:%M:%S", localtime())

``self.name()`` returns the name under which the task was registered by the scheduler. It is unique among all tasks and scheduling tasks with the same name will delete the old task with that name (so beware of that feature!). Another simple example which is used by Webware itself is found in ``Tasks/SessionTask.py``::

    from TaskKit.Task import Task

    class SessionTask(Task):

        def __init__(self, sessions):
            Task.__init__(self)
            self._sessionstore = sessions

        def run(self):
            if self.proceed():
                self._sessionstore.cleanStaleSessions(self)

Here you see the ``proceed()`` method in action. It can be used by long running tasks to check if they should terminate. This is the case when the scheduler or the task itself has been stopped. The latter is achieved with a ``stopTask()`` call which is not recommended though. It's generally better to let the task finish and use the ``unregister()`` and ``disable()`` methods of the task handler. The first really deletes the task after termination while the second only disables its rescheduling. You can still use it afterwards. The implementation of ``proceed()`` is very simple::

    def proceed(self):
        """Check whether this task should continue running.

        Should be called periodically by long tasks to check if the system
        wants them to exit. Returns True if its OK to continue, False if
        it's time to quit.

        """
        return self._handle._isRunning

Take a look at the ``SimpleTask`` class at the end of this article for an example of using ``proceed()``. Another thing to remember about tasks is, that they know nothing about scheduling, how often they will run (periodically or just once) or if they are on hold. All this is managed by the task wrapper class ``TaskHandler``, which will be discussed shortly. Let's look at some more examples first.


Generating static pages
-----------------------

On a high traffic web site (like `slashdot <https://slashdot.org>`_) it's common practice to use semi-static page generation techniques. For example you can generate the entry page as a static page once per minute. During this time the content will not be completely accurate (e.g. the number of comments will certainly increase), but nobody really cares about that. The benefit is a dramatic reduction of database requests. For other pages (like older news with comments attached) it makes more sense to generate static versions on demand. This is the case when the discussion has come to an end, but somebody adds a comment afterwards and implicitly changes the page by this action. Generating a static version will happen very seldom after the "hot phase" when getting data directly out of the database is more appropriate. So you need a periodic task which checks if there are new "dead" stories (e.g. no comments for 2 days) and marks them with a flag for static generation on demand. It should be clear by now, that an integrated Webware scheduling mechnism is very useful for this kind of things and the better approach than external ``cron`` jobs. Let's look a little bit closer at the static generation technique now. First of all we need a ``PageGenerator`` class. To keep the example simple we just write the actual date into a file. In real life you will assemble much more complex data into such static pages.

::

    from time import asctime
    from TaskKit.Task import Task

    html = '''<html>
    <head><title>%s</title></head>
    <body bgcolor="white">
    <h1>%s</h1>
    </body>
    </html>
    '''

    class PageGenerator(Task):

        def __init__(self, filename):
            Task.__init__(self)
            self._filename = filename

        def run(self):
            f = open(self._filename, 'w')
            f.write(html % ('Static Page',  asctime()))
            f.close()

Scheduling
~~~~~~~~~~

That was easy. Now it's time to schedule our task. In the following example you can see how this is accomplished with TaskKit. As a general recommendation you should put all your tasks in a separate folder (with an empty ``__init__.py`` file to make this folder a Python package). First of all we create a new ``Scheduler`` object, start it as a thread and add a periodic page generation object (of type ``PageGenerator``) with the ``addPeriodicAction`` method. The first parameter here is the first execution time (which can be in the future), the second is the period (in seconds), the third an instance of our task class and the last parameter is a unique task name which allows us to find the task later on (e.g. if we want to change the period or put the task on hold).

::

    from time import sleep, time
    from TaskKit.Scheduler import Scheduler
    from Tasks.PageGenerator import PageGenerator

    def main():
        scheduler = Scheduler()
        scheduler.start()
        scheduler.addPeriodicAction(time(), 5, PageGenerator('static.html'), 'PageGenerator')
        sleep(20)
        scheduler.stop()

    if __name__ == '__main__':
        main()

When you fire up this example you will notice that the timing is not 100% accurate. The reason for this seems to be an imprecise ``wait()`` function in the Python ``threading`` module. Unfortunately this method is indispensible because we need to be able to wake up a sleeping scheduler when scheduling new tasks with first execution times smaller than ``scheduler.nextTime()``. This is achieved through the ``notify()`` method, which sets the ``notifyEvent`` (``scheduler._notifyEvent.set()``). On Unix we could use ``sleep`` and a ``signal`` to interrupt this system call, but TaskKit has to be plattform independent to be of any use. But don't worry; this impreciseness is not important for normal usage, because we are talking about scheduling in the minute (not second) range here. Unix ``cron`` jobs have a granularity of one minute, which is a good value for TaskKit too. Of course nobody can stop you starting tasks with a period of one second (but you have been warned that this is not a good idea, except for testing purposes).


Generating static pages again
-----------------------------

Let's refine our example a little bit and plug it into Webware. We will write a Python servlet which loks like this:

.. raw:: html

    <div style="font-family: sans-serif;font-size:12px">
    <table><tr><td class="center">
    <form method="post">
    <input type="submit" name="_action_" value="Generate">
    <input type="text" name="filename" value="static.html" size="16"> every
    <input type="text" name="seconds" value="60" size="4"> seconds</form>

    <table style="width:28em;margin-top:6px">
    <tr style="background-color:#009">
    <th colspan="2" style="color:#fff">Task List</th></tr>
    <tr style="background-color:#ddd">
    <td><b>Task Name</b></td>
    <td><b>Period</b></td></tr>
    <tr><td>SessionSweeper</td><td>360</td></tr>
    <tr><td>PageGenerator for static3.html</td><td>30</td></tr>
    <tr><td>PageGenerator for static1.html</td><td>60</td></tr>
    <tr><td>PageGenerator for static2.html</td><td>120</td></tr>
    </table>
    </td></tr></table>
    </div>

When you click on the ``Generate`` button a new periodic ``PageGenerator`` task will be added to the Webware scheduler. Remember that this will generate a static page ``static.html`` every 60 seconds (if you use the default values). The new task name is ``"PageGenerator for filename"``, so you can use this servlet to change the settings of already scheduled tasks (by rescheduling) or add new ``PageGenerator`` tasks with different filenames. This is quite useless here, but as soon as you begin to parametrize your ``Task`` classes this approach can become quite powerful (consider for example a mail reminder form or collecting news from different news channels as periodic tasks with user defined parameters). In any case, don't be shy and contribute other interesting examples (the sky's the limit!).

Finally we come to the servlet code, which should be more or less self explanatory, except for the ``_action_`` construct which is very well explained in the Webware documentation though (just in case you forgot that). ``app.taskManager()`` gives you the Webware scheduler, which can be used to add new tasks. In real life you will have to make the scheduling information persistent and reschedule all tasks after a Webware server restart because it would be quite annoying to enter this data again and again.

::

    from time import time
    from ExamplePage import ExamplePage
    from Tasks.PageGenerator import PageGenerator

    class Schedule(ExamplePage):

        def writeContent(self):
            self.write('''
                <center><form method="post">
                <input type="submit" name="_action_ value=Generate">
                <input type="text" name="filename" value="static.html" size="16"> every
                <input type="text" name="seconds" value="60" size="4"> seconds
                </form>
                <table style="width:28em;margin-top:6px">
                <tr style="background-color:009">
                <th colspan="2" style="color:#fff">Task List</th></tr>
                <tr style="background-color:#ddd">
                <td><b>Task Name</b></td>
                <td><b>Period</b></td></tr>''')
            for taskname, handler in self.application().taskManager().scheduledTasks().items():
                self.write('''
                    <tr><td>%s</td><td>%s</td></tr>''' % (taskname, handler.period()))
            self.write('''
                </table></center>''')

        def generate(self, trans):
            app = self.application()
            tm = app.taskManager()
            req = self.request()
            if req.hasField('filename') and req.hasField('seconds'):
                self._filename = req.field('filename')
                self._seconds = int(req.field('seconds'))
                task = PageGenerator(app.serverSidePath('Examples/' + self._filename))
                taskname = 'PageGenerator for ' + self._filename
                tm.addPeriodicAction(time(), self._seconds, task, taskname)
            self.writeBody()

        def methodNameForAction(self, name):
            return name.lower()

        def actions(self):
            return ExamplePage.actions(self) + ['generate']


The Scheduler
-------------

Now it's time to take a closer look at the ``Scheduler`` class itself. As you have seen in the examples above, writing tasks is only a matter of overloading the ``run()`` method in a derived class and adding it to the scheduler with ``addTimedAction, addActionOnDemand, addDailyAction`` or ``addPeriodicAction``. The scheduler will wrap the Task in a ``TaskHandler`` structure which knows all the scheduling details and add it to its ``_scheduled`` or ``_onDemand`` dictionaries. The latter is populated by ``addActionOnDemand`` and contains tasks which can be called any time by ``scheduler.runTaskNow('taskname')`` as you can see in the following example. After that the task has gone.

::

    scheduler = Scheduler()
    scheduler.start()
    scheduler.addActionOnDemand(SimpleTask(), 'SimpleTask')
    sleep(5)
    print "Demanding SimpleTask"
    scheduler.runTaskNow('SimpleTask')
    sleep(5)
    scheduler.stop()

If you need a task more than one time it's better to start it regularly with one of the ``add*Action`` methods first. It will be added to the ``_scheduled`` dictionary. If you do not need the task for a certain time disable it with ``scheduler.disableTask('taskname')`` and enable it later with ``scheduler.enableTask('taskname')``. There are some more methods (e.g. ``demandTask(), stopTask(), ...``) in the ``Scheduler`` class which are all documented by docstrings. Take a look at them and write your own examples to understand the methods.

When a periodic task is scheduled it is added in a wrapped version to the ``_scheduled`` dictionary first. The (most of the time sleeping) scheduler thread always knows when to wake up and start the next task whose wrapper is moved to the ``_runnning`` dictionary. After completion of the task thread the handler reschedules the task (by putting it back from ``_running`` to ``_scheduled``), calculating the next execution time ``nextTime`` and possibly waking up the scheduler. It is important to know that you can manipulate the handle while the task is running, e.g. change the period or call ``runOnCompletion`` to request that a task be re-run after its current completion. For normal use you will probably not need the handles at all, but the more you want to manipulate the task execution, the more you will appreciate the TaskHandler API. You get all the available handles from the scheduler with the ``running('taskname'), scheduled('taskname')`` and ``onDemand('taskname')`` methods.

In our last example which was contributed by Jay Love, who debugged, stress tested and contributed a lot of refinements to TaskKit, you see how to write a period modifying Task. This is quite weird but shows the power of handle manipulations. The last thing to remember is that the scheduler does not start a separate thread for each periodic task. It uses a thread for each task run instead and at any time keeps the number of threads as small as possible.

::

    class SimpleTask(Task):

        def run(self):
            if self.proceed():
                print self.name(), time()
                print "Increasing period"
                self.handle().setPeriod(self.handle().period() + 2)
            else:
                print "Should not proceed", self.name()

As you can see, the TaskKit framework is quite sophisticated and will hopefully be used by many people from the Python community. If you have further question, please feel free to ask them on the Webware mailing list.


Credit
------

Authors: Tom Schwaller, Jay Love

Based on code from the Ganymede Directory Management System written by Jonathan Abbey.
