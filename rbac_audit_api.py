"""
RBAC Audit API - Role-Based Access Control Audit Logging
Handles audit logging for module access attempts and RBAC violations
Critical for RBAC-POST-CREATION-001 compliance requirement
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import json
from pydantic import BaseModel

from mvp1_auth import get_current_user, MVP1User, require_role, UserRole
from mvp1_models import AuditLogEntry
from database import DatabaseOperations

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/audit", tags=["RBAC Audit"])

class AccessAttemptRequest(BaseModel):
    """Request model for logging access attempts"""
    action_type: str
    action_description: str
    result: str  # 'GRANTED' or 'DENIED'
    reason: str  # Detailed reason for the result
    route: str   # Route/module attempted
    additional_data: Optional[Dict[str, Any]] = {}

@router.post("/access-attempt")
async def log_access_attempt(
    request: AccessAttemptRequest,
    http_request: Request,
    current_user: Optional[MVP1User] = Depends(get_current_user)
):
    """
    Log module access attempts for RBAC compliance
    Critical endpoint for RBAC-POST-CREATION-001 requirement
    """
    try:
        # Extract additional request metadata
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        # Create audit log entry
        audit_entry = AuditLogEntry(
            organization_id=current_user.organization_id if current_user else "unknown",
            action_type="rbac_access_attempt",
            action_description=f"RBAC Access: {request.result} - {request.action_description}",
            actor_id=current_user.id if current_user else "anonymous",
            actor_name=current_user.name if current_user else "Anonymous User",
            actor_role=current_user.role if current_user else UserRole.ANALYST,
            actor_ip_address=client_ip,
            target_type="route",
            target_id=request.route,
            target_name=request.route,
            changes_made={
                "access_result": request.result,
                "reason": request.reason,
                "route": request.route,
                "user_agent": user_agent
            },
            category="security",
            sensitive_data=False,
            additional_metadata={
                **request.additional_data,
                "rbac_enforcement": True,
                "compliance_requirement": "RBAC-POST-CREATION-001"
            }
        )
        
        # Insert to audit log
        await DatabaseOperations.insert_one("mvp1_audit_logs", audit_entry.dict())
        
        # Log to application logs based on severity
        if request.result == "DENIED":
            logger.warning(
                f"RBAC Access Denied: User {current_user.email if current_user else 'anonymous'} "
                f"({current_user.role.value if current_user else 'unknown'}) attempted to access {request.route}. "
                f"Reason: {request.reason}",
                extra={
                    "user_id": current_user.id if current_user else None,
                    "route": request.route,
                    "reason": request.reason,
                    "client_ip": client_ip
                }
            )
        else:
            logger.info(
                f"RBAC Access Granted: User {current_user.email if current_user else 'anonymous'} "
                f"accessed {request.route}",
                extra={
                    "user_id": current_user.id if current_user else None,
                    "route": request.route
                }
            )
        
        return {
            "success": True,
            "message": "Access attempt logged successfully",
            "log_id": audit_entry.id,
            "timestamp": audit_entry.timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to log access attempt: {str(e)}")
        # Don't raise exception to avoid breaking frontend functionality
        return {
            "success": False,
            "message": "Failed to log access attempt",
            "error": str(e)
        }

@router.get("/access-logs")
@require_role([UserRole.ADMIN])
async def get_access_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action_type: Optional[str] = None,
    result: Optional[str] = None,
    user_id: Optional[str] = None,
    route: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Retrieve access logs for audit purposes (Admin only)
    """
    try:
        # Build query filter
        query_filter = {
            "organization_id": current_user.organization_id,
            "category": "security"
        }
        
        # Add date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query_filter["timestamp"] = date_filter
        
        # Add additional filters
        if action_type:
            query_filter["action_type"] = action_type
        if user_id:
            query_filter["actor_id"] = user_id
        if route:
            query_filter["target_id"] = route
        if result:
            query_filter["changes_made.access_result"] = result
        
        # Get logs with pagination
        logs = await DatabaseOperations.find_many(
            "mvp1_audit_logs",
            query_filter,
            limit=limit,
            skip=offset,
            sort=[("timestamp", -1)]  # Most recent first
        )
        
        # Get total count for pagination
        total_count = await DatabaseOperations.count_documents("mvp1_audit_logs", query_filter)
        
        return {
            "success": True,
            "logs": logs,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(logs) < total_count
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve access logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve access logs"
        )

# Health check endpoint
@router.get("/health")
async def audit_health_check():
    """Health check for RBAC audit system"""
    try:
        # Test database connection
        await DatabaseOperations.find_one("mvp1_audit_logs", {}, limit=1)
        
        return {
            "success": True,
            "service": "RBAC Audit API",
            "status": "healthy",
            "compliance_requirement": "RBAC-POST-CREATION-001",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"RBAC Audit health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RBAC audit system unavailable"
        )