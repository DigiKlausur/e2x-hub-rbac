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
def lms_admin_user() -> UserLike:
    return UserStub(username="admin", groups=["lms.lms-admin"])


@pytest.fixture
def math101_course_owner_user() -> UserLike:
    return UserStub(username="course-owner", groups=["lms.course.math101.course-owner"])


@pytest.fixture
def math101_2024ws_student_user() -> UserLike:
    return UserStub(username="alice", groups=["lms.course.math101.term.2024ws.student"])


@pytest.fixture
def math101_2024ws_teaching_assistant_user() -> UserLike:
    return UserStub(username="bob", groups=["lms.course.math101.term.2024ws.teaching-assistant"])


@pytest.fixture
def multi_course_multi_role_user() -> UserLike:
    """User with roles in two different courses/terms."""
    return UserStub(
        username="multi",
        groups=[
            "lms.course.math101.term.2024ws.student",
            "lms.course.phys201.term.2024ws.teaching-assistant",
            "lms.course.chem301.course-owner",
        ],
    )


@pytest.fixture
def no_role_user() -> UserLike:
    return UserStub(username="nobody", groups=[])


@pytest.fixture
def student_checker(math101_2024ws_student_user, role_permissions):
    return PermissionChecker(math101_2024ws_student_user, role_permissions)


@pytest.fixture
def hub_admin_checker(lms_admin_user, role_permissions):
    return PermissionChecker(lms_admin_user, role_permissions)


@pytest.fixture
def teaching_assistant_checker(math101_2024ws_teaching_assistant_user, role_permissions):
    return PermissionChecker(math101_2024ws_teaching_assistant_user, role_permissions)


@pytest.fixture
def no_role_checker(no_role_user, role_permissions):
    return PermissionChecker(no_role_user, role_permissions)


@pytest.fixture
def multi_role_checker(multi_course_multi_role_user, role_permissions):
    return PermissionChecker(multi_course_multi_role_user, role_permissions)
