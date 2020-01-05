import pkg_resources

from PlugIn import PlugIn


class PlugInLoader(object):

    def __init__(self, app):
        self.app = app
        self._plugIns = {}

    def loadPlugIn(self, name, module, verbose=True):
        """Load and return the given plug-in.

        May return None if loading was unsuccessful (in which case this method
        prints a message saying so). Used by `loadPlugIns` (note the **s**).
        """
        try:
            plugIn = PlugIn(self.app, name, module)
            willNotLoadReason = plugIn.load(verbose=verbose)
            if willNotLoadReason:
                print(f'    Plug-in {name} cannot be loaded because:\n'
                      f'    {willNotLoadReason}')
                return None
            plugIn.install()
        except Exception:
            print()
            print(f'Plug-in {name} raised exception.')
            raise
        return plugIn

    def loadPlugIns(self, plugInNames, verbose=True):
        """Load all plug-ins.

        A plug-in allows you to extend the functionality of Webware without
        necessarily having to modify its source. Plug-ins are loaded by
        Application at startup time, just before listening for requests.
        See the docs in `PlugIn` for more info.
        """
        plugInNames = set(plugInNames)
        plugInNames.add('Webware')
        plugIns = [
            (entry_point.name, entry_point.load())
            for entry_point
            in pkg_resources.iter_entry_points('webware.plugins')
            if entry_point.name in plugInNames
        ]

        if verbose:
            print('Plug-ins list:', ', '.join(
                name for name, _module in plugIns if name != 'Webware'))

        # Now that we have our plug-in list, load them...
        for name, module in plugIns:
            plugIn = self.loadPlugIn(name, module, verbose=verbose)
            if plugIn:
                self._plugIns[name] = plugIn
        if verbose:
            print()
        return self._plugIns
