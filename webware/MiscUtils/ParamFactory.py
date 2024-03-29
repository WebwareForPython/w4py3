"""ParamFactory.py

A factory for creating cached, parametrized class instances.
"""

from threading import Lock


class ParamFactory:

    def __init__(self, klass, **extraMethods):
        self.lock = Lock()
        self.cache = {}
        self.klass = klass
        for name, func in list(extraMethods.items()):
            setattr(self, name, func)

    def __call__(self, *args):
        with self.lock:
            if args in self.cache:
                value = self.cache[args]
            else:
                value = self.klass(*args)
                self.cache[args] = value
        return value

    def allInstances(self):
        return list(self.cache.values())
