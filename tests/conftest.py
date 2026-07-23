"""Shared fixtures and helpers for the test suite."""

from enum import Enum

import pytest

from e2x_hub_rbac.auth.rbac import (
    Role,
    RolePermissions,
    Scope,
)
from e2x_hub_rbac.auth.user import User

# ---------------------------------------------------------------------------
# Minimal concrete Permission implementation for testing
# ---------------------------------------------------------------------------


class Permission(Enum):
    """Test permissions covering all three scopes."""

    # Hub-scoped
    HUB_MANAGE = ("hub_manage", Scope.HUB)
    # Course-scoped
    COURSE_READ = ("course_read", Scope.COURSE)
    COURSE_MANAGE = ("course_manage", Scope.COURSE)
    # Term-scoped
    TERM_READ = ("term_read", Scope.TERM)
    TERM_GRADE = ("term_grade", Scope.TERM)

    def __init__(self, code: str, required_scope: Scope):
        self.code = code
        self.required_scope = required_scope


# ---------------------------------------------------------------------------
# Role→Permission mapping
# ---------------------------------------------------------------------------


ROLE_PERMISSIONS: RolePermissions = {
    Role.HUB_ADMIN: frozenset(
        [
            Permission.HUB_MANAGE,
            Permission.COURSE_READ,
            Permission.COURSE_MANAGE,
            Permission.TERM_READ,
            Permission.TERM_GRADE,
        ]
    ),
    Role.COURSE_CREATOR: frozenset([Permission.HUB_MANAGE]),
    Role.COURSE_ADMIN: frozenset(
        [
            Permission.COURSE_READ,
            Permission.COURSE_MANAGE,
            Permission.TERM_READ,
            Permission.TERM_GRADE,
        ]
    ),
    Role.TERM_ADMIN: frozenset([Permission.TERM_READ, Permission.TERM_GRADE]),
    Role.GRADER: frozenset([Permission.TERM_READ, Permission.TERM_GRADE]),
    Role.STUDENT: frozenset([Permission.TERM_READ]),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def role_permissions() -> RolePermissions:
    return ROLE_PERMISSIONS


@pytest.fixture
def hub_admin_user() -> User:
    return User(username="admin", admin=True, groups=["hub.hub_admin"])


@pytest.fixture
def course_admin_user() -> User:
    return User(username="course_admin", groups=["course.math101.course_admin"])


@pytest.fixture
def student_user() -> User:
    return User(username="alice", groups=["term.math101.2024ws.student"])


@pytest.fixture
def grader_user() -> User:
    return User(username="bob", groups=["term.math101.2024ws.grader"])


@pytest.fixture
def multi_role_user() -> User:
    """User with roles in two different courses/terms."""
    return User(
        username="multi",
        groups=[
            "term.math101.2024ws.student",
            "term.phys201.2024ws.grader",
            "course.chem301.course_admin",
        ],
    )


@pytest.fixture
def no_role_user() -> User:
    return User(username="nobody", groups=[])
