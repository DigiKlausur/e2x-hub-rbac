"""Tests for the require_permission decorator."""

import pytest

from e2x_hub_rbac.auth.decorator import require_permission
from e2x_hub_rbac.auth.rbac import PermissionChecker, UserLike
from e2x_hub_rbac.errors import APIPermissionError

from .models import DummyPermission

# ---------------------------------------------------------------------------
# Minimal API class that uses the decorator
# ---------------------------------------------------------------------------


class FakeAPI:
    def __init__(self, role_permissions):
        self._role_permissions = role_permissions

    def permission_checker(self, user: UserLike) -> PermissionChecker:
        return PermissionChecker(user, self._role_permissions)

    @require_permission(DummyPermission.TERM_READ)
    def get_term_data(self, user: UserLike, course_id: str, term_id: str):
        return f"{course_id}/{term_id}"

    @require_permission(DummyPermission.TERM_GRADE)
    def submit_grade(self, user: UserLike, course_id: str, term_id: str):
        return "graded"

    @require_permission(DummyPermission.COURSE_MANAGE)
    def manage_course(self, user: UserLike, course_id: str):
        return f"managing {course_id}"

    @require_permission(DummyPermission.HUB_MANAGE)
    def hub_action(self, user: UserLike):
        return "hub action done"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRequirePermission:
    @pytest.fixture
    def api(self, role_permissions):
        return FakeAPI(role_permissions)

    def test_permitted_call_succeeds(self, api, math101_2024ws_student_user):
        result = api.get_term_data(
            math101_2024ws_student_user, course_id="math101", term_id="2024ws"
        )
        assert result == "math101/2024ws"

    def test_denied_call_raises_api_permission_error(self, api, math101_2024ws_student_user):
        with pytest.raises(APIPermissionError):
            api.submit_grade(math101_2024ws_student_user, course_id="math101", term_id="2024ws")

    def test_teaching_assistant_can_submit_grade(self, api, math101_2024ws_teaching_assistant_user):
        result = api.submit_grade(
            math101_2024ws_teaching_assistant_user, course_id="math101", term_id="2024ws"
        )
        assert result == "graded"

    def test_hub_admin_can_call_all_methods(self, api, hub_admin_user):
        assert api.get_term_data(hub_admin_user, course_id="c1", term_id="t1") == "c1/t1"
        assert api.submit_grade(hub_admin_user, course_id="c1", term_id="t1") == "graded"
        assert api.manage_course(hub_admin_user, course_id="c1") == "managing c1"
        assert api.hub_action(hub_admin_user) == "hub action done"

    def test_no_role_user_denied(self, api, no_role_user):
        with pytest.raises(APIPermissionError):
            api.get_term_data(no_role_user, course_id="math101", term_id="2024ws")

    def test_error_contains_username(self, api, math101_2024ws_student_user):
        with pytest.raises(APIPermissionError) as exc_info:
            api.submit_grade(math101_2024ws_student_user, course_id="math101", term_id="2024ws")
        assert math101_2024ws_student_user.username in str(exc_info.value)

    def test_error_contains_permission_code(self, api, math101_2024ws_student_user):
        with pytest.raises(APIPermissionError) as exc_info:
            api.submit_grade(math101_2024ws_student_user, course_id="math101", term_id="2024ws")
        assert DummyPermission.TERM_GRADE.code in str(exc_info.value)

    def test_wraps_preserves_function_metadata(self):
        assert FakeAPI.get_term_data.__name__ == "get_term_data"

    def test_course_scoped_method_no_term_id(self, api, math101_course_owner_user):
        result = api.manage_course(math101_course_owner_user, course_id="math101")
        assert result == "managing math101"

    def test_course_scoped_method_wrong_course_denied(self, api, math101_course_owner_user):
        with pytest.raises(APIPermissionError):
            api.manage_course(math101_course_owner_user, course_id="phys201")

    def test_wrong_term_denied(self, api, math101_2024ws_student_user):
        """Student in math101/2024ws cannot access math101/2025ss."""
        with pytest.raises(APIPermissionError):
            api.get_term_data(math101_2024ws_student_user, course_id="math101", term_id="2025ss")
