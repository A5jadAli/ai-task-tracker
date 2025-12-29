from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.models.database import get_db, Project
from app.agents.git_agent import GitAgent
from app.memory.project_memory import ProjectMemory
from app.config import settings
from loguru import logger
from pathlib import Path
import uuid

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Register a new project"""
    try:
        logger.info(f"Creating project: {project.name}")

        # Create project instance
        db_project = Project(
            id=uuid.uuid4(),
            name=project.name,
            repository_url=project.repository_url,
            description=project.description,
            context=project.context or {},
        )

        # Clone repository
        git_agent = GitAgent()
        local_path = settings.PROJECTS_BASE_PATH / str(db_project.id)

        try:
            await git_agent.clone_repository(project.repository_url, local_path)
            db_project.local_path = str(local_path)

            # Detect main branch
            main_branch = await git_agent.detect_main_branch(local_path)
            db_project.main_branch = main_branch

        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise HTTPException(
                status_code=400, detail=f"Failed to clone repository: {str(e)}"
            )

        # Extract and save project context
        project_memory = ProjectMemory(str(db_project.id))
        extracted_context = await project_memory.extract_context_from_project(
            local_path
        )
        extracted_context.update(project.context or {})
        await project_memory.save_context(extracted_context)

        db_project.context = extracted_context

        # Save to database
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        logger.info(f"Project created successfully: {db_project.id}")
        return db_project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create project: {str(e)}"
        )


@router.get("/", response_model=list[ProjectResponse])
async def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return projects


@router.get("/user/repositories")
async def get_user_repositories(access_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            params={"per_page": 100, "sort": "updated"},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to fetch repositories from GitHub"
            )
        return response.json()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get project details"""
    try:
        project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return project

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, project_update: ProjectUpdate, db: Session = Depends(get_db)
):
    """Update project details"""
    try:
        project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update fields
        if project_update.name is not None:
            project.name = project_update.name
        if project_update.description is not None:
            project.description = project_update.description
        if project_update.context is not None:
            project.context.update(project_update.context)

            # Update memory as well
            project_memory = ProjectMemory(str(project.id))
            await project_memory.update_context(project_update.context)

        db.commit()
        db.refresh(project)

        logger.info(f"Project updated: {project_id}")
        return project

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    try:
        project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete from database
        db.delete(project)
        db.commit()

        logger.info(f"Project deleted: {project_id}")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
