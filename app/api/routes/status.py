from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get real-time task status"""
    # TODO: Implement status retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
