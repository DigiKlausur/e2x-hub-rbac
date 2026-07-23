# e2x-hub-rbac

Role-Based Access Control (RBAC) for JupyterHub within the e2x ecosystem, supporting hierarchical scopes (Hub, Course, Term) based on JupyterHub groups.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/e2x-hub-rbac.svg)](https://pypi.org/project/e2x-hub-rbac/)

---

## 📌 Overview

`e2x-hub-rbac` provides a flexible and scalable Role-Based Access Control system for JupyterHub, designed to work seamlessly within the e2x ecosystem. It enables fine-grained permission management across three hierarchical scopes:

- **Hub-level**: Global permissions for administrators and course creators
- **Course-level**: Permissions scoped to specific courses
- **Term-level**: Permissions scoped to specific terms within courses

Permissions are enforced using decorators and integrated with JupyterHub's group system, allowing for dynamic role assignments and permission checks.

---

## 🚀 Features

- ✅ **Hierarchical Scopes**: Manage permissions at Hub, Course, and Term levels
- ✅ **Role-Based Permissions**: Predefined roles with specific permissions (e.g., `HUB_ADMIN`, `COURSE_ADMIN`, `STUDENT`)
- ✅ **Decorator-Based Enforcement**: Easy-to-use decorators for permission checks in API endpoints
- ✅ **JupyterHub Integration**: Leverages JupyterHub groups for role assignments
- ✅ **RFC 9457 Compliant Errors**: Structured error responses for permission denials
- ✅ **Extensible**: Custom permissions can be added as needed

## Group Naming Convention

Roles are derived from JupyterHub group names.

| Scope | Pattern | Example |
|---|---|---|
| Hub | `{role}` | `hub_admin` |
| Course | `course.{course_id}.{role}` | `course.cs101.course_admin` |
| Term | `term.{course_id}.{term_id}.{role}` | `term.cs101.2024_ws.student` |

The final group segment determines the assigned role.

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

## 🏗️ Architecture

### Core Components

| Component | Description |
|-----------|-------------|
| `User` | Represents a user with username, admin status, and group memberships |
| `Role` | Defines roles with hierarchical scopes (Hub, Course, Term) |
| `PermissionProtocol` | Interface for defining permissions |
| `RoleAssignment` | Associates roles with users at specific scopes |
| `require_permission` | Decorator for enforcing permissions on methods |

### Scopes

| Scope | Description |
|-------|-------------|
| `HUB` | Global permissions for the entire JupyterHub instance |
| `COURSE` | Permissions scoped to a specific course |
| `TERM` | Permissions scoped to a specific term within a course |

### Roles

| Role | Scope | Description |
|------|-------|-------------|
| `HUB_ADMIN` | Hub | Full administrative access to the entire JupyterHub instance |
| `COURSE_CREATOR` | Hub | Can create new courses |
| `COURSE_ADMIN` | Course | Administrative access to a specific course |
| `TERM_ADMIN` | Term | Administrative access to a specific term within a course |
| `GRADER` | Term | Can grade assignments within a term |
| `STUDENT` | Term | Standard student access within a term |

---

## 🔧 Usage

### Permission Decorator

Use the `require_permission` decorator to enforce permissions on methods:

```python
from e2x_hub_rbac.auth import (
    User,
    PermissionProtocol,
    RolePermissions,
    Role,
    Scope,
    require_permission,
)
from typing import Optional
from e2x_hub_rbac.api import BaseAPI
from logging import Logger


class MyPermission(PermissionProtocol):
    code = "my_permission"
    required_scope = Scope.TERM


# Define the mapping from roles to permissions
ROLE_PERMISSIONS: RolePermissions = {
    Role.COURSE_ADMIN: frozenset({MyPermission}),
    Role.STUDENT: frozenset(),
    # Add more roles and permissions here...
}


class MyAPI(BaseAPI):
    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(role_permissions=ROLE_PERMISSIONS)

    @require_permission(MyPermission)
    def get_student_term_profile(self, user, course_id, term_id):
        return {"profile": "data"}


api = MyAPI()

alice = User(username="Alice", groups=["course.cs101.course_admin"])

api.get_student_term_profile(alice, "cs101", "AnyTerm") # Succeeds
api.get_student_term_profile(
    alice, "math101", "AnyTerm"
)  # Fails with APIPermissionError

```

---

## 📚 Examples

### Example 1: Basic Permission Check

```python
from e2x_hub_rbac.auth.user import User
from e2x_hub_rbac.auth.rbac import (
    Role,
    Scope,
    PermissionProtocol,
    PermissionChecker,
    RolePermissions,
)


class ProfilePermission(PermissionProtocol):
    code = "profile_access"
    required_scope = Scope.TERM


# Define the mapping from roles to permissions
ROLE_PERMISSIONS: RolePermissions = {
    Role.STUDENT: frozenset({ProfilePermission}),
    # Add more roles and permissions here...
}

# Create a user with a student role
user = User(username="alice", groups=["term.math101.2024_ws.student"])

# Check permission
checker = PermissionChecker(user, ROLE_PERMISSIONS)
has_permission = checker.has_permission(
    ProfilePermission, course_id="math101", term_id="2024_ws"
)
print(f"Has permission: {has_permission}")  # True

has_permission = checker.has_permission(
    ProfilePermission, course_id="cs101", term_id="2024_ws"
)
print(f"Has permission: {has_permission}")  # False

```

### Example 2: Course-Level Permission

```python
from e2x_hub_rbac.auth.user import User
from e2x_hub_rbac.auth.rbac import (
    Role,
    Scope,
    PermissionProtocol,
    PermissionChecker,
    RolePermissions,
)


class ViewCoursePermission(PermissionProtocol):
    code = "view_course"
    required_scope = Scope.COURSE


# Define the mapping from roles to permissions
ROLE_PERMISSIONS: RolePermissions = {
    Role.COURSE_ADMIN: frozenset({ViewCoursePermission}),
    # Add more roles and permissions here...
}

# Create a user with a student role
user = User(username="alice", groups=["course.math101.course_admin"])

# Check permission
checker = PermissionChecker(user, ROLE_PERMISSIONS)
has_permission = checker.has_permission(
    ViewCoursePermission, course_id="math101"
)
print(f"Has permission: {has_permission}")  # True

has_permission = checker.has_permission(
    ViewCoursePermission, course_id="cs101"
)
print(f"Has permission: {has_permission}")  # False
```

---

## 🛠️ Development

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/Digiklausur/e2x-hub-rbac.git
cd e2x-hub-rbac

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
make html
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
