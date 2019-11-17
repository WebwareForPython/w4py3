"""The RoleUserManager mixin."""

from MiscUtils import NoDefault

from .RoleUser import RoleUser
from .Role import Role


class RoleUserManagerMixIn:
    """Mixin class for mapping names to roles.

    This mixin adds the functionality of keeping a dictionary mapping
    names to role instances. Several accessor methods are provided for this.
    """

    # region Init

    def __init__(self):
        self._roles = {}
        self.initUserClass()

    def initUserClass(self):
        """Invoked by __init__ to set the default user class to RoleUser."""
        self.setUserClass(RoleUser)

    # endregion Init

    # region Roles

    def addRole(self, role):
        if not isinstance(role, Role):
            raise TypeError(f'{role} is not a Role object')
        name = role.name()
        if name in self._roles:
            raise KeyError(f'role name {name!r} already exists')
        self._roles[name] = role

    def role(self, name, default=NoDefault):
        if default is NoDefault:
            return self._roles[name]
        return self._roles.get(name, default)

    def hasRole(self, name):
        return name in self._roles

    def delRole(self, name):
        del self._roles[name]

    def roles(self):
        return self._roles

    def clearRoles(self):
        self._roles = {}

    # endregion Roles
