from logging import Logger, getLogger
from typing import Optional

from ..auth.rbac import PermissionChecker, PermissionProtocol, RolePermissions, UserLike


class BaseAPI:
    """Base class for all API classes providing common functionality.

    Provides access to the server configuration and common permission
    checking utilities for course-based operations.

    Attributes:
        logger: Logger instance for logging messages.
        _role_permissions: Mapping of roles to their associated permissions.
    """

    def __init__(
        self,
        role_permissions: RolePermissions,
        logger: Optional[Logger] = None,
    ):
        """Initialize the API with application context.

        Args:
            context: The application context object
            role_permissions: A mapping of roles to their associated permissions
            logger: Optional logger for logging purposes
        """
        if logger is None:
            logger = getLogger(__name__)
        self.logger = logger
        self._role_permissions = role_permissions

    def permission_checker(self, user: UserLike) -> PermissionChecker:
        """Get a PermissionChecker instance for the given user.

        Args:
            user: The User object for whom to create the PermissionChecker
        Returns:
            A PermissionChecker instance initialized with the user's permissions
        """
        return PermissionChecker(user, self._role_permissions)

    def has_permission(
        self,
        user: UserLike,
        permission: PermissionProtocol,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
    ) -> bool:
        """Check if the user has the required permission.

        Args:
            user: The User object to check permissions for
            permission: The Permission to check
            course_id: Optional course ID for context-specific permissions
            term_id: Optional term ID for context-specific permissions
        Returns:
            True if the user has the required permission, False otherwise
        """
        checker = self.permission_checker(user)
        return checker.has_permission(permission, course_id=course_id, term_id=term_id)

    def get_registered_permissions(self) -> set[PermissionProtocol]:
        """Get the set of all registered permissions in the system.

        Returns:
            A set of all registered PermissionProtocol instances
        """
        permissions = set()
        for role, perms in self._role_permissions.items():
            permissions.update(perms)
        return permissions
