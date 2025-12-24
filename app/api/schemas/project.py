from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    repository_url: str = Field(..., description="Git repository URL")
    description: Optional[str] = Field(None, description="Project description")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


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
