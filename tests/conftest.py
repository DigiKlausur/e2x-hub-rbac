"""Shared fixtures and helpers for the test suite."""

import pytest

from e2x_hub_rbac.auth.rbac import (
    PermissionChecker,
    RolePermissions,
    UserLike,
)

from .models import TEST_ROLE_PERMISSIONS, UserStub

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def role_permissions() -> RolePermissions:
    return TEST_ROLE_PERMISSIONS


@pytest.fixture
def hub_admin_user() -> UserLike:
    return UserStub(username="admin", groups=["hub.hub_admin"])


@pytest.fixture
def math101_course_owner_user() -> UserLike:
    return UserStub(username="course_owner", groups=["course.math101.course_owner"])


@pytest.fixture
def math101_2024ws_student_user() -> UserLike:
    return UserStub(username="alice", groups=["term.math101.2024ws.student"])


@pytest.fixture
def math101_2024ws_teaching_assistant_user() -> UserLike:
    return UserStub(username="bob", groups=["term.math101.2024ws.teaching_assistant"])


@pytest.fixture
def multi_course_multi_role_user() -> UserLike:
    """User with roles in two different courses/terms."""
    return UserStub(
        username="multi",
        groups=[
            "term.math101.2024ws.student",
            "term.phys201.2024ws.teaching_assistant",
            "course.chem301.course_owner",
        ],
    )


@pytest.fixture
def no_role_user() -> UserLike:
    return UserStub(username="nobody", groups=[])


@pytest.fixture
def student_checker(math101_2024ws_student_user, role_permissions):
    return PermissionChecker(math101_2024ws_student_user, role_permissions)


@pytest.fixture
def hub_admin_checker(hub_admin_user, role_permissions):
    return PermissionChecker(hub_admin_user, role_permissions)


@pytest.fixture
def teaching_assistant_checker(math101_2024ws_teaching_assistant_user, role_permissions):
    return PermissionChecker(math101_2024ws_teaching_assistant_user, role_permissions)


@pytest.fixture
def no_role_checker(no_role_user, role_permissions):
    return PermissionChecker(no_role_user, role_permissions)


@pytest.fixture
def multi_role_checker(multi_course_multi_role_user, role_permissions):
    return PermissionChecker(multi_course_multi_role_user, role_permissions)
