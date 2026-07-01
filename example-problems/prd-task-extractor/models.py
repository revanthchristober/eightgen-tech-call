from typing import Literal
from pydantic import BaseModel, field_validator

Priority = Literal["high", "medium", "low"]


class PRDInput(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("PRD text must not be empty")
        return v


class Task(BaseModel):
    task_name: str
    description: str
    priority: Priority


class TaskList(BaseModel):
    tasks: list[Task]
