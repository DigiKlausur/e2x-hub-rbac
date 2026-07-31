from dataclasses import dataclass

from e2x_hub_rbac.auth.rbac import PermissionEnum, Role, RolePermissions, Scope


@dataclass
class UserStub:
    """A simple user representation for testing purposes."""

    username: str
    groups: list[str]


class DummyPermission(PermissionEnum):
    """Test permissions covering all three scopes."""

    # Hub-scoped
    HUB_MANAGE = ("hub_manage", Scope.HUB)
    # Course-scoped
    COURSE_READ = ("course_read", Scope.COURSE)
    COURSE_MANAGE = ("course_manage", Scope.COURSE)
    # Term-scoped
    TERM_READ = ("term_read", Scope.TERM)
    TERM_GRADE = ("term_grade", Scope.TERM)


# ---------------------------------------------------------------------------
# Role→Permission mapping
# ---------------------------------------------------------------------------


TEST_ROLE_PERMISSIONS: RolePermissions = {
    Role.HUB_ADMIN: frozenset(
        [
            DummyPermission.HUB_MANAGE,
            DummyPermission.COURSE_READ,
            DummyPermission.COURSE_MANAGE,
            DummyPermission.TERM_READ,
            DummyPermission.TERM_GRADE,
        ]
    ),
    Role.COURSE_CREATOR: frozenset([DummyPermission.HUB_MANAGE]),
    Role.COURSE_OWNER: frozenset(
        [
            DummyPermission.COURSE_READ,
            DummyPermission.COURSE_MANAGE,
            DummyPermission.TERM_READ,
            DummyPermission.TERM_GRADE,
        ]
    ),
    Role.INSTRUCTOR: frozenset([DummyPermission.TERM_READ, DummyPermission.TERM_GRADE]),
    Role.TEACHING_ASSISTANT: frozenset([DummyPermission.TERM_READ, DummyPermission.TERM_GRADE]),
    Role.STUDENT: frozenset([DummyPermission.TERM_READ]),
    Role.OBSERVER: frozenset([DummyPermission.TERM_READ]),
}
