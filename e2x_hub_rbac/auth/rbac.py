from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Scope(str, Enum):
    HUB = "hub"
    COURSE = "course"
    TERM = "term"


class UserLike(Protocol):
    username: str
    groups: list[str]


class Role(Enum):
    role_name: str
    scope: Scope

    HUB_ADMIN = ("hub_admin", Scope.HUB)
    COURSE_CREATOR = ("course_creator", Scope.HUB)
    COURSE_OWNER = ("course_owner", Scope.COURSE)
    INSTRUCTOR = ("instructor", Scope.TERM)
    TEACHING_ASSISTANT = ("teaching_assistant", Scope.TERM)
    OBSERVER = ("observer", Scope.TERM)
    STUDENT = ("student", Scope.TERM)

    def __init__(self, role_name: str, scope: Scope):
        self.role_name = role_name
        self.scope = scope

    def __str__(self) -> str:
        return self.role_name


ROLE_BY_NAME: dict[str, Role] = {role.role_name: role for role in Role}


def _lookup_role(role_name: str, expected_scope: Scope) -> Role | None:
    """Return the Role with the given name and scope, or None if not found."""
    role = ROLE_BY_NAME.get(role_name)
    if role is None or role.scope is not expected_scope:
        return None
    return role


class PermissionProtocol(Protocol):
    code: str
    required_scope: Scope


RolePermissions = dict[Role, frozenset[PermissionProtocol]]


class PermissionEnum(Enum):
    code: str
    required_scope: Scope

    def __init__(self, code: str, required_scope: Scope):
        self.code = code
        self.required_scope = required_scope

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class ResourceContext:
    """Identifies the resource being acted upon.

    - No course_id/term_id: hub-level resource
    - course_id only: course-level resource
    - course_id + term_id: term-level resource
    """

    course_id: str | None = None
    term_id: str | None = None


@dataclass(frozen=True)
class RoleAssignment:
    """A role granted to a user at a specific scope."""

    role: Role
    course_id: str | None = None
    term_id: str | None = None

    @classmethod
    def hub(cls, role: Role):
        """Create a hub-level role assignment."""
        if role.scope is not Scope.HUB:
            raise ValueError(f"Role {role.role_name} is not a hub-level role")
        return cls(role=role)

    @classmethod
    def course(cls, role: Role, course_id: str):
        """Create a course-level role assignment."""
        if role.scope is not Scope.COURSE:
            raise ValueError(f"Role {role.role_name} is not a course-level role")
        return cls(role=role, course_id=course_id)

    @classmethod
    def term(cls, role: Role, course_id: str, term_id: str):
        """Create a term-level role assignment."""
        if role.scope is not Scope.TERM:
            raise ValueError(f"Role {role.role_name} is not a term-level role")
        return cls(
            role=role,
            course_id=course_id,
            term_id=term_id,
        )

    @property
    def scope(self) -> Scope:
        return self.role.scope

    @property
    def group_name(self) -> str:
        if self.scope is Scope.HUB:
            return f"hub.{self.role.role_name}"
        if self.scope is Scope.COURSE:
            return f"course.{self.course_id}.{self.role.role_name}"
        if self.scope is Scope.TERM:
            return f"term.{self.course_id}.{self.term_id}.{self.role.role_name}"
        raise ValueError(f"Invalid role scope: {self.scope}")

    @classmethod
    def from_group_name(cls, group_name: str) -> "RoleAssignment | None":
        """Parse a JupyterHub group name into a RoleAssignment.

        Formats:
            hub.<role_id>
            course.<course_id>.<role_id>
            term.<course_id>.<term_id>.<role_id>

        Returns None if the group name doesn't match a known format.
        """
        parts = group_name.split(".")
        if len(parts) < 2:
            return None

        scope_str = parts[0]

        if scope_str == "hub" and len(parts) == 2:
            role = _lookup_role(parts[1], Scope.HUB)
            if role is None:
                return None
            return cls.hub(role=role)

        if scope_str == "course" and len(parts) == 3:
            role = _lookup_role(parts[2], Scope.COURSE)
            if role is None:
                return None
            return cls.course(role=role, course_id=parts[1])

        if scope_str == "term" and len(parts) == 4:
            role = _lookup_role(parts[3], Scope.TERM)

            if role is None:
                return None
            return cls.term(role=role, course_id=parts[1], term_id=parts[2])

        return None


def _assignment_applies_to(assignment: RoleAssignment, context: ResourceContext) -> bool:
    """Return whether a role assignment applies to the given resource context.

    A role assignment grants permissions for resources within its scope:

    - HUB roles apply everywhere.
    - COURSE roles apply to their course and all terms within that course.
    - TERM roles apply only to their assigned term.

    When the resource context refers to a higher-level resource (for example,
    a course or hub resource rather than a term), any assignment within that
    resource hierarchy is considered applicable.
    """
    scope = assignment.scope

    if scope is Scope.HUB:
        return True

    if scope is Scope.COURSE:
        if context.course_id is None:
            # Hub-level resource — any holder of this role qualifies.
            return True
        return assignment.course_id == context.course_id

    if scope is Scope.TERM:
        if context.course_id is None:
            # Hub-level resource — any holder of this role qualifies.
            return True
        if context.term_id is None:
            # Course-level resource — verify the role is in the same course.
            return assignment.course_id == context.course_id
        return assignment.course_id == context.course_id and assignment.term_id == context.term_id

    return False


def check_permission(
    assignments: list[RoleAssignment],
    permission: PermissionProtocol,
    role_permissions: RolePermissions,
    context: ResourceContext | None = None,
) -> bool:
    """Return whether the user's role assignments grant a permission.

    The permission is granted if at least one role assignment:

    - includes the requested permission, and
    - applies to the given resource context.

    Args:
        assignments: The user's role assignments.
        permission: The permission to evaluate.
        role_permissions: Mapping from roles to the permissions they grant.
        context: The resource being accessed. If omitted, the hub is assumed.

    Raises:
        ValueError: If the permission requires a course or term context that
            is not provided.

    Returns:
        True if the permission is granted by any applicable role assignment,
        otherwise False.
    """
    if context is None:
        context = ResourceContext()

    # Validate that required context fields are provided.
    required_scope = permission.required_scope
    if required_scope is Scope.COURSE and context.course_id is None:
        raise ValueError(f"{permission.code} requires course_id in the resource context")
    if required_scope is Scope.TERM and (context.course_id is None or context.term_id is None):
        raise ValueError(
            f"{permission.code} requires course_id and term_id in the resource context"
        )

    for assignment in assignments:
        if permission in role_permissions[assignment.role] and _assignment_applies_to(
            assignment, context
        ):
            return True
    return False


class PermissionChecker:
    """Checks whether a user has a given permission based on their role assignments."""

    def __init__(
        self,
        user: UserLike,
        role_permissions: RolePermissions,
    ):
        self._user = user
        self._role_permissions = role_permissions
        self._groups = list(user.groups)
        self._assignments = []

        for group_name in user.groups:
            assignment = RoleAssignment.from_group_name(group_name)
            if assignment is not None:
                self._assignments.append(assignment)

    @property
    def user(self) -> UserLike:
        return self._user

    @property
    def groups(self) -> list[str]:
        return list(self._groups)

    @property
    def assignments(self) -> list[RoleAssignment]:
        return list(self._assignments)

    def has_permission(
        self,
        permission: PermissionProtocol,
        course_id: str | None = None,
        term_id: str | None = None,
    ) -> bool:
        context = ResourceContext(course_id=course_id, term_id=term_id)
        return check_permission(
            assignments=self._assignments,
            permission=permission,
            role_permissions=self._role_permissions,
            context=context,
        )

    def get_roles_in_hub(self) -> set[Role]:
        """Return the roles the user has at the hub level."""
        roles = set()
        for assignment in self._assignments:
            if assignment.scope is Scope.HUB:
                roles.add(assignment.role)
        return roles

    def get_permissions_in_hub(self) -> set[PermissionProtocol]:
        """Return the permissions the user has at the hub level."""
        permissions = set()
        for role in self.get_roles_in_hub():
            permissions.update(self._role_permissions[role])
        return permissions

    def get_roles_in_course(self, course_id: str) -> set[Role]:
        """Return the roles the user has in a specific course."""
        context = ResourceContext(course_id=course_id)
        roles = set()
        for assignment in self._assignments:
            if _assignment_applies_to(assignment, context):
                roles.add(assignment.role)
        return set([role for role in roles if role.scope in (Scope.COURSE, Scope.HUB)])

    def get_permissions_in_course(self, course_id: str) -> set[PermissionProtocol]:
        """Return the permissions the user has in a specific course."""
        permissions = set()
        for role in self.get_roles_in_course(course_id):
            permissions.update(self._role_permissions[role])
        return permissions

    def get_roles_in_term(self, course_id: str, term_id: str) -> set[Role]:
        """Return the roles the user has in a specific course and term."""
        context = ResourceContext(course_id=course_id, term_id=term_id)
        roles = set()
        for assignment in self._assignments:
            if _assignment_applies_to(assignment, context):
                roles.add(assignment.role)
        return roles

    def get_permissions_in_term(self, course_id: str, term_id: str) -> set[PermissionProtocol]:
        """Return the permissions the user has in a specific course and term."""
        permissions = set()
        for role in self.get_roles_in_term(course_id, term_id):
            permissions.update(self._role_permissions[role])
        return permissions

    def get_course_ids(self) -> set[str]:
        """Return the list of course IDs for which the user has any role assignment."""
        return {
            assignment.course_id
            for assignment in self._assignments
            if assignment.scope in (Scope.COURSE, Scope.TERM) and assignment.course_id is not None
        }
