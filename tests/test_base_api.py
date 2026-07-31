"""Tests for BaseAPI."""

import pytest

from e2x_hub_rbac.api.base_api import BaseAPI
from e2x_hub_rbac.auth.rbac import PermissionChecker

from .models import DummyPermission


@pytest.fixture
def api(role_permissions):
    return BaseAPI(role_permissions=role_permissions)


class TestBaseAPI:
    def test_permission_checker_returns_permission_checker(self, api, math101_2024ws_student_user):
        checker = api.permission_checker(math101_2024ws_student_user)
        assert isinstance(checker, PermissionChecker)

    def test_permission_checker_is_bound_to_user(self, api, math101_2024ws_student_user):
        checker = api.permission_checker(math101_2024ws_student_user)
        assert checker.user == math101_2024ws_student_user

    def test_has_permission_granted(self, api, math101_2024ws_student_user):
        assert (
            api.has_permission(
                math101_2024ws_student_user,
                DummyPermission.TERM_READ,
                course_id="math101",
                term_id="2024ws",
            )
            is True
        )

    def test_has_permission_denied(self, api, math101_2024ws_student_user):
        assert (
            api.has_permission(
                math101_2024ws_student_user,
                DummyPermission.TERM_GRADE,
                course_id="math101",
                term_id="2024ws",
            )
            is False
        )

    def test_has_permission_hub_admin(self, api, hub_admin_user):
        assert api.has_permission(hub_admin_user, DummyPermission.HUB_MANAGE) is True
        assert (
            api.has_permission(
                hub_admin_user, DummyPermission.TERM_GRADE, course_id="c1", term_id="t1"
            )
            is True
        )

    def test_has_permission_no_role(self, api, no_role_user):
        assert (
            api.has_permission(
                no_role_user, DummyPermission.TERM_READ, course_id="math101", term_id="2024ws"
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

    def test_get_registered_permissions(self, api):
        permissions = api.get_registered_permissions()
        assert isinstance(permissions, set)
        assert all(isinstance(p, DummyPermission) for p in permissions)
        all_permissions = DummyPermission.__members__.values()
        assert permissions == set(all_permissions)
