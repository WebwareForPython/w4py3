"""PickleCache.py

PickleCache provides tools for keeping fast-loading cached versions of
files so that subsequent loads are faster. This is similar to how Python
silently caches .pyc files next to .py files.

The typical scenario is that you have a type of text file that gets
"translated" to Pythonic data (dictionaries, tuples, instances, ints,
etc.). By caching the Python data on disk in pickle format, you can
avoid the expensive translation on subsequent reads of the file.

Two real life cases are MiscUtils.DataTable, which loads and represents
comma-separated files, and the separate MiddleKit plug-in which has an
object model file. So for examples on using this module, load up the
following files and search for "Pickle"::

    MiscUtils/DataTable.py
    MiddleKit/Core/Model.py

The cached file is named the same as the original file with
'.pickle.cache' suffixed. The utility of '.pickle' is to denote the file
format and the utility of '.cache' is to provide ``*.cache`` as a simple
pattern that can be removed, ignored by backup scripts, etc.

The treatment of the cached file is silent and friendly just like
Python's approach to .pyc files. If it cannot be read or written for
various reasons (cache is out of date, permissions are bad, wrong python
version, etc.), then it will be silently ignored.

GRANULARITY

In constructing the test suite, I discovered that if the source file is
newly written less than 1 second after the cached file, then the fact
that the source file is newer will not be detected and the cache will
still be used. I believe this is a limitation of the granularity of
os.path.getmtime(). If anyone knows of a more granular solution, please
let me know.

This would only be a problem in programmatic situations where the source
file was rapidly being written and read. I think that's fairly rare.

SEE ALSO
    https://docs.python.org/3/library/pickle.html
"""

import os
import sys
from time import sleep
from pprint import pprint
try:
    from pickle import load, dump, HIGHEST_PROTOCOL as maxPickleProtocol
except ImportError:
    from pickle import load, dump, HIGHEST_PROTOCOL as maxPickleProtocol

verbose = False

# force version_info into a simple tuple
versionInfo = tuple(sys.version_info)


class PickleCache:
    """Abstract base class for PickleCacheReader and PickleCacheWriter."""

    _verbose = verbose

    def picklePath(self, filename):
        return filename + '.pickle.cache'


class PickleCacheReader(PickleCache):

    def read(self, filename,
             pickleProtocol=None, source=None, verbose=None):
        """Read data from pickle cache.

        Returns the data from the pickle cache version of the filename,
        if it can read. Otherwise returns None, which also indicates
        that writePickleCache() should be subsequently called after
        the original file is read.
        """
        if pickleProtocol is None or pickleProtocol < 0:
            pickleProtocol = maxPickleProtocol
        if verbose is None:
            v = self._verbose
        else:
            v = verbose
        if v:
            print('>> PickleCacheReader.read() - verbose is on')
        if not filename:
            raise ValueError('Missing filename')

        if not os.path.exists(filename):
            if v:
                print(f'Cannot find {filename!r}.')
            open(filename)  # to get a properly constructed IOError

        shouldDeletePickle = False
        data = None

        picklePath = self.picklePath(filename)
        if os.path.exists(picklePath):
            if os.path.getmtime(picklePath) < os.path.getmtime(filename):
                if v:
                    print('Cache is out of date.')
                shouldDeletePickle = True
            else:
                try:
                    if v:
                        print(f'About to open for read {picklePath!r}.')
                    file = open(picklePath, 'rb')
                except IOError as e:
                    if v:
                        print('Cannot open cache file:'
                              f' {e.__class__.__name__}: {e}.')
                else:
                    try:
                        if v:
                            print('about to load')
                        d = load(file)
                    except EOFError:
                        if v:
                            print('EOFError - not loading')
                        shouldDeletePickle = True
                    except Exception as exc:
                        print(f'WARNING: {self.__class__.__name__}:'
                              f' {exc.__class__.__name__}: {exc}')
                        shouldDeletePickle = True
                    else:
                        file.close()
                        if v:
                            print('Finished reading.')
                        if not isinstance(d, dict):
                            raise TypeError(f'Expected dict, but got: {d!r}')
                        for key in ('source', 'data',
                                    'pickle protocol', 'python version'):
                            if key not in d:
                                raise ValueError(f'{key} not found')
                        if source and d['source'] != source:
                            if v:
                                print(f'Not from required source ({source}):'
                                      f" {d['source']}.")
                            shouldDeletePickle = True
                        elif d['pickle protocol'] != pickleProtocol:
                            if v:
                                print('Pickle protocol'
                                      f" ({d['pickle protocol']})"
                                      ' does not match expected'
                                      f' ({pickleProtocol}).')
                            shouldDeletePickle = True
                        elif d['python version'] != versionInfo:
                            if v:
                                print('Python version'
                                      " {d['python version']}"
                                      ' does not match current'
                                      ' {versionInfo}')
                            shouldDeletePickle = True
                        else:
                            if v:
                                print('All tests pass, accepting data.')
                                if v > 1:
                                    print('Display full dict:')
                                    pprint(d)
                            data = d['data']

        # Delete the pickle file if suggested by previous conditions
        if shouldDeletePickle:
            try:
                if v:
                    print('Attempting to remove pickle cache file.')
                os.remove(picklePath)
            except OSError as exc:
                if v:
                    print(f'Failed to remove: {exc.__class__.__name__}: {exc}')

        if v:
            print('Done reading data.')
            print()

        return data


class PickleCacheWriter(PickleCache):

    _writeSleepInterval = 0.1

    def write(self, data, filename,
              pickleProtocol=None, source=None, verbose=None):
        if pickleProtocol is None or pickleProtocol < 0:
            pickleProtocol = maxPickleProtocol
        if verbose is None:
            v = self._verbose
        else:
            v = verbose
        if v:
            print('>> PickleCacheWriter.write() - verbose is on.')
        if not filename:
            raise ValueError('Missing filename')
        sourceTimestamp = os.path.getmtime(filename)

        picklePath = self.picklePath(filename)
        d = {
            'source': source,
            'python version': versionInfo,
            'pickle protocol': pickleProtocol,
            'data': data,
        }
        if v > 1:
            print('Display full dict:')
            pprint(d)
        try:
            if v:
                print('About to open for write %r.' % picklePath)
            pickleFile = open(picklePath, 'wb')
        except IOError as e:
            if v:
                print(f'error. not writing. {e.__class__.__name__}: {e}')
        else:
            while True:
                dump(d, pickleFile, pickleProtocol)
                pickleFile.close()
                # Make sure the cache has a newer timestamp, otherwise the
                # cache will just get ignored and rewritten next time.
                if os.path.getmtime(picklePath) == sourceTimestamp:
                    if v:
                        print('Timestamps are identical, sleeping'
                              f' {self._writeSleepInterval:%0.2f} seconds.')
                    sleep(self._writeSleepInterval)
                    pickleFile = open(picklePath, 'wb')
                else:
                    break

        if v:
            print('Done writing data.')
            print()


# Define module level convenience functions:
_reader = PickleCacheReader()
readPickleCache = _reader.read
_writer = PickleCacheWriter()
writePickleCache = _writer.write
