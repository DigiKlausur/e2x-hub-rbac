from ..auth.rbac import PermissionEnum, Role, RolePermissions, Scope


class MembershipPermission(PermissionEnum):
    """Permissions related to membership management."""

    # ------------------------------
    # Hub-level permissions
    # -----------------------------
    ADD_HUB_ADMIN = ("membership.hub.add_hub_admin", Scope.HUB)
    REMOVE_HUB_ADMIN = ("membership.hub.remove_hub_admin", Scope.HUB)
    LIST_HUB_ADMINS = ("membership.hub.list_hub_admins", Scope.HUB)

    ADD_COURSE_CREATOR = ("membership.hub.add_course_creator", Scope.HUB)
    REMOVE_COURSE_CREATOR = ("membership.hub.remove_course_creator", Scope.HUB)
    LIST_COURSE_CREATORS = ("membership.hub.list_course_creators", Scope.HUB)

    # ------------------------------
    # Course-level permissions
    # -----------------------------
    ADD_COURSE_OWNER = ("membership.course.add_course_owner", Scope.COURSE)
    REMOVE_COURSE_OWNER = ("membership.course.remove_course_owner", Scope.COURSE)
    LIST_COURSE_OWNERS = ("membership.course.list_course_owners", Scope.COURSE)

    # ------------------------------
    # Term-level permissions
    # -----------------------------
    ADD_INSTRUCTOR = ("membership.term.add_instructor", Scope.TERM)
    REMOVE_INSTRUCTOR = ("membership.term.remove_instructor", Scope.TERM)
    LIST_INSTRUCTORS = ("membership.term.list_instructors", Scope.TERM)

    ADD_TEACHING_ASSISTANT = ("membership.term.add_teaching_assistant", Scope.TERM)
    REMOVE_TEACHING_ASSISTANT = ("membership.term.remove_teaching_assistant", Scope.TERM)
    LIST_TEACHING_ASSISTANTS = ("membership.term.list_teaching_assistants", Scope.TERM)

    ADD_OBSERVER = ("membership.term.add_observer", Scope.TERM)
    REMOVE_OBSERVER = ("membership.term.remove_observer", Scope.TERM)
    LIST_OBSERVERS = ("membership.term.list_observers", Scope.TERM)

    ADD_STUDENT = ("membership.term.add_student", Scope.TERM)
    REMOVE_STUDENT = ("membership.term.remove_student", Scope.TERM)
    LIST_STUDENTS = ("membership.term.list_students", Scope.TERM)


class MembershipPermissionSets:
    """Predefined sets of membership permissions for convenience."""

    MANAGE_HUB_ADMINS = frozenset(
        [
            MembershipPermission.ADD_HUB_ADMIN,
            MembershipPermission.REMOVE_HUB_ADMIN,
            MembershipPermission.LIST_HUB_ADMINS,
        ]
    )

    MANAGE_COURSE_CREATORS = frozenset(
        [
            MembershipPermission.ADD_COURSE_CREATOR,
            MembershipPermission.REMOVE_COURSE_CREATOR,
            MembershipPermission.LIST_COURSE_CREATORS,
        ]
    )

    MANAGE_COURSE_OWNERS = frozenset(
        [
            MembershipPermission.ADD_COURSE_OWNER,
            MembershipPermission.REMOVE_COURSE_OWNER,
            MembershipPermission.LIST_COURSE_OWNERS,
        ]
    )

    MANAGE_INSTRUCTORS = frozenset(
        [
            MembershipPermission.ADD_INSTRUCTOR,
            MembershipPermission.REMOVE_INSTRUCTOR,
            MembershipPermission.LIST_INSTRUCTORS,
        ]
    )

    MANAGE_TEACHING_ASSISTANTS = frozenset(
        [
            MembershipPermission.ADD_TEACHING_ASSISTANT,
            MembershipPermission.REMOVE_TEACHING_ASSISTANT,
            MembershipPermission.LIST_TEACHING_ASSISTANTS,
        ]
    )

    MANAGE_OBSERVERS = frozenset(
        [
            MembershipPermission.ADD_OBSERVER,
            MembershipPermission.REMOVE_OBSERVER,
            MembershipPermission.LIST_OBSERVERS,
        ]
    )

    MANAGE_STUDENTS = frozenset(
        [
            MembershipPermission.ADD_STUDENT,
            MembershipPermission.REMOVE_STUDENT,
            MembershipPermission.LIST_STUDENTS,
        ]
    )

    VIEW_TERM_MEMBERS = frozenset(
        [
            MembershipPermission.LIST_COURSE_OWNERS,
            MembershipPermission.LIST_INSTRUCTORS,
            MembershipPermission.LIST_TEACHING_ASSISTANTS,
            MembershipPermission.LIST_OBSERVERS,
            MembershipPermission.LIST_STUDENTS,
        ]
    )

    COURSE_STAFF_PERMISSIONS = frozenset(
        MANAGE_INSTRUCTORS | MANAGE_TEACHING_ASSISTANTS | MANAGE_OBSERVERS | MANAGE_STUDENTS
    )


MEMBERSHIP_ROLE_PERMISSIONS: RolePermissions = {
    Role.HUB_ADMIN: frozenset(
        MembershipPermissionSets.MANAGE_HUB_ADMINS
        | MembershipPermissionSets.MANAGE_COURSE_CREATORS
        | MembershipPermissionSets.MANAGE_COURSE_OWNERS
        | MembershipPermissionSets.MANAGE_INSTRUCTORS
        | MembershipPermissionSets.MANAGE_TEACHING_ASSISTANTS
        | MembershipPermissionSets.MANAGE_OBSERVERS
        | MembershipPermissionSets.MANAGE_STUDENTS
    ),
    Role.COURSE_CREATOR: frozenset(),
    Role.COURSE_OWNER: frozenset(
        MembershipPermissionSets.MANAGE_COURSE_OWNERS
        | MembershipPermissionSets.COURSE_STAFF_PERMISSIONS
    ),
    Role.INSTRUCTOR: frozenset(
        MembershipPermissionSets.COURSE_STAFF_PERMISSIONS
        | MembershipPermissionSets.VIEW_TERM_MEMBERS
    ),
    Role.TEACHING_ASSISTANT: frozenset([MembershipPermission.ADD_STUDENT])
    | MembershipPermissionSets.VIEW_TERM_MEMBERS,
    Role.OBSERVER: frozenset(MembershipPermissionSets.VIEW_TERM_MEMBERS),
    Role.STUDENT: frozenset(),
}
