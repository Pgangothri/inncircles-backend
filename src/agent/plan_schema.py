from enum import Enum
from typing import List
from pydantic import BaseModel

class AgentEnum(str, Enum):
    DocumentAgent = "document_agent"
    QuestionAgent = "question_agent"
    RetrievalAgent = "retrieval_agent"
    ReadAgent = "read_agent"
    ShellAgent = "shell_agent"
    VisionAgent = "vision_agent"
    CodeAgent = "code_agent"
    ComputerAgent = "computer_agent"

class Subtask(BaseModel):
    step: int
    description: str
    assigned_agent: AgentEnum

class Plan(BaseModel):
    goal: str
    subtasks: List[Subtask]
