import unittest

from TaskKit.Scheduler import Scheduler


class TaskKitTest(unittest.TestCase):

    def setUp(self):
        self._scheduler = Scheduler()

    def testSchedulerStarts(self):
        scheduler = self._scheduler
        scheduler.start()

    def tearDown(self):
        self._scheduler.stop()
        self._scheduler = None
