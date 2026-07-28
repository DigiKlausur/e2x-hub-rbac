import json
from posixpath import join as urljoin

import httpx

from .errors import GroupNotFoundError, HubAPIError, InvalidInputError, UserNotFoundError
from .protocol import GroupBackend


class HubAPI(GroupBackend):
    """Client for interacting with JupyterHub's REST API.

    Provides methods for managing users, groups, and group memberships
    with proper error handling and exception wrapping.
    """

    def __init__(self, api_token: str, api_url: str, **kwargs):
        """Initialize the Hub API client.

        Args:
            api_token: JupyterHub API token for authentication.
            api_url: Base URL of the JupyterHub API.
        """
        self.api_token = api_token
        self.api_url = api_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.api_url, headers={"Authorization": f"token {self.api_token}"}
        )

    def _url(self, *parts: str) -> str:
        """Build a full API URL from path segments."""
        return urljoin(self.api_url, *parts)

    @property
    def auth_header(self):
        """Get authorization header for Hub API requests."""
        return {"Authorization": f"token {self.api_token}"}

    async def request(self, url, method="GET", body=None) -> httpx.Response:
        """Make an authenticated request to the Hub API.

        Args:
            url: Full URL to request
            method: HTTP method (GET, POST, DELETE, etc.)
            body: Optional request body (as string)

        Returns:
            HTTP response from the Hub API

        Raises:
            HubAPIError: If the request fails
        """
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        resp = await self._client.request(method, url, headers=headers, content=body)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Let specific methods handle 404s, re-raise others as HubAPIError
            if e.response.status_code == 404:
                raise  # Let caller handle 404s specifically
            raise HubAPIError(f"Hub API request failed: {e.response.status_code}") from e
        return resp

    def _handle_not_found(
        self, error: httpx.HTTPStatusError, resource_type: str, resource_name: str
    ):
        """Convert 404 errors to specific exceptions.

        Args:
            error: The HTTP error to handle
            resource_type: Type of resource ("group" or "user")
            resource_name: Name of the resource

        Raises:
            GroupNotFoundError: If resource_type is "group"
            UserNotFoundError: If resource_type is "user"
            httpx.HTTPStatusError: For other error codes
        """
        if error.response.status_code == 404:
            if resource_type == "group":
                raise GroupNotFoundError(resource_name) from error
            elif resource_type == "user":
                raise UserNotFoundError(resource_name) from error
        raise error

    async def ensure_users_exist(self, usernames: list[str], create_if_missing: bool = True):
        """Ensure that all specified users exist in the Hub, creating them if necessary.

        Args:
            usernames: List of usernames to ensure exist
            create_if_missing: Whether to create missing users

        Raises:
            HubAPIError: If any API request fails
            UserNotFoundError: If create_if_missing is False and some users are missing
        """
        if not usernames:
            return  # Nothing to do
        existing_usernames = await self.filter_existing_users(usernames)
        missing_usernames = set(usernames) - existing_usernames
        if missing_usernames:
            if not create_if_missing:
                raise UserNotFoundError(", ".join(missing_usernames))
            await self.create_users(list(missing_usernames))

    async def ensure_group_exists(self, groupname: str, create_if_missing: bool = True):
        """Ensure that the specified group exists in the Hub, creating it if necessary.

        Args:
            groupname: Name of the group to ensure exists
            create_if_missing: Whether to create the group if it doesn't exist
        Raises:
            HubAPIError: If any API request fails
            GroupNotFoundError: If create_if_missing is False and group are missing
        """
        if not groupname:
            return  # Nothing to do
        try:
            await self.get_group(groupname)
        except GroupNotFoundError:
            if not create_if_missing:
                raise GroupNotFoundError(groupname)
            await self.create_group(groupname)

    async def list_users(self, offset=None):
        """List users from the Hub API with optional pagination.

        Args:
            offset: Starting offset for pagination, None to get all users

        Returns:
            List of user dictionaries from Hub API

        Raises:
            HubAPIError: If the request fails
        """
        if offset is None:
            return await self.list_all_users()
        url = self._url("users") + f"?offset={offset}"
        resp = await self.request(url, method="GET")
        return resp.json()

    async def list_all_users(self):
        """List all users by paginating through results.

        Returns:
            Complete list of all user dictionaries from Hub API

        Raises:
            HubAPIError: If any request fails
        """
        offset = 0
        users = []
        while True:
            batch = await self.list_users(offset)
            if not batch:
                break
            users.extend(batch)
            offset += len(batch)
        return users

    async def filter_existing_users(self, usernames: list):
        """Filter a list of usernames to only those that exist in Hub.

        Args:
            usernames: List of usernames to check

        Returns:
            Set of usernames that exist in the Hub

        Raises:
            HubAPIError: If the user list request fails
        """
        if not usernames:
            return set()

        existing_users = await self.list_all_users()
        existing_usernames = {user["name"] for user in existing_users}
        return set(usernames).intersection(existing_usernames)

    async def get_user(self, username: str):
        """Get information about a user.

        Args:
            username: Username to look up

        Returns:
            User dictionary from Hub API

        Raises:
            UserNotFoundError: If the user doesn't exist
            HubAPIError: If the request fails
        """
        url = self._url("users", username)
        try:
            resp = await self.request(url, method="GET")
            return resp.json()
        except httpx.HTTPStatusError as e:
            self._handle_not_found(e, "user", username)

    async def create_user(self, username: str):
        """Create a single user in the Hub.

        Args:
            username: Username to create

        Returns:
            User dictionary from Hub API

        Raises:
            InvalidInputError: If username is empty
            HubAPIError: If the creation fails
        """
        if not username or not username.strip():
            raise InvalidInputError("Username cannot be empty")

        url = self._url("users", username)
        resp = await self.request(url, method="POST", body="{}")
        return resp.json()

    async def create_users(self, usernames: list):
        """Create multiple users in the Hub in a single request.

        Args:
            usernames: List of usernames to create

        Returns:
            Response from Hub API

        Raises:
            InvalidInputError: If usernames list is empty or contains invalid names
            HubAPIError: If the creation fails
        """
        if not usernames:
            raise InvalidInputError("Usernames list cannot be empty")

        # Filter out empty usernames
        valid_usernames = [u.strip() for u in usernames if u and u.strip()]
        if not valid_usernames:
            raise InvalidInputError("No valid usernames provided")

        url = self._url("users")
        body = {
            "usernames": valid_usernames,
            "admin": False,
        }
        resp = await self.request(url, method="POST", body=json.dumps(body))
        return resp.json()

    async def get_group(self, groupname: str):
        """Get information about a group.

        Args:
            groupname: Name of the group

        Returns:
            Group dictionary from Hub API

        Raises:
            GroupNotFoundError: If the group doesn't exist
            HubAPIError: If the request fails
        """
        url = self._url("groups", groupname)
        try:
            resp = await self.request(url, method="GET")
            return resp.json()
        except httpx.HTTPStatusError as e:
            self._handle_not_found(e, "group", groupname)

    async def get_group_members(self, groupname: str):
        """Get the list of users in a group.

        Args:
            groupname: Name of the group

        Returns:
            List of usernames in the group

        Raises:
            GroupNotFoundError: If the group doesn't exist
            HubAPIError: If the request fails
        """
        group = await self.get_group(groupname)
        return group.get("users", [])

    async def create_group(self, groupname: str):
        """Create a new group in the Hub.

        Args:
            groupname: Name of the group to create

        Returns:
            Group dictionary from Hub API

        Raises:
            InvalidInputError: If groupname is empty
            HubAPIError: If the creation fails
        """
        if not groupname or not groupname.strip():
            raise InvalidInputError("Group name cannot be empty")

        url = self._url("groups", groupname)
        resp = await self.request(url, method="POST", body="{}")
        return resp.json()

    async def delete_group(self, groupname: str):
        """Delete a group from the Hub.

        Args:
            groupname: Name of the group to delete

        Returns:
            Response from Hub API

        Raises:
            GroupNotFoundError: If the group doesn't exist
            HubAPIError: If the deletion fails
        """
        url = self._url("groups", groupname)
        try:
            resp = await self.request(url, method="DELETE")
            return resp.json()
        except httpx.HTTPStatusError as e:
            self._handle_not_found(e, "group", groupname)

    async def add_users_to_group(self, groupname: str, usernames: list):
        """Add users to a group.

        Args:
            groupname: Name of the group
            usernames: List of usernames to add

        Returns:
            Response from Hub API

        Raises:
            GroupNotFoundError: If the group doesn't exist
            InvalidInputError: If usernames list is empty
            HubAPIError: If the operation fails
        """
        if not usernames:
            raise InvalidInputError("Usernames list cannot be empty")

        url = self._url("groups", groupname, "users")
        body = {"users": usernames}
        try:
            resp = await self.request(url, method="POST", body=json.dumps(body))
            return resp.json()
        except httpx.HTTPStatusError as e:
            self._handle_not_found(e, "group", groupname)

    async def remove_users_from_group(self, groupname: str, usernames: list):
        """Remove users from a group.

        Args:
            groupname: Name of the group
            usernames: List of usernames to remove

        Returns:
            Response from Hub API

        Raises:
            GroupNotFoundError: If the group doesn't exist
            InvalidInputError: If usernames list is empty
            HubAPIError: If the operation fails
        """
        if not usernames:
            raise InvalidInputError("Usernames list cannot be empty")

        url = self._url("groups", groupname, "users")
        body = {"users": usernames}
        try:
            resp = await self.request(url, method="DELETE", body=json.dumps(body))
            return resp.json()
        except httpx.HTTPStatusError as e:
            self._handle_not_found(e, "group", groupname)
