from ..errors import APIError


class HubAPIError(APIError):
    """Base exception for all Hub API errors."""

    pass


class GroupNotFoundError(HubAPIError):
    """Raised when a requested group is not found in the Hub API."""

    def __init__(self, groupname: str):
        self.groupname = groupname
        super().__init__(f"Group '{groupname}' not found")


class UserNotFoundError(HubAPIError):
    """Raised when a requested user is not found in the Hub API."""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User '{username}' not found")


class InvalidInputError(HubAPIError):
    """Raised when input validation fails."""

    pass
