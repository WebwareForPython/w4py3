import os
import time
import shutil
import tempfile
import unittest

from MiscUtils import PickleCache as pc


class TestPickleCache(unittest.TestCase):

    def setUp(self):
        self._tempDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tempDir, ignore_errors=True)

    @staticmethod
    def remove(filename):
        try:
            os.remove(filename)
        except OSError:
            pass

    def testTwoIterations(self):
        iterations = 2
        for _iteration in range(iterations):
            self.testOneIteration()

    def testOneIteration(self):
        sourcePath = self._sourcePath = os.path.join(self._tempDir, 'foo.dict')
        picklePath = self._picklePath = pc.PickleCache().picklePath(sourcePath)
        self.remove(picklePath)  # make sure we're clean
        data = self._data = dict(x=1)
        self.writeSource()
        try:
            # test 1: no pickle cache yet
            self.assertTrue(pc.readPickleCache(sourcePath) is None)
            self.writePickle()
            # test 2: correctness
            self.assertEqual(pc.readPickleCache(sourcePath), data)
            # test 3: wrong pickle version
            self.assertTrue(
                pc.readPickleCache(sourcePath, pickleProtocol=1) is None)
            self.writePickle()  # restore
            # test 4: wrong data source
            self.assertTrue(
                pc.readPickleCache(sourcePath, source='notTest') is None)
            self.writePickle()  # restore
            # test 5: wrong Python version
            v = list(pc.versionInfo)
            v[-1] += 1  # increment serial number
            v, pc.versionInfo = pc.versionInfo, tuple(v)
            try:
                self.assertTrue(pc.readPickleCache(sourcePath) is None)
                self.writePickle()  # restore
            finally:
                pc.versionInfo = v
            # test 6: source is newer
            self.remove(picklePath)
            self.writePickle()
            # we have to allow for the granularity of getmtime()
            # (see the comment in the docstring of PickleCache.py)
            time.sleep(1.25)
            self.writeSource()
            self.assertTrue(pc.readPickleCache(sourcePath) is None)
            self.writePickle()  # restore
        finally:
            self.remove(sourcePath)
            self.remove(picklePath)

    def writeSource(self):
        with open(self._sourcePath, 'w') as f:
            f.write(str(self._data))

    def writePickle(self):
        self.assertFalse(os.path.exists(self._picklePath))
        pc.writePickleCache(self._data, self._sourcePath, source='test')
        self.assertTrue(os.path.exists(self._picklePath))
