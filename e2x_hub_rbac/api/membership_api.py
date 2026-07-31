from ..auth.decorator import require_permission
from ..auth.rbac import Role, RoleAssignment, UserLike
from ..backend.errors import GroupNotFoundError
from ..backend.protocol import GroupBackend
from ..permissions.membership import MEMBERSHIP_ROLE_PERMISSIONS, MembershipPermission
from .base_api import BaseAPI


class MembershipAPI(BaseAPI):
    """API for managing user memberships in courses and terms."""

    def __init__(self, group_backend: GroupBackend, add_users_to_hub: bool = False):
        super().__init__(role_permissions=MEMBERSHIP_ROLE_PERMISSIONS)
        self._group_backend = group_backend
        self.add_users_to_hub = add_users_to_hub

    @property
    def backend(self) -> GroupBackend:
        return self._group_backend

    async def __add_role_assignment(self, role_assignment: RoleAssignment, usernames: list[str]):
        group_name = role_assignment.group_name
        await self.backend.ensure_group_exists(group_name, create_if_missing=True)
        await self.backend.ensure_users_exist(usernames, create_if_missing=self.add_users_to_hub)
        await self.backend.add_users_to_group(group_name, usernames)

    async def __remove_role_assignment(self, role_assignment: RoleAssignment, usernames: list[str]):
        group_name = role_assignment.group_name
        try:
            current_members = await self.backend.get_group_members(group_name)
            usernames_to_remove = [u for u in usernames if u in current_members]
            await self.backend.remove_users_from_group(group_name, usernames_to_remove)
        except GroupNotFoundError:
            # Group doesn't exist, so no members to remove
            return

    async def __list_role_assignment_members(self, role_assignment: RoleAssignment) -> list[str]:
        group_name = role_assignment.group_name
        try:
            return await self.backend.get_group_members(group_name)
        except GroupNotFoundError:
            return []

    @require_permission(MembershipPermission.ADD_HUB_ADMIN)
    async def add_hub_admins(self, user: UserLike, usernames: list[str]):
        """Add users to the Hub Admin role."""
        role_assignment = RoleAssignment.hub(role=Role.HUB_ADMIN)
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_HUB_ADMIN)
    async def remove_hub_admins(self, user: UserLike, usernames: list[str]):
        """Remove users from the Hub Admin role."""
        role_assignment = RoleAssignment.hub(role=Role.HUB_ADMIN)
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_HUB_ADMINS)
    async def list_hub_admins(self, user: UserLike) -> list[str]:
        """List all users in the Hub Admin role."""
        role_assignment = RoleAssignment.hub(role=Role.HUB_ADMIN)
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_COURSE_CREATOR)
    async def add_course_creators(self, user: UserLike, usernames: list[str]):
        """Add users to the Course Creator role."""
        role_assignment = RoleAssignment.hub(role=Role.COURSE_CREATOR)
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_COURSE_CREATOR)
    async def remove_course_creators(self, user: UserLike, usernames: list[str]):
        """Remove users from the Course Creator role."""
        role_assignment = RoleAssignment.hub(role=Role.COURSE_CREATOR)
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_COURSE_CREATORS)
    async def list_course_creators(self, user: UserLike) -> list[str]:
        """List all users in the Course Creator role."""
        role_assignment = RoleAssignment.hub(role=Role.COURSE_CREATOR)
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_COURSE_OWNER)
    async def add_course_owners(self, user: UserLike, course_id: str, usernames: list[str]):
        """Add users to the Course Owner role for a specific course."""
        role_assignment = RoleAssignment.course(role=Role.COURSE_OWNER, course_id=course_id)
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_COURSE_OWNER)
    async def remove_course_owners(self, user: UserLike, course_id: str, usernames: list[str]):
        """Remove users from the Course Owner role for a specific course."""
        role_assignment = RoleAssignment.course(role=Role.COURSE_OWNER, course_id=course_id)
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_COURSE_OWNERS)
    async def list_course_owners(self, user: UserLike, course_id: str) -> list[str]:
        """List all users in the Course Owner role for a specific course."""
        role_assignment = RoleAssignment.course(role=Role.COURSE_OWNER, course_id=course_id)
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_INSTRUCTOR)
    async def add_instructors(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Add users to the Instructor role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.INSTRUCTOR, course_id=course_id, term_id=term_id
        )
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_INSTRUCTOR)
    async def remove_instructors(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Remove users from the Instructor role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.INSTRUCTOR, course_id=course_id, term_id=term_id
        )
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_INSTRUCTORS)
    async def list_instructors(self, user: UserLike, course_id: str, term_id: str) -> list[str]:
        """List all users in the Instructor role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.INSTRUCTOR, course_id=course_id, term_id=term_id
        )
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_TEACHING_ASSISTANT)
    async def add_teaching_assistants(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Add users to the Teaching Assistant role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.TEACHING_ASSISTANT, course_id=course_id, term_id=term_id
        )
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_TEACHING_ASSISTANT)
    async def remove_teaching_assistants(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Remove users from the Teaching Assistant role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.TEACHING_ASSISTANT, course_id=course_id, term_id=term_id
        )
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_TEACHING_ASSISTANTS)
    async def list_teaching_assistants(
        self, user: UserLike, course_id: str, term_id: str
    ) -> list[str]:
        """List all users in the Teaching Assistant role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.TEACHING_ASSISTANT, course_id=course_id, term_id=term_id
        )
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_OBSERVER)
    async def add_observers(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Add users to the Observer role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.OBSERVER, course_id=course_id, term_id=term_id
        )
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_OBSERVER)
    async def remove_observers(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Remove users from the Observer role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.OBSERVER, course_id=course_id, term_id=term_id
        )
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_OBSERVERS)
    async def list_observers(self, user: UserLike, course_id: str, term_id: str) -> list[str]:
        """List all users in the Observer role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.OBSERVER, course_id=course_id, term_id=term_id
        )
        return await self.__list_role_assignment_members(role_assignment)

    @require_permission(MembershipPermission.ADD_STUDENT)
    async def add_students(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Add users to the Student role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.STUDENT, course_id=course_id, term_id=term_id
        )
        await self.__add_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.REMOVE_STUDENT)
    async def remove_students(
        self, user: UserLike, course_id: str, term_id: str, usernames: list[str]
    ):
        """Remove users from the Student role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.STUDENT, course_id=course_id, term_id=term_id
        )
        await self.__remove_role_assignment(role_assignment, usernames)

    @require_permission(MembershipPermission.LIST_STUDENTS)
    async def list_students(self, user: UserLike, course_id: str, term_id: str) -> list[str]:
        """List all users in the Student role for a specific course and term."""
        role_assignment = RoleAssignment.term(
            role=Role.STUDENT, course_id=course_id, term_id=term_id
        )
        return await self.__list_role_assignment_members(role_assignment)
