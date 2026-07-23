from typing import Any, Dict, Optional

from .auth.rbac import PermissionProtocol

# --- RFC 9457 HTTP Response Errors ---


class APIError(Exception):
    """
    Base class for all course service errors, RFC 9457-compliant.
    """

    status_code: int = 500
    type_uri: str = "about:blank"
    title: str = "Course Service Error"

    def __init__(self, detail: Optional[str] = None, **extra: Any):
        """
        :param detail: Human-readable explanation specific to this occurrence.
        :param extra: Optional extra fields to include in the problem details JSON.
        """
        self.detail: str = detail or self.title
        self.extra: Dict[str, Any] = extra
        super().__init__(self.detail)


class APIPermissionError(APIError):
    """Exception raised when a user does not have the required permission."""

    status_code: int = 403
    type_uri: str = "urn:e2x:permission-denied"
    title: str = "Permission Denied"
    permission: PermissionProtocol
    course_id: str | None = None
    term_id: str | None = None

    def __init__(
        self,
        username: str,
        permission: PermissionProtocol,
        course_id: str | None = None,
        term_id: str | None = None,
    ):
        self.permission = permission
        self.username = username
        self.course_id = course_id
        self.term_id = term_id
        message = f"User {self.username} does not have permission '{permission.code}'"
        if course_id is not None:
            message += f" for course '{course_id}'"
        if term_id is not None:
            message += f", term '{term_id}'"
        super().__init__(message)
