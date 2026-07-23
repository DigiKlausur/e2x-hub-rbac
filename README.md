# e2x-hub-rbac

Role-Based Access Control (RBAC) for JupyterHub within the e2x ecosystem, supporting hierarchical scopes (Hub, Course, Term) based on JupyterHub groups.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/e2x-hub-rbac.svg)](https://pypi.org/project/e2x-hub-rbac/)

---

## Overview

`e2x-hub-rbac` maps JupyterHub group memberships to predefined roles, and lets consuming packages attach permissions to those roles.

The core idea:

1. A user's JupyterHub groups are parsed into **role assignments** at a specific scope (Hub, Course, or Term).
2. Consuming packages define **permissions** and a **role → permissions** mapping.
3. The `PermissionChecker` (or the `require_permission` decorator) evaluates whether a user's roles grant a requested permission within the given scope.

---

## Predefined Roles

Roles are fixed and ship with this package.

| Role | Scope | Group name format |
|------|-------|-------------------|
| `HUB_ADMIN` | Hub | `hub.hub_admin` |
| `COURSE_CREATOR` | Hub | `hub.course_creator` |
| `COURSE_ADMIN` | Course | `course.{course_id}.course_admin` |
| `TERM_ADMIN` | Term | `term.{course_id}.{term_id}.term_admin` |
| `GRADER` | Term | `term.{course_id}.{term_id}.grader` |
| `STUDENT` | Term | `term.{course_id}.{term_id}.student` |

## Permission Resolution

- **Hub** roles apply globally to any resource.
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

## Usage

### 1. Define your permissions

`PermissionProtocol` is a structural protocol — implement it with class-level `code` and `required_scope` attributes.

```python
from e2x_hub_rbac.auth import Scope, PermissionProtocol, Role, RolePermissions

class Permission(PermissionProtocol):
    code = "view_profile"
    required_scope = Scope.TERM

ROLE_PERMISSIONS: RolePermissions = {
    Role.HUB_ADMIN:      frozenset({Permission}),
    Role.COURSE_CREATOR: frozenset(),
    Role.COURSE_ADMIN:   frozenset({Permission}),
    Role.TERM_ADMIN:     frozenset({Permission}),
    Role.GRADER:         frozenset({Permission}),
    Role.STUDENT:        frozenset({Permission}),
}
```

> **Note:** `ROLE_PERMISSIONS` must include an entry for every `Role` value, because the checker looks up each of the user's assigned roles in this mapping.

### 2. Check permissions directly

```python
from e2x_hub_rbac.auth import User, PermissionChecker

user = User(username="alice", groups=["term.math101.2024ws.student"])
checker = PermissionChecker(user, ROLE_PERMISSIONS)

checker.has_permission(Permission, course_id="math101", term_id="2024ws")  # True
checker.has_permission(Permission, course_id="cs101",   term_id="2024ws")  # False
```

### 3. Use the decorator with `BaseAPI`

Extend `BaseAPI` and annotate methods with `@require_permission`. The decorator resolves `user`, `course_id`, and `term_id` from the method arguments by name.

```python
from e2x_hub_rbac.api import BaseAPI
from e2x_hub_rbac.auth import require_permission

class MyAPI(BaseAPI):
    def __init__(self):
        super().__init__(role_permissions=ROLE_PERMISSIONS)

    @require_permission(Permission)
    def get_profile(self, user, course_id, term_id):
        return {"profile": "data"}

api = MyAPI()
alice = User(username="alice", groups=["term.math101.2024ws.student"])

api.get_profile(alice, "math101", "2024ws")  # succeeds
api.get_profile(alice, "cs101",   "2024ws")  # raises APIPermissionError (403)
```

`APIPermissionError` is RFC 9457-compliant and carries `status_code = 403`.

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
