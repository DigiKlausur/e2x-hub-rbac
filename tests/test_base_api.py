"""Tests for BaseAPI."""

import pytest

from e2x_hub_rbac.api.base_api import BaseAPI
from e2x_hub_rbac.auth.rbac import PermissionChecker

from .conftest import Permission


@pytest.fixture
def api(role_permissions):
    return BaseAPI(role_permissions=role_permissions)


class TestBaseAPI:
    def test_permission_checker_returns_permission_checker(self, api, student_user):
        checker = api.permission_checker(student_user)
        assert isinstance(checker, PermissionChecker)

    def test_permission_checker_is_bound_to_user(self, api, student_user):
        checker = api.permission_checker(student_user)
        assert checker.user == student_user

    def test_has_permission_granted(self, api, student_user):
        assert (
            api.has_permission(
                student_user, Permission.TERM_READ, course_id="math101", term_id="2024ws"
            )
            is True
        )

    def test_has_permission_denied(self, api, student_user):
        assert (
            api.has_permission(
                student_user, Permission.TERM_GRADE, course_id="math101", term_id="2024ws"
            )
            is False
        )

    def test_has_permission_hub_admin(self, api, hub_admin_user):
        assert api.has_permission(hub_admin_user, Permission.HUB_MANAGE) is True
        assert (
            api.has_permission(hub_admin_user, Permission.TERM_GRADE, course_id="c1", term_id="t1")
            is True
        )

    def test_has_permission_no_role(self, api, no_role_user):
        assert (
            api.has_permission(
                no_role_user, Permission.TERM_READ, course_id="math101", term_id="2024ws"
            )
            is False
        )

    def test_default_logger_created_when_not_provided(self, role_permissions):
        """Should not raise when no logger is passed."""
        api = BaseAPI(role_permissions=role_permissions)
        assert api is not None

    def test_custom_logger_accepted(self, role_permissions):
        import logging

        logger = logging.getLogger("test")
        api = BaseAPI(role_permissions=role_permissions, logger=logger)
        assert api is not None
