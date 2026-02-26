from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
import logging

from mvp1_auth import get_current_user, require_admin, MVP1AuthService
from mvp1_models import MVP1User, UserRole, UserStatus, UserCreationRequest
from database import DatabaseOperations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mvp1/admin", tags=["Admin"])


class SimpleCreateUserRequest(BaseModel):
	name: str
	email: EmailStr
	password: str
	department: str | None = None
	job_title: str | None = None


async def _create_role_user(role: UserRole, payload: SimpleCreateUserRequest, current_user: MVP1User):
    # REMOVED: Manual hashing here usually causes "Invalid Credentials" later.
    
    # Build UserCreationRequest
    # We pass the raw payload.password or handle it via the service
    user_req = UserCreationRequest(
        name=payload.name,
        email=payload.email.lower(),
        role=role,
        department=payload.department,
        job_title=payload.job_title,
        send_onboarding_email=False
    )

    # Let the service handle the initial creation
    new_user, temp_password = await MVP1AuthService.create_user(
        user_request=user_req,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )

    # Now, update the user with the ACTUAL password provided in the request
    # Use the service's hash method here so it matches the login logic exactly
    final_hashed_password = MVP1AuthService.hash_password(payload.password)
    
    update_data = {
        "password_hash": final_hashed_password,
        "status": UserStatus.ACTIVE.value.lower()  # Changed from .value to .value.lower()
    }
    
    await DatabaseOperations.update_one(
        "mvp1_users",
        {"id": new_user.id},
        update_data
    )
    
    logger.info(f"{role.value.title()} user created and activated: {payload.email}")

    return {
        "message": f"{role.value.title()} user created successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": role.value,
            "status": UserStatus.ACTIVE.value,
            "organization_id": new_user.organization_id
        }
    }


@router.post("/create-auditor")
@require_admin
async def create_auditor(
	payload: SimpleCreateUserRequest,
	current_user: MVP1User = Depends(get_current_user)
):
	try:
		return await _create_role_user(UserRole.AUDITOR, payload, current_user)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error creating auditor user: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create auditor user")


@router.post("/create-analyst")
@require_admin
async def create_analyst(
	payload: SimpleCreateUserRequest,
	current_user: MVP1User = Depends(get_current_user)
):
	try:
		return await _create_role_user(UserRole.ANALYST, payload, current_user)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error creating analyst user: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create analyst user")


@router.post("/create-leadership")
@require_admin
async def create_leadership(
	payload: SimpleCreateUserRequest,
	current_user: MVP1User = Depends(get_current_user)
):
	try:
		return await _create_role_user(UserRole.LEADERSHIP, payload, current_user)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error creating leadership user: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create leadership user")
