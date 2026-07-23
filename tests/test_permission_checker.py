"""Tests for PermissionChecker."""

import pytest

from e2x_hub_rbac.auth.rbac import PermissionChecker, Role, RoleAssignment
from e2x_hub_rbac.auth.user import User

from .conftest import Permission


@pytest.fixture
def student_checker(student_user, role_permissions):
    return PermissionChecker(student_user, role_permissions)


@pytest.fixture
def hub_admin_checker(hub_admin_user, role_permissions):
    return PermissionChecker(hub_admin_user, role_permissions)


@pytest.fixture
def grader_checker(grader_user, role_permissions):
    return PermissionChecker(grader_user, role_permissions)


@pytest.fixture
def no_role_checker(no_role_user, role_permissions):
    return PermissionChecker(no_role_user, role_permissions)


@pytest.fixture
def multi_role_checker(multi_role_user, role_permissions):
    return PermissionChecker(multi_role_user, role_permissions)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestPermissionCheckerInit:
    def test_user_property(self, student_checker, student_user):
        assert student_checker.user == student_user

    def test_groups_property(self, student_checker):
        assert student_checker.groups == ["term.math101.2024ws.student"]

    def test_assignments_parsed(self, student_checker):
        assert len(student_checker.assignments) == 1
        assert student_checker.assignments[0] == RoleAssignment.term(
            Role.STUDENT, "math101", "2024ws"
        )

    def test_unknown_groups_are_ignored(self, role_permissions):
        user = User(username="alice", groups=["term.math101.2024ws.student", "custom-group"])
        checker = PermissionChecker(user, role_permissions)
        assert len(checker.assignments) == 1

    def test_no_groups_no_assignments(self, no_role_checker):
        assert no_role_checker.assignments == []


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------


class TestHasPermission:
    def test_student_can_read_own_term(self, student_checker):
        assert (
            student_checker.has_permission(
                Permission.TERM_READ, course_id="math101", term_id="2024ws"
            )
            is True
        )

    def test_student_cannot_read_different_term(self, student_checker):
        assert (
            student_checker.has_permission(
                Permission.TERM_READ, course_id="math101", term_id="2025ss"
            )
            is False
        )

    def test_student_cannot_grade(self, student_checker):
        assert (
            student_checker.has_permission(
                Permission.TERM_GRADE, course_id="math101", term_id="2024ws"
            )
            is False
        )

    def test_grader_can_grade(self, grader_checker):
        assert (
            grader_checker.has_permission(
                Permission.TERM_GRADE, course_id="math101", term_id="2024ws"
            )
            is True
        )

    def test_hub_admin_can_do_everything(self, hub_admin_checker):
        assert hub_admin_checker.has_permission(Permission.HUB_MANAGE) is True
        assert hub_admin_checker.has_permission(Permission.COURSE_READ, course_id="any") is True
        assert (
            hub_admin_checker.has_permission(Permission.TERM_GRADE, course_id="any", term_id="any")
            is True
        )

    def test_no_role_user_denied_everywhere(self, no_role_checker):
        assert (
            no_role_checker.has_permission(
                Permission.TERM_READ, course_id="math101", term_id="2024ws"
            )
            is False
        )

    def test_multi_role_user_has_correct_permissions(self, multi_role_checker):
        # Student in math101/2024ws
        assert (
            multi_role_checker.has_permission(
                Permission.TERM_READ, course_id="math101", term_id="2024ws"
            )
            is True
        )
        assert (
            multi_role_checker.has_permission(
                Permission.TERM_GRADE, course_id="math101", term_id="2024ws"
            )
            is False
        )

        # Grader in phys201/2024ws
        assert (
            multi_role_checker.has_permission(
                Permission.TERM_GRADE, course_id="phys201", term_id="2024ws"
            )
            is True
        )

        # Course admin in chem301
        assert (
            multi_role_checker.has_permission(Permission.COURSE_MANAGE, course_id="chem301") is True
        )

        # Should not have access to unrelated course
        assert (
            multi_role_checker.has_permission(Permission.COURSE_MANAGE, course_id="bio101") is False
        )


# ---------------------------------------------------------------------------
# get_roles_in_course_and_term
# ---------------------------------------------------------------------------


class TestGetRolesInCourseAndTerm:
    def test_student_role_returned(self, student_checker):
        roles = student_checker.get_roles_in_course_and_term("math101", "2024ws")
        assert Role.STUDENT in roles

    def test_empty_for_unrelated_course(self, student_checker):
        roles = student_checker.get_roles_in_course_and_term("phys201", "2024ws")
        assert roles == set()

    def test_hub_admin_role_returned_for_any_course(self, hub_admin_checker):
        roles = hub_admin_checker.get_roles_in_course_and_term("any_course", "any_term")
        assert Role.HUB_ADMIN in roles

    def test_multi_role_user(self, multi_role_checker):
        roles = multi_role_checker.get_roles_in_course_and_term("math101", "2024ws")
        assert Role.STUDENT in roles
        roles = multi_role_checker.get_roles_in_course_and_term("phys201", "2024ws")
        assert Role.GRADER in roles


# ---------------------------------------------------------------------------
# get_course_ids
# ---------------------------------------------------------------------------


class TestGetCourseIds:
    def test_student_has_course_id(self, student_checker):
        assert student_checker.get_course_ids() == {"math101"}

    def test_no_role_user_empty(self, no_role_checker):
        assert no_role_checker.get_course_ids() == set()

    def test_hub_admin_no_course_ids(self, hub_admin_checker):
        # Hub-level roles don't carry a course_id
        assert hub_admin_checker.get_course_ids() == set()

    def test_multi_role_user_has_all_course_ids(self, multi_role_checker):
        assert multi_role_checker.get_course_ids() == {"math101", "phys201", "chem301"}
