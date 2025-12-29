from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.database import get_db, Task, TaskEvent
import json
import asyncio
from app.utils.progress import calculate_progress

router = APIRouter()

@router.websocket("/ws/tasks/{task_id}")
async def task_updates(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates"""
    await websocket.accept()
    
    try:
        db = next(get_db())
        
        while True:
            # Get current task status
            task = db.query(Task).filter(Task.id == task_id).first()
            
            if task:
                # Get recent events
                events = db.query(TaskEvent).filter(
                    TaskEvent.task_id == task.id
                ).order_by(TaskEvent.created_at.desc()).limit(5).all()
                
                # Send update
                await websocket.send_json({
                    "task_id": str(task.id),
                    "status": task.status.value,
                    "progress": calculate_progress(task.status),
                    "logs": [e.event_type for e in events]
                })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        pass
    finally:
        db.close()