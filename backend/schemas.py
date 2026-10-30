from pydantic import BaseModel, Field
from typing import Literal

TaskType = Literal["review", "debug", "tests", "explain", "build"]

class WorkspaceFile(BaseModel):
    path: str = Field(min_length=1, max_length=180)
    content: str = Field(max_length=60000)

class AgentRequest(BaseModel):
    task_type: TaskType = "debug"
    task: str = Field(min_length=3, max_length=4000)
    files: list[WorkspaceFile] = Field(min_length=1, max_length=12)

class AnalyzeRequest(BaseModel):
    task_type: TaskType = "review"
    code: str = Field(min_length=1, max_length=30000)
    language: str = "python"
