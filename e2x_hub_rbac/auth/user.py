from typing import List

from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Represents a user in the system.
    """

    username: str
    admin: bool = Field(default=False)
    groups: List[str] = Field(default_factory=list)
