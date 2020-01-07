import pkg_resources

from PlugIn import PlugIn


class PlugInLoader:

    def __init__(self, app):
        self.app = app

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

    def loadPlugIns(self, plugInNames=None, verbose=None):
        """Load all plug-ins.

        A plug-in allows you to extend the functionality of Webware without
        necessarily having to modify its source. Plug-ins are loaded by
        Application at startup time, just before listening for requests.
        See the docs in `PlugIn` for more info.
        """
        if plugInNames is None:
            plugInNames = self.app.setting('PlugIns')
        if verbose is None:
            verbose = self.app.setting('PrintPlugIns')

        if verbose:
            print('Plug-ins list:', ', '.join(plugInNames))

        entryPoints = {
            entry_point.name: entry_point for entry_point
            in pkg_resources.iter_entry_points('webware.plugins')}

        plugIns = {}
        for name in plugInNames:
            if name in plugIns:
                if verbose:
                    print(f'Plug-in {name} has already been loaded.')
                    continue
            entry_point = entryPoints.get(name)
            if not entry_point:
                if verbose:
                    print(f'Plug-in {name} has not entry point.')
                    continue
            module = entry_point.load()
            plugIn = self.loadPlugIn(name, module, verbose=verbose)
            if plugIn:
                plugIns[name] = plugIn

        if verbose:
            print()

        return plugIns
