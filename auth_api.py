"""
Authentication API Endpoints
Handles password reset functionality and token validation
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, EmailStr
import logging

from sendgrid_service import get_sendgrid_service
from mvp1_auth import MVP1AuthService
from mvp1_models import MVP1User
from database import DatabaseOperations

logger = logging.getLogger(__name__)

# Router for authentication endpoints
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Request/Response Models
class TokenValidationRequest(BaseModel):
    token: str

class TokenValidationResponse(BaseModel):
    valid: bool
    email: str = None
    message: str = None

class PasswordResetRequest(BaseModel):
    token: str
    newPassword: str

class PasswordResetResponse(BaseModel):
    success: bool
    message: str

@auth_router.post("/validate-reset-token", response_model=TokenValidationResponse)
async def validate_reset_token(request: TokenValidationRequest) -> TokenValidationResponse:
    """
    Validate password reset token
    
    Args:
        request: Token validation request with JWT token
        
    Returns:
        TokenValidationResponse with validation status and user email
    """
    try:
        sendgrid_service = get_sendgrid_service()
        validation_result = await sendgrid_service.validate_reset_token(request.token)
        
        if validation_result:
            return TokenValidationResponse(
                valid=True,
                email=validation_result["email"],
                message="Token is valid"
            )
        else:
            return TokenValidationResponse(
                valid=False,
                message="Invalid or expired reset token"
            )
            
    except Exception as e:
        logger.error(f"Error validating reset token: {str(e)}")
        return TokenValidationResponse(
            valid=False,
            message="Unable to validate reset token"
        )

@auth_router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: PasswordResetRequest) -> PasswordResetResponse:
    """
    Reset user password using validated token
    
    Args:
        request: Password reset request with token and new password
        
    Returns:
        PasswordResetResponse with success status and message
    """
    try:
        sendgrid_service = get_sendgrid_service()
        
        # Validate token first
        validation_result = await sendgrid_service.validate_reset_token(request.token)
        
        if not validation_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user_email = validation_result["email"]
        
        # Find user in database
        user_data = await DatabaseOperations.find_one(
            "mvp1_users",
            {"email": user_email.lower()}
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        new_password_hash = MVP1AuthService.hash_password(request.newPassword)
        
        # Update user password and status
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"email": user_email.lower()},
            {
                "password_hash": new_password_hash,
                "status": "active",  # Activate user after password reset
                "session_token": None  # Invalidate existing sessions
            }
        )
        
        # Mark token as used to prevent reuse
        await sendgrid_service.mark_token_as_used(request.token)
        
        # Log password reset for audit trail
        user = MVP1User(**user_data)
        await MVP1AuthService._log_audit_event(
            organization_id=user.organization_id,
            action_type="password_reset",
            action_description=f"Password reset completed for user: {user.name}",
            actor_id=user.id,
            actor_name=user.name,
            actor_role=user.role,
            target_type="user",
            target_id=user.id,
            target_name=user.name
        )
        
        logger.info(f"Password reset successful for user: {user_email}")
        
        return PasswordResetResponse(
            success=True,
            message="Password has been reset successfully. You can now log in with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset password. Please try again or contact support."
        )