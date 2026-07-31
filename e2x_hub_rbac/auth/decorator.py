import functools
import inspect
from typing import Any, Callable

from ..errors import APIPermissionError
from .rbac import PermissionProtocol, UserLike


def require_permission(permission: PermissionProtocol) -> Callable[..., Any]:
    """Decorator that checks a permission before executing the method.

    Extracts ``user``, ``course_id``, and ``term_id`` from the decorated
    method's arguments (by name).  ``course_id`` and ``term_id`` are
    optional and default to ``None`` when absent.

    The decorated method must live on a class that has a ``permission_checker(user: User)`` method
    that returns a ``PermissionChecker`` instance for the given user.

    Usage::

        @require_permission(Permission.PROFILE_SPAWN_STUDENT)
        def get_student_term_profile(self, user, course_id, term_id):
            ...
    """

    def decorator(method):
        sig = inspect.signature(method)

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            self = arguments["self"]
            user: UserLike = arguments["user"]
            course_id: str | None = arguments.get("course_id")
            term_id: str | None = arguments.get("term_id")

            checker = self.permission_checker(user)
            if not checker.has_permission(permission, course_id=course_id, term_id=term_id):
                raise APIPermissionError(
                    username=user.username,
                    permission=permission,
                    course_id=course_id,
                    term_id=term_id,
                )
            return method(*args, **kwargs)

        return wrapper

    return decorator
