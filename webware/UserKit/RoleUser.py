"""The RoleUser class."""

from .User import User


class RoleUser(User):
    """In conjunction with Role, provides role-based users and security.

    See the doc for playsRole() for an example.

    Note that this class plays nicely with both Role and HierRole,
    e.g., no "HierRoleUser" is needed when making use of HierRoles.

    See also:
      * class Role
      * class HierRole
    """

    # region Init

    def __init__(self, manager=None, name=None, password=None):
        User.__init__(self, manager, name, password)
        self._roles = []
        self._rolesByName = {}

    # endregion Init

    # region Accessing roles

    def roles(self):
        """Return a direct list of the user's roles.

        Do not modify.
        """
        return self._roles

    def setRoles(self, listOfRoles):
        """Set all the roles for the user.

        Each role in the list may be a valid role name or a Role object.

        Implementation note: depends on addRoles().
        """
        self._roles = []
        self.addRoles(listOfRoles)

    def addRoles(self, listOfRoles):
        """Add additional roles for the user.

        Each role in the list may be a valid role name or a Role object.
        """
        start = len(self._roles)
        self._roles.extend(listOfRoles)

        # Convert names to role objects and update self._rolesByName
        index = start
        numRoles = len(self._roles)
        while index < numRoles:
            role = self._roles[index]
            if isinstance(role, str):
                role = self._manager.roleForName(role)
                self._roles[index] = role
            self._rolesByName[role.name()] = role
            index += 1

    def playsRole(self, roleOrName):
        """Check whether the user plays the given role.

        More specifically, if any of the user's roles return true for
        role.playsRole(otherRole), this method returns True.

        The application of this popular method often looks like this:
            if user.playsRole('admin'):
                self.displayAdminMenuItems()
        """
        if isinstance(roleOrName, str):
            roleOrName = self._manager.roleForName(roleOrName)
        return any(role.playsRole(roleOrName) for role in self._roles)

    # endregion Accessing roles
