"""The HierRole class."""

from .Role import Role


class HierRole(Role):
    """HierRole is a hierarchical role.

    It points to its parent roles. The hierarchy cannot have cycles.
    """

    def __init__(self, name, description=None, superRoles=None):
        Role.__init__(self, name, description)
        if superRoles is None:
            superRoles = []
        for role in superRoles:
            if not isinstance(role, Role):
                raise TypeError(f'{role} is not a Role object')
        self._superRoles = superRoles[:]

    def playsRole(self, role):
        """Check whether the receiving role plays the role that is passed in.

        This implementation provides for the inheritance supported by HierRole.
        """
        return self == role or any(
            superRole.playsRole(role) for superRole in self._superRoles)
