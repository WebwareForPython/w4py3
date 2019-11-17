#!/usr/bin/env python3

import sys
import time
from glob import glob
try:
    from cProfile import Profile
except ImportError:
    from profile import Profile

from MiscUtils.DataTable import DataTable


class BenchDataTable:

    def __init__(self, profile=False, runTestSuite=True):
        self._shouldProfile = profile
        self._shouldRunTestSuite = runTestSuite
        self._iterations = 1000

    def main(self):
        print('Benchmarking DataTable ...')
        print()
        if len(sys.argv) > 1 and sys.argv[1].lower().startswith('prof'):
            self._shouldProfile = True
        if self._shouldRunTestSuite:
            print('Running test suite ...')
            from unittest import main
            main('MiscUtils.Tests.TestDataTable', exit=False)
        start = time.time()
        if self._shouldProfile:
            prof = Profile()
            prof.runcall(self._main)
            filename = f'{self.__class__.__name__}.pstats'
            prof.dump_stats(filename)
            print('Wrote', filename)
        else:
            self._main()
        duration = time.time() - start
        print(f'{duration:.1f} secs')

    def _main(self):
        print()
        for name in glob('Sample*.csv'):
            print("Benchmark using", name, "...")
            self.benchFileNamed(name)

    def benchFileNamed(self, name):
        with open(name) as f:
            contents = f.read()
        for _iteration in range(self._iterations):
            # we duplicate lines to reduce the overhead of the loop
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)
            dt = DataTable()
            dt.readString(contents)


if __name__ == '__main__':
    BenchDataTable().main()
