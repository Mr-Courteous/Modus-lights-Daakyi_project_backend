"""
MVP 1 - Admin-Only User Management APIs
Secure user management endpoints for administrators
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ValidationError
from datetime import datetime
import uuid
import logging
import csv
import io
from dataclasses import dataclass

from mvp1_auth import get_current_user, require_admin, require_admin_for_user_management, MVP1AuthService
from mvp1_models import (
    MVP1User, UserRole, UserStatus, UserCreationRequest, UserPermissions
)
from database import DatabaseOperations
from sendgrid_service import get_sendgrid_service

logger = logging.getLogger(__name__)

# Router for user management
user_mgmt_router = APIRouter(prefix="/api/mvp1/admin/user-management", tags=["User Management"])

# =====================================
# REQUEST/RESPONSE MODELS
# =====================================

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[UserStatus] = None
    permissions: Optional[List[str]] = None

class UserSearchFilters(BaseModel):
    search: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = None

class BulkUserAction(BaseModel):
    user_ids: List[str]
    action: str  # 'activate', 'deactivate', 'delete'

class PasswordResetRequest(BaseModel):
    user_id: str
    send_email: bool = False

class UserManagementStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    pending_users: int
    users_by_role: Dict[str, int]
    recent_registrations: int

# CSV Bulk Import Models
@dataclass
class CSVValidationError:
    row_number: int
    field: str
    error_message: str
    row_data: Dict[str, str]

class CSVPreviewRow(BaseModel):
    row_number: int
    name: str
    email: str
    role: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    errors: List[Dict[str, str]] = []
    is_valid: bool = True

class CSVPreviewResponse(BaseModel):
    total_rows: int
    preview_rows: List[CSVPreviewRow]
    validation_errors: List[Dict[str, str]]
    valid_rows: int
    invalid_rows: int
    duplicate_emails: List[str]

class BulkImportRequest(BaseModel):
    csv_data: List[Dict[str, str]]
    send_onboarding_emails: bool = False

class BulkImportResponse(BaseModel):
    success: bool
    total_processed: int
    successful_imports: int
    failed_imports: int
    skipped_rows: int
    errors: List[Dict[str, Any]]
    imported_users: List[Dict[str, str]]

# =====================================
# USER MANAGEMENT ENDPOINTS
# =====================================

@user_mgmt_router.get("/health")
async def user_management_health():
    """Health check for user management module"""
    return {
        "module": "MVP 1 - Admin User Management",
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": [
            "secure_user_creation",
            "role_assignment_control", 
            "user_status_management",
            "search_and_filtering",
            "password_reset_functionality",
            "bulk_operations",
            "audit_trail_logging",
            "session_invalidation"
        ],
        "total_endpoints": 10,
        "security_level": "admin_only_access"
    }

@user_mgmt_router.get("/dashboard-stats")
@require_admin
async def get_user_management_stats(current_user: MVP1User = Depends(get_current_user)) -> UserManagementStats:
    """Get user management dashboard statistics"""
    try:
        # Get all users for current organization
        users = await DatabaseOperations.find_many(
            "mvp1_users", 
            {"organization_id": current_user.organization_id}
        )
        
        total_users = len(users)
        active_users = len([u for u in users if u.get("status") == UserStatus.ACTIVE])
        inactive_users = len([u for u in users if u.get("status") == UserStatus.INACTIVE])
        pending_users = len([u for u in users if u.get("status") == UserStatus.PENDING])
        
        # Users by role
        users_by_role = {}
        for role in UserRole:
            users_by_role[role.value] = len([u for u in users if u.get("role") == role])
        
        # Recent registrations (last 7 days)
        seven_days_ago = datetime.utcnow().replace(microsecond=0) - timedelta(days=7)
        recent_registrations = len([
            u for u in users 
            if u.get("created_at") and u.get("created_at") >= seven_days_ago
        ])
        
        return UserManagementStats(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            pending_users=pending_users,
            users_by_role=users_by_role,
            recent_registrations=recent_registrations
        )
        
    except Exception as e:
        logger.error(f"Error getting user management stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@user_mgmt_router.post("/users")
@require_admin_for_user_management("create users")
async def create_user_secure(
    user_request: UserCreationRequest,
    current_user: MVP1User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create new user (Admin only) - Secure user creation with email notification"""
    try:
        # Validate admin permissions
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Administrator privileges required to create users."
            )
        
        # Additional validation for admin role assignment
        if user_request.role == UserRole.ADMIN:
            logger.warning(f"Admin {current_user.name} attempting to create admin user: {user_request.email}")
            # Could add additional validation here (e.g., require super-admin permission)
        
        # Create user using secure method
        new_user, temporary_password = await MVP1AuthService.create_user(
            user_request=user_request,
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Send onboarding email if requested
        email_status = None
        if user_request.send_onboarding_email:
            try:
                # Get organization info for email
                org_data = await DatabaseOperations.find_one(
                    "mvp1_organizations",
                    {"id": current_user.organization_id}
                )
                
                organization_name = org_data.get("name", "Your Organization") if org_data else "Your Organization"
                
                # Send onboarding email
                sendgrid_service = get_sendgrid_service()
                email_result = await sendgrid_service.send_user_onboarding_email(
                    user_email=new_user.email,
                    user_name=new_user.name,
                    organization_name=organization_name,
                    temporary_password=temporary_password
                )
                
                email_status = email_result
                
                if email_result["success"]:
                    logger.info(f"Onboarding email sent successfully to {new_user.email}")
                else:
                    logger.error(f"Failed to send onboarding email to {new_user.email}: {email_result.get('error')}")
                    
            except Exception as email_error:
                logger.error(f"Error sending onboarding email to {new_user.email}: {str(email_error)}")
                email_status = {
                    "success": False,
                    "error": str(email_error),
                    "message": "Failed to send onboarding email"
                }
        
        # Log successful user creation
        logger.info(f"User created by admin {current_user.name}: {new_user.email} with role {new_user.role}")
        
        response_data = {
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "status": new_user.status,
                "created_at": new_user.created_at
            },
            "temporary_password_logged": True
        }
        
        # Add email status to response if email was attempted
        if email_status:
            response_data["email_notification"] = email_status
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@user_mgmt_router.get("/users")
@require_admin
async def get_users_advanced(
    current_user: MVP1User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search by name, email, or role"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    job_title: Optional[str] = Query(None, description="Filter by job title"),
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip")
) -> Dict[str, Any]:
    """Get users with advanced filtering and pagination"""
    try:
        # Build query
        query = {"organization_id": current_user.organization_id}
        
        if role:
            query["role"] = role
        if status:
            query["status"] = status
        if department:
            query["department"] = department
        if job_title:
            query["job_title"] = job_title
        
        # Get users from database
        users_data = await DatabaseOperations.find_many("mvp1_users", query)
        
        # Apply search filter - enhanced to search across multiple fields
        if search:
            search_lower = search.lower()
            users_data = [
                user for user in users_data
                if search_lower in user.get("name", "").lower() or 
                   search_lower in user.get("email", "").lower() or
                   search_lower in user.get("role", "").lower() or
                   search_lower in user.get("department", "").lower() or
                   search_lower in user.get("job_title", "").lower()
            ]
        
        # Apply pagination
        total_count = len(users_data)
        users_data = users_data[offset:offset + limit]
        
        # Format response
        users = []
        for user_data in users_data:
            user = MVP1User(**user_data)
            users.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "department": user.department,
                "job_title": user.job_title,
                "last_login": user.last_login,
                "created_at": user.created_at,
                "permissions_count": len(user.permissions)
            })
        
        return {
            "users": users,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@user_mgmt_router.get("/users/{user_id}")
@require_admin
async def get_user_details(
    user_id: str,
    current_user: MVP1User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed user information"""
    try:
        # Get user data
        user_data = await DatabaseOperations.find_one(
            "mvp1_users",
            {"id": user_id, "organization_id": current_user.organization_id}
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = MVP1User(**user_data)
        
        # Get user's recent activity/audit logs
        recent_logs = await DatabaseOperations.find_many(
            "mvp1_audit_logs",
            {"actor_id": user_id, "organization_id": current_user.organization_id},
            limit=10,
            sort=[("timestamp", -1)]
        )
        
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "department": user.department,
                "job_title": user.job_title,
                "permissions": user.permissions,
                "assigned_engagements": user.assigned_engagements,
                "last_login": user.last_login,
                "last_activity": user.last_activity,
                "created_at": user.created_at,
                "created_by": user.created_by,
                "failed_login_attempts": user.failed_login_attempts,
                "account_locked_until": user.account_locked_until
            },
            "recent_activity": [
                {
                    "action_type": log.get("action_type"),
                    "action_description": log.get("action_description"),
                    "timestamp": log.get("timestamp")
                }
                for log in recent_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )

@user_mgmt_router.put("/users/{user_id}")
@require_admin_for_user_management("edit users")
async def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    current_user: MVP1User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user information (Admin only)"""
    try:
        # Get existing user
        existing_user_data = await DatabaseOperations.find_one(
            "mvp1_users",
            {"id": user_id, "organization_id": current_user.organization_id}
        )
        
        if not existing_user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        existing_user = MVP1User(**existing_user_data)
        
        # Prevent self-demotion from admin
        if (existing_user.id == current_user.id and 
            user_update.role and user_update.role != UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own admin role"
            )
        
        # Build update data
        update_data = {}
        changes_made = {}
        
        if user_update.name:
            update_data["name"] = user_update.name
            changes_made["name"] = {"old": existing_user.name, "new": user_update.name}
        
        if user_update.role:
            update_data["role"] = user_update.role
            # Update permissions based on new role
            update_data["permissions"] = MVP1AuthService._get_role_permissions(user_update.role)
            changes_made["role"] = {"old": existing_user.role, "new": user_update.role}
        
        if user_update.department:
            update_data["department"] = user_update.department
            changes_made["department"] = {"old": existing_user.department, "new": user_update.department}
        
        if user_update.job_title:
            update_data["job_title"] = user_update.job_title
            changes_made["job_title"] = {"old": existing_user.job_title, "new": user_update.job_title}
        
        if user_update.status:
            update_data["status"] = user_update.status
            changes_made["status"] = {"old": existing_user.status, "new": user_update.status}
            
            # If deactivating user, invalidate session
            if user_update.status == UserStatus.INACTIVE:
                update_data["session_token"] = None
                logger.info(f"Invalidated session for deactivated user: {existing_user.email}")
        
        if user_update.permissions:
            update_data["permissions"] = user_update.permissions
            changes_made["permissions"] = {"old": existing_user.permissions, "new": user_update.permissions}
        
        # Update user
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            update_data
        )
        
        # Log user update
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="user_updated",
            action_description=f"User updated: {existing_user.name}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="user",
            target_id=user_id,
            target_name=existing_user.name,
            changes_made=changes_made
        )
        
        logger.info(f"User updated by admin {current_user.name}: {existing_user.email}")
        
        return {
            "message": "User updated successfully",
            "changes_made": changes_made
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@user_mgmt_router.post("/users/{user_id}/reset-password")
@require_admin_for_user_management("reset user passwords")
async def reset_user_password(
    user_id: str,
    reset_request: PasswordResetRequest,
    current_user: MVP1User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reset user password (Admin only)"""
    try:
        # Get user
        user_data = await DatabaseOperations.find_one(
            "mvp1_users",
            {"id": user_id, "organization_id": current_user.organization_id}
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = MVP1User(**user_data)
        
        # Generate new temporary password
        temp_password = f"Reset{uuid.uuid4().hex[:8]}!"
        hashed_password = MVP1AuthService.hash_password(temp_password)
        
        # Update user password and set status to pending (requires password change)
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            {
                "password_hash": hashed_password,
                "status": UserStatus.PENDING,
                "session_token": None,  # Invalidate current session
                "failed_login_attempts": 0,  # Reset failed attempts
                "account_locked_until": None  # Remove any lockout
            }
        )
        
        # Log password reset
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="password_reset",
            action_description=f"Password reset for user: {user.name}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="user",
            target_id=user_id,
            target_name=user.name
        )
        
        logger.info(f"Password reset by admin {current_user.name} for user: {user.email}")
        logger.info(f"New temporary password for {user.email}: {temp_password}")
        
        return {
            "message": "Password reset successfully",
            "user_email": user.email,
            "temporary_password_logged": True,
            "user_status": "pending_password_change"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

@user_mgmt_router.post("/users/bulk-action")
@require_admin_for_user_management("perform bulk user actions")
async def bulk_user_action(
    bulk_action: BulkUserAction,
    current_user: MVP1User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Perform bulk actions on users (Admin only)"""
    try:
        if not bulk_action.user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        # Validate action
        valid_actions = ["activate", "deactivate", "delete"]
        if bulk_action.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        # Get users to be affected
        users_data = await DatabaseOperations.find_many(
            "mvp1_users",
            {
                "id": {"$in": bulk_action.user_ids},
                "organization_id": current_user.organization_id
            }
        )
        
        if not users_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found for the provided IDs"
            )
        
        # Prevent actions on self
        if current_user.id in bulk_action.user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot perform bulk actions on your own account"
            )
        
        affected_users = []
        
        # Perform bulk action
        if bulk_action.action == "activate":
            await DatabaseOperations.update_many(
                "mvp1_users",
                {"id": {"$in": bulk_action.user_ids}},
                {"status": UserStatus.ACTIVE}
            )
            action_description = "Bulk user activation"
            
        elif bulk_action.action == "deactivate":
            await DatabaseOperations.update_many(
                "mvp1_users",
                {"id": {"$in": bulk_action.user_ids}},
                {
                    "status": UserStatus.INACTIVE,
                    "session_token": None  # Invalidate sessions
                }
            )
            action_description = "Bulk user deactivation"
            
        elif bulk_action.action == "delete":
            # Note: In production, consider soft delete instead of hard delete
            await DatabaseOperations.delete_many(
                "mvp1_users",
                {"id": {"$in": bulk_action.user_ids}}
            )
            action_description = "Bulk user deletion"
        
        # Log bulk action
        for user_data in users_data:
            user = MVP1User(**user_data)
            affected_users.append({
                "id": user.id,
                "name": user.name,
                "email": user.email
            })
            
            await MVP1AuthService._log_audit_event(
                organization_id=current_user.organization_id,
                action_type="bulk_user_action",
                action_description=f"{action_description}: {user.name}",
                actor_id=current_user.id,
                actor_name=current_user.name,
                actor_role=current_user.role,
                target_type="user",
                target_id=user.id,
                target_name=user.name,
                changes_made={"bulk_action": bulk_action.action}
            )
        
        logger.info(f"Bulk action {bulk_action.action} performed by admin {current_user.name} on {len(affected_users)} users")
        
        return {
            "message": f"Bulk action '{bulk_action.action}' completed successfully",
            "action": bulk_action.action,
            "affected_users": affected_users,
            "count": len(affected_users)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing bulk action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )

# Import required for datetime
from datetime import timedelta

# =====================================
# CSV BULK IMPORT ENDPOINTS
# =====================================

def validate_csv_data(csv_data: List[Dict[str, str]], organization_id: str) -> tuple[List[CSVPreviewRow], List[str]]:
    """
    Validate CSV data and return preview rows with validation errors
    
    Args:
        csv_data: List of dictionaries representing CSV rows
        organization_id: Organization ID for checking duplicate emails
        
    Returns:
        Tuple of (preview_rows, duplicate_emails)
    """
    preview_rows = []
    duplicate_emails = []
    email_set = set()
    valid_roles = ['admin', 'analyst', 'auditor', 'leadership']
    
    for idx, row_data in enumerate(csv_data[:10], start=1):  # Preview first 10 rows
        errors = []
        
        # Normalize keys (handle case variations and extra spaces)
        normalized_row = {}
        for key, value in row_data.items():
            if key:
                normalized_key = key.strip().lower().replace(' ', '_')
                normalized_row[normalized_key] = value.strip() if value else ""
        
        # Get normalized values
        name = normalized_row.get('name', '').strip()
        email = normalized_row.get('email', '').strip().lower()
        role = normalized_row.get('role', '').strip().lower()
        department = normalized_row.get('department', '').strip()
        job_title = normalized_row.get('job_title', '').strip()
        
        # Validate required fields
        if not name:
            errors.append({"field": "name", "message": "Name is required"})
        
        if not email:
            errors.append({"field": "email", "message": "Email is required"})
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors.append({"field": "email", "message": "Invalid email format"})
        elif email in email_set:
            errors.append({"field": "email", "message": "Duplicate email in CSV"})
            if email not in duplicate_emails:
                duplicate_emails.append(email)
        else:
            email_set.add(email)
        
        if not role:
            errors.append({"field": "role", "message": "Role is required"})
        elif role not in valid_roles:
            errors.append({
                "field": "role", 
                "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            })
        
        # Create preview row
        preview_row = CSVPreviewRow(
            row_number=idx,
            name=name,
            email=email,
            role=role,
            department=department if department else None,
            job_title=job_title if job_title else None,
            errors=errors,
            is_valid=len(errors) == 0
        )
        
        preview_rows.append(preview_row)
    
    return preview_rows, duplicate_emails

async def check_existing_emails(emails: List[str], organization_id: str) -> List[str]:
    """Check which emails already exist in the database"""
    existing_users = await DatabaseOperations.find_many(
        "mvp1_users",
        {
            "email": {"$in": emails},
            "organization_id": organization_id
        }
    )
    
    return [user["email"] for user in existing_users]

@user_mgmt_router.post("/users/csv/preview")
@require_admin
async def preview_csv_import(
    file: UploadFile = File(...),
    current_user: MVP1User = Depends(get_current_user)
) -> CSVPreviewResponse:
    """
    Preview CSV file for bulk user import with validation
    
    Args:
        file: Uploaded CSV file
        current_user: Current admin user
        
    Returns:
        CSV preview with validation results
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are allowed"
            )
        
        # Read and parse CSV
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        # Convert to list of dictionaries
        csv_data = []
        for row in csv_reader:
            csv_data.append(row)
        
        if not csv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or invalid"
            )
        
        # Validate CSV structure and data
        preview_rows, duplicate_emails = validate_csv_data(csv_data, current_user.organization_id)
        
        # Check for existing emails in database
        all_emails = [row.email for row in preview_rows if row.email]
        existing_emails = await check_existing_emails(all_emails, current_user.organization_id)
        
        # Update validation errors for existing emails
        for row in preview_rows:
            if row.email in existing_emails:
                row.errors.append({
                    "field": "email",
                    "message": "Email already exists in system"
                })
                row.is_valid = False
        
        # Count valid/invalid rows
        valid_rows = sum(1 for row in preview_rows if row.is_valid)
        invalid_rows = len(preview_rows) - valid_rows
        
        # Collect all validation errors
        validation_errors = []
        for row in preview_rows:
            for error in row.errors:
                validation_errors.append({
                    "row_number": row.row_number,
                    "field": error["field"],
                    "message": error["message"],
                    "value": getattr(row, error["field"], "")
                })
        
        logger.info(f"CSV preview generated by admin {current_user.name}: {len(csv_data)} rows, {valid_rows} valid, {invalid_rows} invalid")
        
        return CSVPreviewResponse(
            total_rows=len(csv_data),
            preview_rows=preview_rows,
            validation_errors=validation_errors,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            duplicate_emails=duplicate_emails + existing_emails
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing CSV import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process CSV file"
        )

@user_mgmt_router.post("/users/csv/import")
@require_admin
async def import_users_from_csv(
    import_request: BulkImportRequest,
    current_user: MVP1User = Depends(get_current_user)
) -> BulkImportResponse:
    """
    Import users from validated CSV data
    
    Args:
        import_request: Bulk import request with CSV data
        current_user: Current admin user
        
    Returns:
        Bulk import results
    """
    try:
        imported_users = []
        failed_imports = []
        skipped_rows = 0
        
        # Validate and import each user
        for idx, row_data in enumerate(import_request.csv_data, start=1):
            try:
                # Normalize data
                name = row_data.get('name', '').strip()
                email = row_data.get('email', '').strip().lower()
                role = row_data.get('role', '').strip().lower()
                department = row_data.get('department', '').strip() or None
                job_title = row_data.get('job_title', '').strip() or None
                
                # Skip invalid rows
                if not name or not email or not role:
                    skipped_rows += 1
                    failed_imports.append({
                        "row_number": idx,
                        "error": "Missing required fields (name, email, role)",
                        "data": row_data
                    })
                    continue
                
                # Check if user already exists
                existing_user = await DatabaseOperations.find_one(
                    "mvp1_users",
                    {"email": email, "organization_id": current_user.organization_id}
                )
                
                if existing_user:
                    skipped_rows += 1
                    failed_imports.append({
                        "row_number": idx,
                        "error": "User with this email already exists",
                        "data": row_data
                    })
                    continue
                
                # Create user
                user_creation_request = UserCreationRequest(
                    name=name,
                    email=email,
                    role=UserRole(role),
                    department=department,
                    job_title=job_title,
                    send_onboarding_email=import_request.send_onboarding_emails
                )
                
                # Create user using existing secure method
                new_user, temp_password = await MVP1AuthService.create_user(
                    user_request=user_creation_request,
                    created_by=current_user.id,
                    organization_id=current_user.organization_id
                )
                
                # Send email if requested
                email_status = None
                if import_request.send_onboarding_emails:
                    try:
                        sendgrid_service = get_sendgrid_service()
                        
                        # Get organization info
                        org_data = await DatabaseOperations.find_one(
                            "mvp1_organizations",
                            {"id": current_user.organization_id}
                        )
                        
                        organization_name = org_data.get("name", "Your Organization") if org_data else "Your Organization"
                        
                        email_result = await sendgrid_service.send_user_onboarding_email(
                            user_email=new_user.email,
                            user_name=new_user.name,
                            organization_name=organization_name,
                            temporary_password=temp_password
                        )
                        
                        email_status = email_result.get("success", False)
                        
                    except Exception as e:
                        logger.error(f"Failed to send onboarding email to {email}: {str(e)}")
                        email_status = False
                
                imported_users.append({
                    "row_number": idx,
                    "name": new_user.name,
                    "email": new_user.email,
                    "role": new_user.role,
                    "user_id": new_user.id,
                    "email_sent": email_status
                })
                
                logger.info(f"CSV import: User created - {new_user.email}")
                
            except Exception as user_error:
                logger.error(f"Error importing user at row {idx}: {str(user_error)}")
                failed_imports.append({
                    "row_number": idx,
                    "error": str(user_error),
                    "data": row_data
                })
        
        # Log bulk import audit event
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="bulk_csv_import",
            action_description=f"Bulk CSV import completed: {len(imported_users)} users imported, {len(failed_imports)} failed",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="bulk_operation",
            target_id="csv_import",
            target_name="CSV Bulk Import",
            changes_made={
                "total_processed": len(import_request.csv_data),
                "successful_imports": len(imported_users),
                "failed_imports": len(failed_imports),
                "skipped_rows": skipped_rows
            }
        )
        
        logger.info(f"CSV bulk import completed by admin {current_user.name}: {len(imported_users)} imported, {len(failed_imports)} failed")
        
        return BulkImportResponse(
            success=True,
            total_processed=len(import_request.csv_data),
            successful_imports=len(imported_users),
            failed_imports=len(failed_imports),
            skipped_rows=skipped_rows,
            errors=failed_imports,
            imported_users=imported_users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing users from CSV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import users from CSV"
        )