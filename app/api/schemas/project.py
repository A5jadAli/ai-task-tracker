# app/api/schemas/project.py (REPLACE EXISTING FILE)

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    repository_url: str = Field(..., description="Git repository URL")
    description: Optional[str] = Field(None, description="Project description")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating project"""
    name: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    repository_url: str
    description: Optional[str]
    local_path: str
    main_branch: str
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True