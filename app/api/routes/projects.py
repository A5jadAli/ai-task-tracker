from fastapi import APIRouter, HTTPException
from app.api.schemas.project import ProjectCreate, ProjectResponse
from uuid import uuid4

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Register a new project"""
    # TODO: Implement project creation logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    # TODO: Implement project retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")
