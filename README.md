# e2x-hub-rbac

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/e2x-hub-rbac.svg)](https://pypi.org/project/e2x-hub-rbac/)


`e2x-hub-rbac` provides the **management and authorization layer for LMS-like applications running on JupyterHub** within the e2x ecosystem.

It connects JupyterHub's users and groups with the concepts an LMS needs to manage courses, terms, and participants. Rather than implementing a complete LMS itself, the package provides the common infrastructure for managing **who can do what, and where**.

A typical setup looks roughly like this:

```text
                    ┌─────────────────────────┐
                    │       JupyterHub        │
                    │                         │
                    │  Users + Groups         │
                    └────────────┬────────────┘
                                 │
                                 │
                    ┌────────────▼────────────┐
                    │      e2x-hub-rbac       │
                    │                         │
                    │  Roles & Permissions    │
                    │  Scope Resolution       │
                    │  Membership Management  │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
       ┌────────▼───────┐ ┌──────▼──────┐ ┌──────▼──────┐
       │   LMS / Course │ │  Assessment │ │ Other e2x   │
       │   Management   │ │   Services  │ │   Services  │
       └────────────────┘ └─────────────┘ └─────────────┘
```

The idea is to use **JupyterHub as the user and group management infrastructure**, while `e2x-hub-rbac` adds the LMS-specific concepts needed by applications built on top of it.

For example, an LMS-like application may need to answer questions such as:

* Is this user an LMS administrator?
* Can this user create a course?
* Is this user the owner of course `math101`?
* Is this user an instructor for `math101` during the `2024ws` term?
* Can this teaching assistant add students to that term?
* Can this observer view the members of a term?

`e2x-hub-rbac` provides a common way to represent and enforce these relationships.

## What does it provide?

The package has two closely related responsibilities:

1. **Authorization** — Translate JupyterHub group memberships into roles and determine whether a role grants a requested permission.
2. **Membership management** — Provide an API for managing those roles by adding and removing users from the corresponding JupyterHub groups.

The package deliberately does **not** try to be a complete LMS. Course data, terms, assessments, content, and other domain-specific functionality remain the responsibility of consuming applications.

Instead, `e2x-hub-rbac` provides the shared management layer that applications can build upon.

---

## The RBAC Model

The authorization model is based on three hierarchical scopes:

* **LMS** — Global permissions across the LMS.
* **Course** — Permissions for a specific course and all of its terms.
* **Term** — Permissions for a specific course and term.

Users receive roles through JupyterHub group memberships. For example:

```text
lms.lms-admin
lms.course-creator
lms.course.math101.course-owner
lms.course.math101.term.2024ws.instructor
lms.course.math101.term.2024ws.student
```

These groups are interpreted as role assignments:

```text
LMS
└── LMS_ADMIN

LMS
└── COURSE_CREATOR

Course: math101
└── COURSE_OWNER

Course: math101
└── Term: 2024ws
    └── INSTRUCTOR

Course: math101
└── Term: 2024ws
    └── STUDENT
```

Consuming applications then define which permissions each role provides.

For example, an application might define:

```python
class ViewProfile(PermissionProtocol):
    code = "view_profile"
    required_scope = Scope.TERM
```

and decide that `INSTRUCTOR`, `TEACHING_ASSISTANT`, and `STUDENT` can exercise that permission within their respective terms.

This separation is intentional:

* **`e2x-hub-rbac` defines the roles and authorization machinery.**
* **The consuming application defines its permissions and what each role is allowed to do.**
* **JupyterHub stores the users and group memberships.**

---

## Why use it?

An LMS-like application running on JupyterHub typically needs both JupyterHub's infrastructure and LMS-specific authorization concepts.

Without a common layer, every application would have to implement its own:

* Role definitions
* Course and term scoping
* JupyterHub group-name parsing
* Permission checks
* Membership management
* Authorization decorators
* JupyterHub API integration

`e2x-hub-rbac` centralizes these concerns so that multiple e2x services can use the same roles, group conventions, and authorization model.

In short:

> **JupyterHub provides the users and groups; `e2x-hub-rbac` turns those groups into an LMS-oriented management and authorization model.**

The remainder of this document describes the roles, group naming convention, permission resolution, and APIs provided by the package.

---

## Predefined Roles

Roles are fixed and ship with this package.

| Role | Scope | Group name format |
|------|-------|-------------------|
| `LMS_ADMIN` | LMS | `lms.lms-admin` |
| `COURSE_CREATOR` | LMS | `lms.course-creator` |
| `COURSE_OWNER` | Course | `lms.course.{course_id}.course-owner` |
| `INSTRUCTOR` | Term | `lms.course.{course_id}.term.{term_id}.instructor` |
| `TEACHING_ASSISTANT` | Term | `lms.course.{course_id}.term.{term_id}.teaching_assistant` |
| `OBSERVER` | Term | `lms.course.{course_id}.term.{term_id}.observer` |
| `STUDENT` | Term | `lms.course.{course_id}.term.{term_id}.student` |

---

## Group Names

JupyterHub group memberships are automatically parsed into role assignments based on a structured naming convention. Each group name encodes the role scope and identifiers.

### Format

Group names follow these patterns:

- **LMS-level roles**: `lms.<role_name>`
- **Course-level roles**: `lms.course.<course_id>.<role_name>`
- **Term-level roles**: `lms.course.<course_id>.term.<term_id>.<role_name>`

### Examples

```
lms.lms-admin                                      # LMS admin (global access)
lms.course-creator                                 # Can create courses (global)
lms.course.math101.course-owner                    # Owner of course math101
lms.course.math101.term.2024ws.instructor          # Instructor for math101 in 2024ws
lms.course.math101..2024ws.teaching_assistant  # TA for math101 in 2024ws
lms.course.cs101.term.2024ss.student               # Student in cs101 for 2024ss
lms.course.physics201.term.2025ws.observer         # Observer in physics201 for 2025ws
```

### Parsing Rules

- Group names are case-sensitive and use dot (`.`) as the separator.
- Only group names matching the expected formats are parsed; others are silently ignored.
- The role name must exactly match one of the predefined roles at the correct scope.
- Course IDs and term IDs can contain any characters except dots.

### Invalid Examples

These group names will be ignored during parsing:

```
admin                                        # Missing scope prefix
lms.invalid_role                             # Unknown role name
lms.course.math101                           # Missing role name
lms.course.math101.math101.term.instructor   # Missing term_id
lms.course.math101.student                   # Wrong scope for student role
```

---

## Permission Resolution

- **Lms** roles apply globally to any resource.
- **Course** roles apply to their course and all terms within it.
- **Term** roles apply only to their specific course + term combination.

---

## 📦 Installation

### From PyPI

```bash
pip install e2x-hub-rbac
```

### From Source

```bash
git clone https://github.com/Digiklausur/e2x-hub-rbac.git
cd e2x-hub-rbac
pip install -e .
```

---

## Architecture

This package provides two main components:

1. **Permission System**: Check if users have specific permissions based on their role assignments
2. **Membership API**: Manage user memberships in courses and terms (add/remove users from roles)

---

## Usage

### 1. Define your permissions

`PermissionProtocol` is a structural protocol — implement it with class-level `code` and `required_scope` attributes.

```python
from e2x_hub_rbac.auth import Scope, PermissionProtocol, Role, RolePermissions

class Permission(PermissionProtocol):
    code = "view_profile"
    required_scope = Scope.TERM

ROLE_PERMISSIONS: RolePermissions = {
    Role.LMS_ADMIN:           frozenset({Permission}),
    Role.COURSE_CREATOR:      frozenset(),
    Role.COURSE_OWNER:        frozenset({Permission}),
    Role.INSTRUCTOR:          frozenset({Permission}),
    Role.TEACHING_ASSISTANT:  frozenset({Permission}),
    Role.OBSERVER:            frozenset({Permission}),
    Role.STUDENT:             frozenset({Permission}),
}
```

> **Note:** `ROLE_PERMISSIONS` must include an entry for every `Role` value, because the checker looks up each of the user's assigned roles in this mapping.

### 2. Check permissions directly

```python
from e2x_hub_rbac.auth import UserLike, PermissionChecker

from dataclasses import dataclass

@dataclass
class User:
    """Example user representation."""

    username: str
    groups: list[str]

alice = User(username="alice", groups=["lms.course.math101.term.2024ws.student"])
checker = PermissionChecker(alice, ROLE_PERMISSIONS)

checker.has_permission(Permission, course_id="math101", term_id="2024ws")  # True
checker.has_permission(Permission, course_id="cs101",   term_id="2024ws")  # False
```

### 3. Use the decorator with `BaseAPI`

Extend `BaseAPI` and annotate methods with `@require_permission`. The decorator resolves `user`, `course_id`, and `term_id` from the method arguments by name.

```python
from e2x_hub_rbac.api import BaseAPI
from e2x_hub_rbac.auth import UserLike, require_permission

class MyAPI(BaseAPI):
    def __init__(self):
        super().__init__(role_permissions=ROLE_PERMISSIONS)

    @require_permission(Permission)
    def get_profile(self, user, course_id, term_id):
        return {"profile": "data"}

api.get_profile(alice, "math101", "2024ws")  # succeeds
api.get_profile(alice, "cs101",   "2024ws")  # raises APIPermissionError (403)
```

`APIPermissionError` is RFC 9457-compliant and carries `status_code = 403`.

---

## Managing Memberships

The `MembershipAPI` provides methods to add, remove, and list users in various roles. It requires a backend implementation of the `GroupBackend` protocol.

### Backend Setup

The package includes a `HubAPI` backend for JupyterHub:

```python
from e2x_hub_rbac.backend import HubAPI
from e2x_hub_rbac.api import MembershipAPI

# Initialize the JupyterHub backend
hub_backend = HubAPI(
    api_token="your-jupyterhub-api-token",
    api_url="https://your-hub.example.com/hub/api"
)

# Create the membership API
membership_api = MembershipAPI(
    group_backend=hub_backend,
    add_users_to_hub=True,     # Automatically create users if they don't exist
    delete_empty_groups=True,  # Delete a group once its last member is removed
)
```

### LMS-Level Operations

Manage lms administrators and course creators:

```python
from e2x_hub_rbac.auth import UserLike

# Admin user who can manage memberships
admin = User(username="admin", groups=["lms.lms-admin"])

# Add/remove lms admins
await membership_api.add_lms_admins(admin, ["user1", "user2"])
await membership_api.remove_lms_admins(admin, ["user1"])
admins = await membership_api.list_lms_admins(admin)

# Add/remove course creators
await membership_api.add_course_creators(admin, ["instructor1"])
await membership_api.remove_course_creators(admin, ["instructor1"])
creators = await membership_api.list_course_creators(admin)
```

### Course-Level Operations

Manage course owners:

```python
# Add/remove course owners
await membership_api.add_course_owners(admin, "math101", ["prof_smith"])
await membership_api.remove_course_owners(admin, "math101", ["prof_smith"])
owners = await membership_api.list_course_owners(admin, "math101")
```

### Term-Level Operations

Manage instructors, teaching assistants, observers, and students:

```python
course_id = "math101"
term_id = "2024ws"

# Instructors
await membership_api.add_instructors(admin, course_id, term_id, ["instructor1"])
await membership_api.remove_instructors(admin, course_id, term_id, ["instructor1"])
instructors = await membership_api.list_instructors(admin, course_id, term_id)

# Teaching Assistants
await membership_api.add_teaching_assistants(admin, course_id, term_id, ["ta1", "ta2"])
await membership_api.remove_teaching_assistants(admin, course_id, term_id, ["ta1"])
tas = await membership_api.list_teaching_assistants(admin, course_id, term_id)

# Observers
await membership_api.add_observers(admin, course_id, term_id, ["observer1"])
await membership_api.remove_observers(admin, course_id, term_id, ["observer1"])
observers = await membership_api.list_observers(admin, course_id, term_id)

# Students
await membership_api.add_students(admin, course_id, term_id, ["alice", "bob"])
await membership_api.remove_students(admin, course_id, term_id, ["alice"])
students = await membership_api.list_students(admin, course_id, term_id)
```

### Permission-Based Access Control

All membership operations are protected by permissions. Different roles can perform different operations:

| Operation | Required Permission | Who Can Do It |
|-----------|-------------------|---------------|
| Manage LMS admins | LMS-scoped | LMS admins only |
| Manage course creators | LMS-scoped | LMS admins only |
| Manage course owners | Course-scoped | LMS admins, course owners |
| Manage instructors | Term-scoped | LMS admins, course owners, instructors |
| Manage TAs | Term-scoped | LMS admins, course owners, instructors |
| Manage observers | Term-scoped | LMS admins, course owners, instructors |
| Manage students | Term-scoped | LMS admins, course owners, instructors, TAs |
| List term members | Term-scoped | LMS admins, course owners, instructors, TAs, observers |

Example of permission checking:

```python
# Course owner can manage their course
course_owner = User(username="prof", groups=["lms.course.math101.course-owner"])
await membership_api.add_students(course_owner, "math101", "2024ws", ["student1"])  # ✓ Succeeds

# But cannot manage a different course
await membership_api.add_students(course_owner, "cs101", "2024ws", ["student1"])  # ✗ Raises APIPermissionError

# Teaching assistant can add students
ta = User(username="ta", groups=["lms.course.math101.term.2024ws.teaching-assistant"])
await membership_api.add_students(ta, "math101", "2024ws", ["student2"])  # ✓ Succeeds

# But cannot remove instructors
await membership_api.remove_instructors(ta, "math101", "2024ws", ["instructor1"])  # ✗ Raises APIPermissionError
```

### Custom Backend Implementation

You can implement your own backend by implementing the `GroupBackend` protocol:

```python
from e2x_hub_rbac.backend.protocol import GroupBackend

class CustomBackend(GroupBackend):
    async def ensure_group_exists(self, group_name: str, create_if_missing: bool) -> None:
        # Your implementation
        ...

    async def ensure_users_exist(self, usernames: list[str], create_if_missing: bool) -> None:
        # Your implementation
        ...

    async def add_users_to_group(self, group_name: str, usernames: list[str]) -> None:
        # Your implementation
        ...

    async def remove_users_from_group(self, group_name: str, usernames: list[str]) -> None:
        # Your implementation
        ...

    async def get_group_members(self, group_name: str) -> list[str]:
        # Your implementation
        ...

    async def delete_group(self, group_name: str) -> None:
        # Your implementation
        ...
```

---

## 🛠️ Development

### Setup

```bash
git clone https://github.com/Digiklausur/e2x-hub-rbac.git
cd e2x-hub-rbac
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pip install -e ".[test]"
pytest
```

The test suite includes:
- Permission checker tests
- Decorator tests
- MembershipAPI tests (requires `pytest-asyncio`)
- RBAC tests

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📧 Contact

For questions or support, please contact [Tim Metzler](mailto:tim.metzler@h-brs.de).

---

## 🔗 Links

- [GitHub Repository](https://github.com/Digiklausur/e2x-hub-rbac)
- [Issues](https://github.com/Digiklausur/e2x-hub-rbac/issues)
- [PyPI Package](https://pypi.org/project/e2x-hub-rbac/)