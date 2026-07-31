import functools
import inspect
from typing import Any, Callable

from ..errors import APIPermissionError
from .rbac import PermissionProtocol, UserLike


def require_permission(permission: PermissionProtocol) -> Callable[..., Any]:
    """Decorator that checks a permission before executing the method."""

    def decorator(method):
        sig = inspect.signature(method)

        def check_permission(args, kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            self = arguments["self"]
            user: UserLike = arguments["user"]
            course_id: str | None = arguments.get("course_id")
            term_id: str | None = arguments.get("term_id")

            checker = self.permission_checker(user)
            if not checker.has_permission(
                permission,
                course_id=course_id,
                term_id=term_id,
            ):
                raise APIPermissionError(
                    username=user.username,
                    permission=permission,
                    course_id=course_id,
                    term_id=term_id,
                )

        if inspect.iscoroutinefunction(method):

            @functools.wraps(method)
            async def async_wrapper(*args, **kwargs):
                check_permission(args, kwargs)
                return await method(*args, **kwargs)

            return async_wrapper

        @functools.wraps(method)
        def sync_wrapper(*args, **kwargs):
            check_permission(args, kwargs)
            return method(*args, **kwargs)

        return sync_wrapper

    return decorator
