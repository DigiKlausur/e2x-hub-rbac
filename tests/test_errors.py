"""Tests for APIError and APIPermissionError."""

import pytest

from e2x_hub_rbac.errors import APIError, APIPermissionError

from .conftest import Permission


class TestAPIError:
    def test_default_message(self):
        err = APIError()
        assert err.detail == "Course Service Error"
        assert err.status_code == 500

    def test_custom_detail(self):
        err = APIError(detail="Something went wrong")
        assert err.detail == "Something went wrong"
        assert str(err) == "Something went wrong"

    def test_extra_fields(self):
        err = APIError(detail="oops", foo="bar")
        assert err.extra == {"foo": "bar"}

    def test_is_exception(self):
        with pytest.raises(APIError):
            raise APIError()


class TestAPIPermissionError:
    def test_status_code(self):
        err = APIPermissionError("alice", Permission.TERM_READ)
        assert err.status_code == 403

    def test_type_uri(self):
        err = APIPermissionError("alice", Permission.TERM_READ)
        assert err.type_uri == "urn:e2x:permission-denied"

    def test_message_hub_scope(self):
        err = APIPermissionError("alice", Permission.HUB_MANAGE)
        assert "alice" in str(err)
        assert Permission.HUB_MANAGE.code in str(err)

    def test_message_includes_course_id(self):
        err = APIPermissionError("alice", Permission.COURSE_READ, course_id="math101")
        assert "math101" in str(err)

    def test_message_includes_term_id(self):
        err = APIPermissionError(
            "alice", Permission.TERM_READ, course_id="math101", term_id="2024ws"
        )
        assert "2024ws" in str(err)

    def test_attributes(self):
        err = APIPermissionError("alice", Permission.TERM_GRADE, "math101", "2024ws")
        assert err.username == "alice"
        assert err.permission is Permission.TERM_GRADE
        assert err.course_id == "math101"
        assert err.term_id == "2024ws"

    def test_is_api_error(self):
        err = APIPermissionError("alice", Permission.TERM_READ)
        assert isinstance(err, APIError)

    def test_is_exception(self):
        with pytest.raises(APIPermissionError):
            raise APIPermissionError("alice", Permission.TERM_READ)
