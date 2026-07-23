import pytest
from pydantic import ValidationError

from e2x_hub_rbac.auth.user import User


class TestUser:
    def test_defaults(self):
        user = User(username="alice")
        assert user.username == "alice"
        assert user.admin is False
        assert user.groups == []

    def test_explicit_fields(self):
        user = User(username="bob", admin=True, groups=["hub.hub_admin"])
        assert user.admin is True
        assert user.groups == ["hub.hub_admin"]

    def test_username_required(self):
        with pytest.raises(ValidationError):
            User()

    def test_groups_is_a_list_copy(self):
        """Mutating the returned list should not affect the model."""
        user = User(username="alice", groups=["a"])
        user.groups.append("b")
        assert user.groups == ["a", "b"]  # pydantic v2 returns a mutable list on the model

    def test_multiple_groups(self):
        groups = ["term.math101.2024ws.student", "term.phys201.2024ws.grader"]
        user = User(username="alice", groups=groups)
        assert user.groups == groups
