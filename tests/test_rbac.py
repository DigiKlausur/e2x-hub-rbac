"""Tests for core RBAC primitives: roles, scopes, RoleAssignment, and helpers."""

import pytest

from e2x_hub_rbac.auth.rbac import (
    ResourceContext,
    Role,
    RoleAssignment,
    Scope,
    _assignment_applies_to,
    _lookup_role,
    check_permission,
)

from .conftest import ROLE_PERMISSIONS, Permission

# ---------------------------------------------------------------------------
# Role / Scope
# ---------------------------------------------------------------------------


class TestRole:
    def test_role_name_and_scope(self):
        assert Role.HUB_ADMIN.role_name == "hub_admin"
        assert Role.HUB_ADMIN.scope is Scope.HUB

        assert Role.COURSE_CREATOR.role_name == "course_creator"
        assert Role.COURSE_CREATOR.scope is Scope.HUB

        assert Role.COURSE_OWNER.role_name == "course_owner"
        assert Role.COURSE_OWNER.scope is Scope.COURSE

        assert Role.INSTRUCTOR.role_name == "instructor"
        assert Role.INSTRUCTOR.scope is Scope.TERM

        assert Role.STUDENT.role_name == "student"
        assert Role.STUDENT.scope is Scope.TERM

        assert Role.TEACHING_ASSISTANT.role_name == "teaching_assistant"
        assert Role.TEACHING_ASSISTANT.scope is Scope.TERM

        assert Role.OBSERVER.role_name == "observer"
        assert Role.OBSERVER.scope is Scope.TERM

    def test_str(self):
        assert str(Role.TEACHING_ASSISTANT) == "teaching_assistant"


class TestLookupRole:
    def test_found(self):
        assert _lookup_role("hub_admin", Scope.HUB) is Role.HUB_ADMIN
        assert _lookup_role("student", Scope.TERM) is Role.STUDENT

    def test_wrong_scope_returns_none(self):
        # hub_admin exists, but it is a HUB scope role — not TERM
        assert _lookup_role("hub_admin", Scope.TERM) is None

    def test_unknown_name_returns_none(self):
        assert _lookup_role("does_not_exist", Scope.HUB) is None


# ---------------------------------------------------------------------------
# RoleAssignment constructors
# ---------------------------------------------------------------------------


class TestRoleAssignmentConstructors:
    def test_hub(self):
        ra = RoleAssignment.hub(Role.HUB_ADMIN)
        assert ra.role is Role.HUB_ADMIN
        assert ra.course_id is None
        assert ra.term_id is None
        assert ra.scope is Scope.HUB

    def test_hub_wrong_scope_raises(self):
        with pytest.raises(ValueError):
            RoleAssignment.hub(Role.COURSE_OWNER)

    def test_course(self):
        ra = RoleAssignment.course(Role.COURSE_OWNER, "math101")
        assert ra.course_id == "math101"
        assert ra.term_id is None
        assert ra.scope is Scope.COURSE

    def test_course_wrong_scope_raises(self):
        with pytest.raises(ValueError):
            RoleAssignment.course(Role.HUB_ADMIN, "math101")

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
        assert RoleAssignment.hub(Role.HUB_ADMIN).group_name == "hub.hub_admin"

    def test_course_group_name(self):
        assert (
            RoleAssignment.course(Role.COURSE_OWNER, "math101").group_name
            == "course.math101.course_owner"
        )

    def test_term_group_name(self):
        assert (
            RoleAssignment.term(Role.STUDENT, "math101", "2024ws").group_name
            == "term.math101.2024ws.student"
        )


# ---------------------------------------------------------------------------
# RoleAssignment.from_group_name
# ---------------------------------------------------------------------------


class TestFromGroupName:
    @pytest.mark.parametrize(
        "group_name, expected",
        [
            ("hub.hub_admin", RoleAssignment.hub(Role.HUB_ADMIN)),
            ("hub.course_creator", RoleAssignment.hub(Role.COURSE_CREATOR)),
            ("course.math101.course_owner", RoleAssignment.course(Role.COURSE_OWNER, "math101")),
            ("term.math101.2024ws.student", RoleAssignment.term(Role.STUDENT, "math101", "2024ws")),
            ("term.math101.2024ws.teaching_assistant", RoleAssignment.term(Role.TEACHING_ASSISTANT, "math101", "2024ws")),
            ("term.math101.2024ws.observer", RoleAssignment.term(Role.OBSERVER, "math101", "2024ws")),
            ("term.math101.2024ws.instructor", RoleAssignment.term(Role.INSTRUCTOR, "math101", "2024ws")),
        ],
    )
    def test_valid(self, group_name, expected):
        assert RoleAssignment.from_group_name(group_name) == expected

    @pytest.mark.parametrize(
        "group_name",
        [
            "invalid",
            "hub",  # too short
            "hub.unknown_role",  # unknown role name
            "course.math101",  # missing role
            "term.math101.2024ws",  # missing role
            "term.math101.2024ws.hub_admin",  # wrong scope
            "",
        ],
    )
    def test_invalid_returns_none(self, group_name):
        assert RoleAssignment.from_group_name(group_name) is None

    def test_roundtrip(self):
        """group_name → from_group_name should be the identity."""
        for role in Role:
            if role.scope is Scope.HUB:
                ra = RoleAssignment.hub(role)
            elif role.scope is Scope.COURSE:
                ra = RoleAssignment.course(role, "c1")
            else:
                ra = RoleAssignment.term(role, "c1", "t1")
            assert RoleAssignment.from_group_name(ra.group_name) == ra


# ---------------------------------------------------------------------------
# _assignment_applies_to
# ---------------------------------------------------------------------------


class TestAssignmentAppliesTo:
    def test_hub_role_applies_everywhere(self):
        ra = RoleAssignment.hub(Role.HUB_ADMIN)
        assert _assignment_applies_to(ra, ResourceContext()) is True
        assert _assignment_applies_to(ra, ResourceContext(course_id="math101")) is True
        assert (
            _assignment_applies_to(ra, ResourceContext(course_id="math101", term_id="2024ws"))
            is True
        )

    def test_course_role_applies_to_its_course(self):
        ra = RoleAssignment.course(Role.COURSE_OWNER, "math101")
        assert _assignment_applies_to(ra, ResourceContext(course_id="math101")) is True
        assert (
            _assignment_applies_to(ra, ResourceContext(course_id="math101", term_id="2024ws"))
            is True
        )

    def test_course_role_does_not_apply_to_other_course(self):
        ra = RoleAssignment.course(Role.COURSE_OWNER, "math101")
        assert _assignment_applies_to(ra, ResourceContext(course_id="phys201")) is False

    def test_course_role_applies_to_hub_context(self):
        ra = RoleAssignment.course(Role.COURSE_OWNER, "math101")
        assert _assignment_applies_to(ra, ResourceContext()) is True

    def test_term_role_applies_to_exact_term(self):
        ra = RoleAssignment.term(Role.STUDENT, "math101", "2024ws")
        assert (
            _assignment_applies_to(ra, ResourceContext(course_id="math101", term_id="2024ws"))
            is True
        )

    def test_term_role_does_not_apply_to_different_term(self):
        ra = RoleAssignment.term(Role.STUDENT, "math101", "2024ws")
        assert (
            _assignment_applies_to(ra, ResourceContext(course_id="math101", term_id="2025ss"))
            is False
        )

    def test_term_role_applies_to_course_context(self):
        ra = RoleAssignment.term(Role.STUDENT, "math101", "2024ws")
        assert _assignment_applies_to(ra, ResourceContext(course_id="math101")) is True

    def test_term_role_applies_to_hub_context(self):
        ra = RoleAssignment.term(Role.STUDENT, "math101", "2024ws")
        assert _assignment_applies_to(ra, ResourceContext()) is True


# ---------------------------------------------------------------------------
# check_permission
# ---------------------------------------------------------------------------


class TestCheckPermission:
    def test_hub_admin_has_all_permissions(self):
        assignments = [RoleAssignment.hub(Role.HUB_ADMIN)]
        for perm in Permission:
            context = ResourceContext(
                course_id="c1" if perm.required_scope in (Scope.COURSE, Scope.TERM) else None,
                term_id="t1" if perm.required_scope is Scope.TERM else None,
            )
            assert check_permission(assignments, perm, ROLE_PERMISSIONS, context) is True

    def test_student_can_read_term(self):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert check_permission(assignments, Permission.TERM_READ, ROLE_PERMISSIONS, ctx) is True

    def test_student_cannot_grade(self):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert check_permission(assignments, Permission.TERM_GRADE, ROLE_PERMISSIONS, ctx) is False

    def test_no_assignments_returns_false(self):
        ctx = ResourceContext(course_id="math101", term_id="2024ws")
        assert check_permission([], Permission.TERM_READ, ROLE_PERMISSIONS, ctx) is False

    def test_missing_course_context_raises_for_course_permission(self):
        assignments = [RoleAssignment.course(Role.COURSE_OWNER, "math101")]
        with pytest.raises(ValueError, match="course_id"):
            check_permission(
                assignments, Permission.COURSE_READ, ROLE_PERMISSIONS, ResourceContext()
            )

    def test_missing_term_context_raises_for_term_permission(self):
        assignments = [RoleAssignment.term(Role.STUDENT, "math101", "2024ws")]
        with pytest.raises(ValueError, match="term_id"):
            check_permission(
                assignments,
                Permission.TERM_READ,
                ROLE_PERMISSIONS,
                ResourceContext(course_id="math101"),
            )

    def test_none_context_defaults_to_hub(self):
        assignments = [RoleAssignment.hub(Role.HUB_ADMIN)]
        # HUB_MANAGE has required_scope = HUB, so hub context is fine
        assert check_permission(assignments, Permission.HUB_MANAGE, ROLE_PERMISSIONS, None) is True
