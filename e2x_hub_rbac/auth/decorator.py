import functools
import inspect
from typing import Any, Callable, Protocol

from ..errors import APIPermissionError
from .rbac import PermissionChecker, PermissionProtocol, UserLike


class HasPermissionChecker(Protocol):
    def permission_checker(self, user: UserLike) -> PermissionChecker: ...


def require_permission(permission: PermissionProtocol) -> Callable[..., Any]:
    """Decorator that checks a permission before executing a method.

    The decorated callable must:

    - be an instance method
    - accept a ``user`` parameter
    - belong to a class implementing ``permission_checker(user)``
    """

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(method)

        def _authorize(*args, **kwargs) -> None:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            self: HasPermissionChecker = arguments["self"]
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
                _authorize(*args, **kwargs)
                return await method(*args, **kwargs)

            return async_wrapper

        @functools.wraps(method)
        def sync_wrapper(*args, **kwargs):
            _authorize(*args, **kwargs)
            return method(*args, **kwargs)

        return sync_wrapper

    return decorator
