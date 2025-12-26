from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.schemas.task import TaskCreate, TaskResponse, TaskApproval, TaskStatus
from app.models.database import get_db, Task, Project, TaskEvent
from app.services.task_service import TaskService
from loguru import logger
import uuid
from pathlib import Path

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new development task"""
    try:
        logger.info(f"Creating task for project: {task.project_id}")
        
        # Verify project exists
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create task
        db_task = Task(
            id=uuid.uuid4(),
            project_id=task.project_id,
            description=task.description,
            priority=task.priority,
            status=TaskStatus.PENDING,
            additional_context=task.additional_context
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Log event
        event = TaskEvent(
            task_id=db_task.id,
            event_type="task_created",
            data={"description": task.description, "priority": task.priority.value}
        )
        db.add(event)
        db.commit()
        
        # Start task execution in background
        task_service = TaskService(db)
        background_tasks.add_task(task_service.execute_task, str(db_task.id))
        
        logger.info(f"Task created and queued: {db_task.id}")
        return db_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task details"""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str, 
    approval: TaskApproval,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Approve or reject task plan"""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != TaskStatus.AWAITING_APPROVAL:
            raise HTTPException(
                status_code=400, 
                detail=f"Task is not awaiting approval (current status: {task.status})"
            )
        
        # Update task based on approval
        if approval.approved:
            task.status = TaskStatus.APPROVED
            event_type = "plan_approved"
            logger.info(f"Task {task_id} approved")
            
            # Continue execution in background
            task_service = TaskService(db)
            background_tasks.add_task(task_service.continue_after_approval, str(task.id))
            
        else:
            if approval.feedback:
                # Revise plan
                task.status = TaskStatus.PLANNING
                event_type = "plan_revision_requested"
                logger.info(f"Task {task_id} revision requested")
                
                # Re-plan in background
                task_service = TaskService(db)
                background_tasks.add_task(
                    task_service.replan_task, 
                    str(task.id), 
                    approval.feedback
                )
            else:
                # Reject task
                task.status = TaskStatus.REJECTED
                event_type = "plan_rejected"
                logger.info(f"Task {task_id} rejected")
        
        # Log event
        event = TaskEvent(
            task_id=task.id,
            event_type=event_type,
            data={"approved": approval.approved, "feedback": approval.feedback}
        )
        db.add(event)
        db.commit()
        
        return {"status": "success", "message": f"Task {event_type}"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/plan")
async def get_task_plan(task_id: str, db: Session = Depends(get_db)):
    """Get task implementation plan"""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if not task.plan_path:
            raise HTTPException(status_code=404, detail="Plan not yet generated")
        
        # Read plan file
        plan_path = Path(task.plan_path)
        if not plan_path.exists():
            raise HTTPException(status_code=404, detail="Plan file not found")
        
        plan_content = plan_path.read_text(encoding='utf-8')
        
        return {
            "task_id": str(task.id),
            "plan_content": plan_content,
            "status": task.status.value
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/report")
async def get_task_report(task_id: str, db: Session = Depends(get_db)):
    """Get task completion report"""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if not task.report_path:
            raise HTTPException(status_code=404, detail="Report not yet generated")
        
        # Read report file
        report_path = Path(task.report_path)
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        report_content = report_path.read_text(encoding='utf-8')
        
        return {
            "task_id": str(task.id),
            "report_content": report_content,
            "status": task.status.value,
            "branch_name": task.branch_name,
            "commit_hash": task.commit_hash
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))