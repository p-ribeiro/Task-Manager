from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password: str = Field(index=True)
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    disabled: bool = Field(default=False)
