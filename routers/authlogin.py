from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import logging
from datetime import datetime

# Import models and services from the backend root
from mvp1_auth import MVP1AuthService, get_current_user
from mvp1_models import UserRole, UserStatus
from database import DatabaseOperations
from mvp1_auth import MVP1AuthService, get_current_user
from mvp1_models import MVP1User, UserRole, UserStatus 
from database import DatabaseOperations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authlogin", tags=["Platform Admin and others"])

class AdminLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def platform_admin_login(request: AdminLoginRequest):
    """
    Login endpoint for all users (admin, analyst, auditor, leadership).
    Normalizes email to lowercase to match creation logic.
    """
    try:
        # Normalize email to lowercase to ensure match with stored data
        normalized_email = request.email.lower()
        
        # 1. Check if user exists first for better logging
        user_record = await DatabaseOperations.find_one("mvp1_users", {"email": normalized_email})
        
        if not user_record:
            logger.warning(f"Login attempt failed: User with email {normalized_email} not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # 2. Authenticate using the service
        # This handles password verification against the stored hash
        user = await MVP1AuthService.authenticate_user(normalized_email, request.password)
        
        if not user:
            logger.warning(f"Login attempt failed: Incorrect password for {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # 3. Generate session and access tokens
        login_result = await MVP1AuthService.login_user(normalized_email, request.password)

        logger.info(f"User {normalized_email} authenticated successfully with role {user.role}")
        
        return {
            "user": login_result.get("user"),
            "session_token": login_result.get("session_token"),
            "access_token": login_result.get("access_token"),
            "token_type": login_result.get("token_type")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login service currently unavailable"
        )

@router.get("/status")
async def platform_admin_status(current_user: MVP1User = Depends(get_current_user)):
    """
    Check if the current user is an authenticated Platform Admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Platform Admin access required")
        
    return {
        "is_admin": True,
        "admin_name": current_user.name,
        "email": current_user.email,
        "timestamp": datetime.utcnow().isoformat()
    }