from fastapi import APIRouter, HTTPException
import httpx
from app.config import settings

router = APIRouter()


@router.post("/auth/github")
async def github_auth(code: str):
    """Exchange GitHub code for access token"""
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_data = user_response.json()
            
            return {
                "access_token": access_token,
                "user": user_data
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))