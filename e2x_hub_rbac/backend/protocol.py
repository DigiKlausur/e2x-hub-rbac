from typing import Protocol, runtime_checkable


@runtime_checkable
class GroupBackend(Protocol):
    """Abstracts the user/group operations needed by RBAC membership management."""

    async def ensure_group_exists(self, group_name: str, create_if_missing: bool) -> None:
        """Ensure a group exists, optionally creating it if it doesn't."""
        ...

    async def ensure_users_exist(self, usernames: list[str], create_if_missing: bool) -> None:
        """Ensure users exist, optionally creating them if they don't."""
        ...

    async def add_users_to_group(self, group_name: str, usernames: list[str]) -> None:
        """Add users to a group."""
        ...

    async def remove_users_from_group(self, group_name: str, usernames: list[str]) -> None:
        """Remove users from a group."""
        ...

    async def get_group_members(self, group_name: str) -> list[str]:
        """Return the current members of a group."""
        ...
