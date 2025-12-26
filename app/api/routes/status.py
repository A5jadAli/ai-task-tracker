from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db, Task, TaskEvent
from loguru import logger
import uuid

router = APIRouter()


@router.get("/status/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get real-time task status"""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get recent events
        events = db.query(TaskEvent).filter(
            TaskEvent.task_id == task.id
        ).order_by(TaskEvent.created_at.desc()).limit(10).all()
        
        # Calculate progress
        status_progress = {
            "pending": 0,
            "git_sync": 10,
            "planning": 30,
            "awaiting_approval": 40,
            "approved": 45,
            "in_progress": 60,
            "testing": 80,
            "completed": 100,
            "failed": 0,
            "rejected": 0
        }
        
        progress = status_progress.get(task.status.value, 0)
        
        # Get logs from events
        logs = [f"{e.created_at.strftime('%H:%M:%S')} - {e.event_type}: {e.data.get('message', '')}" 
                for e in reversed(events)]
        
        return {
            "id": str(task.id),
            "status": task.status.value,
            "current_step": task.status.value.replace('_', ' ').title(),
            "progress_percentage": progress,
            "logs": logs,
            "plan_available": task.plan_path is not None,
            "report_available": task.report_path is not None,
            "error_message": task.error_message
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Coding Assistant"
    }