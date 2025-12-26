# app/api/schemas/task.py (REPLACE EXISTING FILE)

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    GIT_SYNC = "git_sync"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreate(BaseModel):
    project_id: UUID
    description: str = Field(..., min_length=10)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    additional_context: Optional[str] = Field(None, description="Additional context for the task")


class TaskApproval(BaseModel):
    approved: bool
    feedback: Optional[str] = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    description: str
    status: TaskStatus
    priority: TaskPriority
    plan_path: Optional[str]
    report_path: Optional[str]
    branch_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True