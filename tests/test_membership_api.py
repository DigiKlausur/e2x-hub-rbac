"""Tests for MembershipAPI."""

from unittest.mock import AsyncMock, Mock

import pytest

from e2x_hub_rbac.api.membership_api import MembershipAPI
from e2x_hub_rbac.backend.errors import GroupNotFoundError
from e2x_hub_rbac.errors import APIPermissionError

from .conftest import UserStub


@pytest.fixture
def mock_backend():
    """Mock GroupBackend for testing."""
    backend = Mock()
    backend.ensure_group_exists = AsyncMock()
    backend.ensure_users_exist = AsyncMock()
    backend.add_users_to_group = AsyncMock()
    backend.remove_users_from_group = AsyncMock()
    backend.get_group_members = AsyncMock(return_value=[])
    return backend


@pytest.fixture
def membership_api(mock_backend):
    """MembershipAPI instance with mocked backend."""
    return MembershipAPI(group_backend=mock_backend, add_users_to_hub=False)


@pytest.fixture
def membership_api_with_hub_add(mock_backend):
    """MembershipAPI instance with add_users_to_hub enabled."""
    return MembershipAPI(group_backend=mock_backend, add_users_to_hub=True)


class TestMembershipAPIHubAdmins:
    """Tests for hub admin management."""

    @pytest.mark.asyncio
    async def test_add_hub_admins_as_hub_admin(self, membership_api, hub_admin_user, mock_backend):
        usernames = ["user1", "user2"]
        await membership_api.add_hub_admins(hub_admin_user, usernames)

        mock_backend.ensure_group_exists.assert_called_once_with(
            "hub.hub_admin", create_if_missing=True
        )
        mock_backend.ensure_users_exist.assert_called_once_with(usernames, create_if_missing=False)
        mock_backend.add_users_to_group.assert_called_once_with("hub.hub_admin", usernames)

    @pytest.mark.asyncio
    async def test_add_hub_admins_with_hub_add_enabled(
        self, membership_api_with_hub_add, hub_admin_user, mock_backend
    ):
        usernames = ["user1"]
        await membership_api_with_hub_add.add_hub_admins(hub_admin_user, usernames)

        mock_backend.ensure_users_exist.assert_called_once_with(usernames, create_if_missing=True)

    @pytest.mark.asyncio
    async def test_add_hub_admins_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_hub_admins(math101_2024ws_student_user, ["user1"])

    @pytest.mark.asyncio
    async def test_remove_hub_admins_as_hub_admin(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.return_value = ["user1", "user2", "user3"]
        usernames = ["user1", "user2"]
        await membership_api.remove_hub_admins(hub_admin_user, usernames)

        mock_backend.get_group_members.assert_called_once_with("hub.hub_admin")
        mock_backend.remove_users_from_group.assert_called_once_with("hub.hub_admin", usernames)

    @pytest.mark.asyncio
    async def test_remove_hub_admins_filters_non_members(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.return_value = ["user1"]
        usernames = ["user1", "user2"]
        await membership_api.remove_hub_admins(hub_admin_user, usernames)

        # Should only remove user1 since user2 is not a member
        mock_backend.remove_users_from_group.assert_called_once_with("hub.hub_admin", ["user1"])

    @pytest.mark.asyncio
    async def test_remove_hub_admins_group_not_found(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.side_effect = GroupNotFoundError("Group not found")

        # Should not raise - gracefully handles missing group
        await membership_api.remove_hub_admins(hub_admin_user, ["user1"])

        mock_backend.remove_users_from_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_hub_admins_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.remove_hub_admins(math101_2024ws_student_user, ["user1"])

    @pytest.mark.asyncio
    async def test_list_hub_admins_as_hub_admin(self, membership_api, hub_admin_user, mock_backend):
        expected_members = ["admin1", "admin2"]
        mock_backend.get_group_members.return_value = expected_members

        result = await membership_api.list_hub_admins(hub_admin_user)

        assert result == expected_members
        mock_backend.get_group_members.assert_called_once_with("hub.hub_admin")

    @pytest.mark.asyncio
    async def test_list_hub_admins_group_not_found(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.side_effect = GroupNotFoundError("Group not found")

        result = await membership_api.list_hub_admins(hub_admin_user)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_hub_admins_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.list_hub_admins(math101_2024ws_student_user)


class TestMembershipAPICourseCreators:
    """Tests for course creator management."""

    @pytest.mark.asyncio
    async def test_add_course_creators_as_hub_admin(
        self, membership_api, hub_admin_user, mock_backend
    ):
        usernames = ["creator1"]
        await membership_api.add_course_creators(hub_admin_user, usernames)

        mock_backend.ensure_group_exists.assert_called_once_with(
            "hub.course_creator", create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with("hub.course_creator", usernames)

    @pytest.mark.asyncio
    async def test_add_course_creators_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_course_creators(math101_2024ws_student_user, ["creator1"])

    @pytest.mark.asyncio
    async def test_remove_course_creators_as_hub_admin(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.return_value = ["creator1", "creator2"]
        await membership_api.remove_course_creators(hub_admin_user, ["creator1"])

        mock_backend.remove_users_from_group.assert_called_once_with(
            "hub.course_creator", ["creator1"]
        )

    @pytest.mark.asyncio
    async def test_list_course_creators_as_hub_admin(
        self, membership_api, hub_admin_user, mock_backend
    ):
        expected = ["creator1"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_course_creators(hub_admin_user)

        assert result == expected


class TestMembershipAPICourseOwners:
    """Tests for course owner management."""

    @pytest.mark.asyncio
    async def test_add_course_owners_as_hub_admin(
        self, membership_api, hub_admin_user, mock_backend
    ):
        course_id = "math101"
        usernames = ["owner1"]
        await membership_api.add_course_owners(hub_admin_user, course_id, usernames)

        expected_group = "course.math101.course_owner"
        mock_backend.ensure_group_exists.assert_called_once_with(
            expected_group, create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with(expected_group, usernames)

    @pytest.mark.asyncio
    async def test_add_course_owners_as_course_owner(self, membership_api, mock_backend):
        # Create a user who is already a course owner for this course
        course_owner = UserStub(username="owner", groups=["course.math101.course_owner"])
        course_id = "math101"
        usernames = ["new_owner"]

        await membership_api.add_course_owners(course_owner, course_id, usernames)

        mock_backend.add_users_to_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_course_owners_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_course_owners(
                math101_2024ws_student_user, "math101", ["owner1"]
            )

    @pytest.mark.asyncio
    async def test_remove_course_owners(self, membership_api, hub_admin_user, mock_backend):
        course_id = "math101"
        mock_backend.get_group_members.return_value = ["owner1", "owner2"]

        await membership_api.remove_course_owners(hub_admin_user, course_id, ["owner1"])

        mock_backend.remove_users_from_group.assert_called_once_with(
            "course.math101.course_owner", ["owner1"]
        )

    @pytest.mark.asyncio
    async def test_list_course_owners(self, membership_api, hub_admin_user, mock_backend):
        course_id = "math101"
        expected = ["owner1"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_course_owners(hub_admin_user, course_id)

        assert result == expected
        mock_backend.get_group_members.assert_called_once_with("course.math101.course_owner")


class TestMembershipAPIInstructors:
    """Tests for instructor management."""

    @pytest.mark.asyncio
    async def test_add_instructors_as_course_owner(self, membership_api, mock_backend):
        course_owner = UserStub(username="owner", groups=["course.math101.course_owner"])
        course_id = "math101"
        term_id = "2024ws"
        usernames = ["instructor1"]

        await membership_api.add_instructors(course_owner, course_id, term_id, usernames)

        expected_group = "term.math101.2024ws.instructor"
        mock_backend.ensure_group_exists.assert_called_once_with(
            expected_group, create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with(expected_group, usernames)

    @pytest.mark.asyncio
    async def test_add_instructors_as_instructor(self, membership_api, mock_backend):
        instructor = UserStub(username="inst", groups=["term.math101.2024ws.instructor"])

        await membership_api.add_instructors(instructor, "math101", "2024ws", ["new_instructor"])

        mock_backend.add_users_to_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_instructors_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_instructors(
                math101_2024ws_student_user, "math101", "2024ws", ["instructor1"]
            )

    @pytest.mark.asyncio
    async def test_remove_instructors(self, membership_api, hub_admin_user, mock_backend):
        mock_backend.get_group_members.return_value = ["instructor1", "instructor2"]

        await membership_api.remove_instructors(
            hub_admin_user, "math101", "2024ws", ["instructor1"]
        )

        mock_backend.remove_users_from_group.assert_called_once_with(
            "term.math101.2024ws.instructor", ["instructor1"]
        )

    @pytest.mark.asyncio
    async def test_list_instructors(self, membership_api, hub_admin_user, mock_backend):
        expected = ["instructor1"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_instructors(hub_admin_user, "math101", "2024ws")

        assert result == expected


class TestMembershipAPITeachingAssistants:
    """Tests for teaching assistant management."""

    @pytest.mark.asyncio
    async def test_add_teaching_assistants(self, membership_api, hub_admin_user, mock_backend):
        usernames = ["ta1"]
        await membership_api.add_teaching_assistants(hub_admin_user, "math101", "2024ws", usernames)

        expected_group = "term.math101.2024ws.teaching_assistant"
        mock_backend.ensure_group_exists.assert_called_once_with(
            expected_group, create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with(expected_group, usernames)

    @pytest.mark.asyncio
    async def test_add_teaching_assistants_as_instructor(self, membership_api, mock_backend):
        instructor = UserStub(username="inst", groups=["term.math101.2024ws.instructor"])

        await membership_api.add_teaching_assistants(instructor, "math101", "2024ws", ["ta1"])

        mock_backend.add_users_to_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_teaching_assistants(self, membership_api, hub_admin_user, mock_backend):
        mock_backend.get_group_members.return_value = ["ta1", "ta2"]

        await membership_api.remove_teaching_assistants(
            hub_admin_user, "math101", "2024ws", ["ta1"]
        )

        mock_backend.remove_users_from_group.assert_called_once_with(
            "term.math101.2024ws.teaching_assistant", ["ta1"]
        )

    @pytest.mark.asyncio
    async def test_list_teaching_assistants(self, membership_api, hub_admin_user, mock_backend):
        expected = ["ta1"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_teaching_assistants(hub_admin_user, "math101", "2024ws")

        assert result == expected


class TestMembershipAPIObservers:
    """Tests for observer management."""

    @pytest.mark.asyncio
    async def test_add_observers(self, membership_api, hub_admin_user, mock_backend):
        usernames = ["observer1"]
        await membership_api.add_observers(hub_admin_user, "math101", "2024ws", usernames)

        expected_group = "term.math101.2024ws.observer"
        mock_backend.ensure_group_exists.assert_called_once_with(
            expected_group, create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with(expected_group, usernames)

    @pytest.mark.asyncio
    async def test_add_observers_as_instructor(self, membership_api, mock_backend):
        instructor = UserStub(username="inst", groups=["term.math101.2024ws.instructor"])

        await membership_api.add_observers(instructor, "math101", "2024ws", ["observer1"])

        mock_backend.add_users_to_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_observers_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_observers(
                math101_2024ws_student_user, "math101", "2024ws", ["observer1"]
            )

    @pytest.mark.asyncio
    async def test_remove_observers(self, membership_api, hub_admin_user, mock_backend):
        mock_backend.get_group_members.return_value = ["observer1"]

        await membership_api.remove_observers(hub_admin_user, "math101", "2024ws", ["observer1"])

        mock_backend.remove_users_from_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_observers(self, membership_api, hub_admin_user, mock_backend):
        expected = ["observer1"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_observers(hub_admin_user, "math101", "2024ws")

        assert result == expected


class TestMembershipAPIStudents:
    """Tests for student management."""

    @pytest.mark.asyncio
    async def test_add_students_as_instructor(self, membership_api, mock_backend):
        instructor = UserStub(username="inst", groups=["term.math101.2024ws.instructor"])
        usernames = ["student1", "student2"]

        await membership_api.add_students(instructor, "math101", "2024ws", usernames)

        expected_group = "term.math101.2024ws.student"
        mock_backend.ensure_group_exists.assert_called_once_with(
            expected_group, create_if_missing=True
        )
        mock_backend.add_users_to_group.assert_called_once_with(expected_group, usernames)

    @pytest.mark.asyncio
    async def test_add_students_as_teaching_assistant(
        self, membership_api, math101_2024ws_teaching_assistant_user, mock_backend
    ):
        await membership_api.add_students(
            math101_2024ws_teaching_assistant_user, "math101", "2024ws", ["student1"]
        )

        mock_backend.add_users_to_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_students_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        with pytest.raises(APIPermissionError):
            await membership_api.add_students(
                math101_2024ws_student_user, "math101", "2024ws", ["another_student"]
            )

    @pytest.mark.asyncio
    async def test_remove_students(self, membership_api, hub_admin_user, mock_backend):
        mock_backend.get_group_members.return_value = ["student1", "student2"]

        await membership_api.remove_students(hub_admin_user, "math101", "2024ws", ["student1"])

        mock_backend.remove_users_from_group.assert_called_once_with(
            "term.math101.2024ws.student", ["student1"]
        )

    @pytest.mark.asyncio
    async def test_list_students_as_observer(self, membership_api, mock_backend):
        observer = UserStub(username="obs", groups=["term.math101.2024ws.observer"])
        expected = ["student1", "student2"]
        mock_backend.get_group_members.return_value = expected

        result = await membership_api.list_students(observer, "math101", "2024ws")

        assert result == expected

    @pytest.mark.asyncio
    async def test_list_students_permission_denied(
        self, membership_api, math101_2024ws_student_user
    ):
        # Students in a different term shouldn't be able to list students
        different_course_student = UserStub(
            username="alice", groups=["term.phys101.2024ws.student"]
        )

        with pytest.raises(APIPermissionError):
            await membership_api.list_students(different_course_student, "math101", "2024ws")


class TestMembershipAPIBackendProperty:
    """Test the backend property."""

    def test_backend_property(self, membership_api, mock_backend):
        assert membership_api.backend is mock_backend


class TestMembershipAPIEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_add_empty_list_of_users(self, membership_api, hub_admin_user, mock_backend):
        await membership_api.add_hub_admins(hub_admin_user, [])

        mock_backend.ensure_group_exists.assert_called_once()
        mock_backend.ensure_users_exist.assert_called_once_with([], create_if_missing=False)
        mock_backend.add_users_to_group.assert_called_once_with("hub.hub_admin", [])

    @pytest.mark.asyncio
    async def test_remove_from_nonexistent_group(
        self, membership_api, hub_admin_user, mock_backend
    ):
        mock_backend.get_group_members.side_effect = GroupNotFoundError("Not found")

        # Should not raise
        await membership_api.remove_course_creators(hub_admin_user, ["creator1"])

        mock_backend.remove_users_from_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_hub_admin_has_all_permissions(
        self, membership_api, hub_admin_user, mock_backend
    ):
        """Hub admin should be able to perform all membership operations."""
        # Test a few different operations at different scopes
        await membership_api.add_hub_admins(hub_admin_user, ["user1"])
        await membership_api.add_course_owners(hub_admin_user, "course1", ["user2"])
        await membership_api.add_students(hub_admin_user, "course1", "term1", ["user3"])

        # All should succeed without APIPermissionError
        assert mock_backend.add_users_to_group.call_count == 3
