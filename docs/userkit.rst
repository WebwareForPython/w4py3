.. module:: UserKit

.. _userkit:

UserKit
=======

UserKit provides for the management of users including passwords, user data, server-side archiving and caching. Users can be persisted on the server side via files or the external MiddleKit plug-in.

Introduction
------------

UserKit is a self contained library and is generally not dependent on the rest of Webware. It does use a few functions in MiscUtils. The objects of interest in UserKit are Users, UserMangers, and Roles.

:class:`User` -- This represents a particular user and has a name, password, and various flags like ``user.isActive()``.

:class:`UserManager` -- Your application will create one instance of a UserManager and use it to create and retrieve Users by name. The UserManager comes in several flavors depending on support for Roles, and where user data is stored. For storage, UserManagers can save the user records to either a flat file or a MiddleKit store. Also user managers may support Roles or not. If you don't need any roles and want the simplest UserManager, choose the UserManagerToFile which saves its data to a file. If you want hierarchical roles and persistence to MiddleKit, choose RoleUserManagerToMiddleKit.

:class:`Role` -- A role represents a permission that users may be granted. A user may belong to several roles, and this is queried using the method ``roleUser.playsRole(role)``. Roles can be hierarchical. For example a customers role may indicate permissions that customers have. A staff role may include the customers role, meaning that members of staff may also do anything that customers can do.

Examples and More Details
-------------------------

The docstrings in :class:`UserManager` is the first place to start. It describes all the methods in :class:`UserManager`. Then go to the file ``Tests/TestExample.py`` which demonstrates how to create users, log them in, and see if they are members of a particular role.

Once you get the idea, the docstrings in the various files may be perused for more details. See also the :ref:`reference documentation <ref-userkit>` for an overview of the available classes and methods.

Encryption of Passwords
-----------------------

Generally one should never save users' passwords anywhere in plain text. However UserKit intentionally does no support encryption of passwords. That is left to how you use UserKit in your application. See ``TestExample.py``, for a demonstration of how easy this is using SHA digests to encrypt passwords. Basically you encrypt your password before you give it to UserKit. It is as simple as this::

    usermanager.createUser('johndoe', sha('buster').hexdigest())

This design decision is to decouple UserKit from your particular encryption requirements, and allows you to use more advanced algorithms as they become available.

Credit
------

Author: Chuck Esterbrook, and a cast of dozens of volunteers.
Thanks to Tom Schwaller for design help.


