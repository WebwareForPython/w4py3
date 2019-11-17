import sys
import time
from glob import glob
try:
    from cProfile import Profile
except ImportError:
    from profile import Profile

from MiscUtils.CSVParser import CSVParser


class BenchCSVParser:

    def __init__(self, profile=False, runTestSuite=True):
        self.parse = CSVParser().parse
        self._shouldProfile = profile
        self._shouldRunTestSuite = runTestSuite
        self._iterations = 1000

    def main(self):
        print('Benchmarking CSVParser ...')
        print()
        if len(sys.argv) > 1 and sys.argv[1].lower().startswith('prof'):
            self._shouldProfile = True
        if self._shouldRunTestSuite:
            print('Running test suite ...')
            from unittest import main
            main('MiscUtils.Tests.TestCSVParser', exit=False)
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
            lines = f.readlines()
        for line in lines:
            for _iteration in range(self._iterations):
                # we duplicate lines to reduce the overhead of the loop
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)
                self.parse(line)


if __name__ == '__main__':
    BenchCSVParser().main()
