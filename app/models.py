from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from app.enums.task_operations import TaskOperations


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password: str = Field(index=True)
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    disabled: bool = Field(default=False)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Task(BaseModel):
    operation: TaskOperations
    data: str
    id: Optional[str] = None


class RegisterForm(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
