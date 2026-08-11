"""Tests for core RBAC primitives: roles, scopes, RoleAssignment, and helpers."""

import pytest

from e2x_hub_rbac.auth.rbac import (
    ResourceContext,
    Role,
    RoleAssignment,
    Scope,
    check_permission,
)

from .models import DummyPermission

# ---------------------------------------------------------------------------
# Role / Scope
# ---------------------------------------------------------------------------


class TestRole:
    @pytest.mark.parametrize(
        "role, expected_name, expected_scope",
        [
            (Role.LMS_ADMIN, "lms-admin", Scope.LMS),
            (Role.COURSE_CREATOR, "course-creator", Scope.LMS),
            (Role.COURSE_OWNER, "course-owner", Scope.COURSE),
            (Role.INSTRUCTOR, "instructor", Scope.TERM),
            (Role.TEACHING_ASSISTANT, "teaching-assistant", Scope.TERM),
            (Role.OBSERVER, "observer", Scope.TERM),
            (Role.STUDENT, "student", Scope.TERM),
        ],
    )
    def test_role_name_and_scope(self, role, expected_name, expected_scope):
        assert role.role_name == expected_name
        assert role.scope is expected_scope

    def test_str(self):
        assert str(Role.TEACHING_ASSISTANT) == "teaching-assistant"


# ---------------------------------------------------------------------------
# RoleAssignment constructors
# ---------------------------------------------------------------------------


class TestRoleAssignmentConstructors:
    def test_hub(self):
        ra = RoleAssignment.lms(Role.LMS_ADMIN)
        assert ra.role is Role.LMS_ADMIN
        assert ra.course_id is None
        assert ra.term_id is None
        assert ra.scope is Scope.LMS

    def test_hub_wrong_scope_raises(self):
        with pytest.raises(ValueError):
            RoleAssignment.lms(Role.COURSE_OWNER)

    def test_course(self):
        ra = RoleAssignment.course(Role.COURSE_OWNER, "math101")
        assert ra.course_id == "math101"
        assert ra.term_id is None
        assert ra.scope is Scope.COURSE

    def test_course_wrong_scope_raises(self):
        with pytest.raises(ValueError):
            RoleAssignment.course(Role.LMS_ADMIN, "math101")

    def test_term(self):
        ra = RoleAssignment.term(Role.STUDENT, "math101", "2024ws")
        assert ra.course_id == "math101"
        assert ra.term_id == "2024ws"
        assert ra.scope is Scope.TERM

    def test_term_wrong_scope_raises(self):
        with pytest.raises(ValueError):
            RoleAssignment.term(Role.COURSE_OWNER, "math101", "2024ws")


# ---------------------------------------------------------------------------
# RoleAssignment.group_name
# ---------------------------------------------------------------------------


class TestGroupName:
    def test_hub_group_name(self):
        assert RoleAssignment.lms(Role.LMS_ADMIN).group_name == "lms.lms-admin"

    def test_course_group_name(self):
        assert (
            RoleAssignment.course(Role.COURSE_OWNER, "math101").group_name
            == "lms.course.math101.course-owner"
        )

    def test_term_group_name(self):
        assert (
            RoleAssignment.term(Role.STUDENT, "math101", "2024ws").group_name
            == "lms.course.math101.term.2024ws.student"
        )


# ---------------------------------------------------------------------------
# RoleAssignment.from_group_name
# ---------------------------------------------------------------------------


class TestFromGroupName:
    @pytest.mark.parametrize(
        "group_name, expected",
        [
            ("lms.lms-admin", RoleAssignment.lms(Role.LMS_ADMIN)),
            ("lms.course-creator", RoleAssignment.lms(Role.COURSE_CREATOR)),
            (
                "lms.course.math101.course-owner",
                RoleAssignment.course(Role.COURSE_OWNER, "math101"),
            ),
            (
                "lms.course.math101.term.2024ws.student",
                RoleAssignment.term(Role.STUDENT, "math101", "2024ws"),
            ),
            (
                "lms.course.math101.term.2024ws.teaching-assistant",
                RoleAssignment.term(Role.TEACHING_ASSISTANT, "math101", "2024ws"),
            ),
            (
                "lms.course.math101.term.2024ws.observer",
                RoleAssignment.term(Role.OBSERVER, "math101", "2024ws"),
            ),
            (
                "lms.course.math101.term.2024ws.instructor",
                RoleAssignment.term(Role.INSTRUCTOR, "math101", "2024ws"),
            ),
        ],
    )
    def test_valid(self, group_name, expected):
        assert RoleAssignment.from_group_name(group_name) == expected

    @pytest.mark.parametrize(
        "group_name",
        [
            "invalid",
            "lms",  # too short
            "lms.unknown_role",  # unknown role name
            "lms.course.math101",  # missing role
            "lms.course.math101.term.2024ws",  # missing role
            "lms.course.math101.term.2024ws.lms-admin",  # wrong scope
            "",
        ],
    )
    def test_invalid_returns_none(self, group_name):
        assert RoleAssignment.from_group_name(group_name) is None

    def test_roundtrip(self):
        """group_name → from_group_name should be the identity."""
        for role in Role:
            if role.scope is Scope.LMS:
                ra = RoleAssignment.lms(role)
            elif role.scope is Scope.COURSE:
                ra = RoleAssignment.course(role, "c1")
            else:
                ra = RoleAssignment.term(role, "c1", "t1")
            assert RoleAssignment.from_group_name(ra.group_name) == ra


# ---------------------------------------------------------------------------
# check_permission
# ---------------------------------------------------------------------------


class TestCheckPermission:
    def test_hub_admin_has_all_permissions(self, role_permissions):
        assignments = [RoleAssignment.lms(Role.LMS_ADMIN)]
        for perm in DummyPermission:
            context = ResourceContext(
                course_id="c1" if perm.required_scope in (Scope.COURSE, Scope.TERM) else None,
                term_id="t1" if perm.required_scope is Scope.TERM else None,
            )
            assert check_permission(assignments, perm, role_permissions, context) is True

    def test_student_can_read_term(self, role_permissions):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert (
            check_permission(assignments, DummyPermission.TERM_READ, role_permissions, ctx) is True
        )

    def test_student_cannot_grade(self, role_permissions):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert (
            check_permission(assignments, DummyPermission.TERM_GRADE, role_permissions, ctx)
            is False
        )

    def test_no_assignments_returns_false(self, role_permissions):
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert check_permission([], DummyPermission.TERM_READ, role_permissions, ctx) is False

    def test_missing_course_context_raises_for_course_permission(self, role_permissions):
        assignments = [RoleAssignment.course(Role.COURSE_OWNER, "math101")]
        with pytest.raises(ValueError, match="course_id"):
            check_permission(
                assignments, DummyPermission.COURSE_READ, role_permissions, ResourceContext()
            )

    def test_missing_term_context_raises_for_term_permission(self, role_permissions):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        with pytest.raises(ValueError, match="term_id"):
            check_permission(
                assignments,
                DummyPermission.TERM_READ,
                role_permissions,
                ResourceContext(course_id="math101"),
            )

    def test_none_context_defaults_to_hub(self, role_permissions):
        assignments = [RoleAssignment.lms(Role.LMS_ADMIN)]
        # HUB_MANAGE has required_scope = HUB, so hub context is fine
        assert (
            check_permission(assignments, DummyPermission.HUB_MANAGE, role_permissions, None)
            is True
        )
