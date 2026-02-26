"""
MVP 1 Week 2 - Enhanced Admin Portal APIs
Comprehensive admin portal backend with advanced user/engagement management

Features:
- Advanced user management (edit, bulk operations, role assignment)
- Enhanced engagement management (full CRUD, user assignment)
- Audit log filtering and analytics
- Organization dashboard with real-time statistics
- Bulk operations and data export capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi import status
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

from mvp1_models import (
    MVP1User, MVP1Organization, UserRole, UserStatus, EngagementStatus,
    ComplianceEngagement, UserCreationRequest, CreateEngagementRequest,
    AuditLogEntry
)
from mvp1_auth import (
    MVP1AuthService, get_current_user, require_admin, ensure_organization_access
)
from database import DatabaseOperations
import uuid

logger = logging.getLogger(__name__)

# Create enhanced admin router
admin_portal_router = APIRouter(prefix="/api/mvp1/admin", tags=["Admin Portal"])

# =====================================
# ENHANCED USER MANAGEMENT MODELS
# =====================================

class UserUpdateRequest(BaseModel):
    """Request to update user information"""
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    assigned_engagements: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

class BulkUserOperationRequest(BaseModel):
    """Request for bulk user operations"""
    user_ids: List[str]
    operation: str  # "activate", "deactivate", "delete", "assign_engagement"
    parameters: Optional[Dict[str, Any]] = {}

class EngagementUpdateRequest(BaseModel):
    """Request to update engagement information"""
    name: Optional[str] = None
    description: Optional[str] = None
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    client_name: Optional[str] = None
    target_quarter: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    status: Optional[EngagementStatus] = None
    assigned_analysts: Optional[List[str]] = None
    assigned_auditors: Optional[List[str]] = None
    leadership_stakeholders: Optional[List[str]] = None

class UserAssignmentRequest(BaseModel):
    """Request to assign users to engagement"""
    engagement_id: str
    analyst_assignments: Optional[List[str]] = []
    auditor_assignments: Optional[List[str]] = []
    leadership_assignments: Optional[List[str]] = []

# =====================================
# ORGANIZATION DASHBOARD ENDPOINTS
# =====================================

@admin_portal_router.get("/dashboard/stats")
@require_admin
async def get_organization_dashboard_stats(current_user: MVP1User = Depends(get_current_user)):
    """Get comprehensive organization dashboard statistics"""
    try:
        org_id = current_user.organization_id
        
        # User statistics
        total_users = await DatabaseOperations.count_documents(
            "mvp1_users", {"organization_id": org_id}
        )
        
        active_users = await DatabaseOperations.count_documents(
            "mvp1_users", {"organization_id": org_id, "status": "active"}
        )
        
        # User role distribution
        user_roles = await DatabaseOperations.aggregate(
            "mvp1_users",
            [
                {"$match": {"organization_id": org_id}},
                {"$group": {"_id": "$role", "count": {"$sum": 1}}}
            ]
        )
        
        role_distribution = {role["_id"]: role["count"] for role in user_roles}
        
        # Engagement statistics
        total_engagements = await DatabaseOperations.count_documents(
            "mvp1_engagements", {"organization_id": org_id}
        )
        
        active_engagements = await DatabaseOperations.count_documents(
            "mvp1_engagements", {"organization_id": org_id, "status": {"$in": ["active", "in_progress"]}}
        )
        
        # Engagement status distribution
        engagement_statuses = await DatabaseOperations.aggregate(
            "mvp1_engagements",
            [
                {"$match": {"organization_id": org_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
        )
        
        status_distribution = {status["_id"]: status["count"] for status in engagement_statuses}
        
        # Framework distribution
        framework_distribution = await DatabaseOperations.aggregate(
            "mvp1_engagements",
            [
                {"$match": {"organization_id": org_id}},
                {"$group": {"_id": "$framework", "count": {"$sum": 1}}}
            ]
        )
        
        framework_stats = {fw["_id"]: fw["count"] for fw in framework_distribution}
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity_count = await DatabaseOperations.count_documents(
            "mvp1_audit_logs",
            {"organization_id": org_id, "timestamp": {"$gte": seven_days_ago}}
        )
        
        # Completion statistics
        completion_stats = await DatabaseOperations.aggregate(
            "mvp1_engagements",
            [
                {"$match": {"organization_id": org_id}},
                {"$group": {
                    "_id": None,
                    "avg_completion": {"$avg": "$completion_percentage"},
                    "total_controls": {"$sum": "$total_controls"},
                    "completed_controls": {"$sum": "$completed_controls"}
                }}
            ]
        )
        
        completion_data = completion_stats[0] if completion_stats else {
            "avg_completion": 0, "total_controls": 0, "completed_controls": 0
        }
        
        return {
            "organization_overview": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "completed_engagements": status_distribution.get("completed", 0)
            },
            "user_analytics": {
                "role_distribution": role_distribution,
                "user_activity_trend": "upward",  # TODO: Calculate from audit logs
                "avg_engagements_per_user": round(total_engagements / max(total_users, 1), 2)
            },
            "engagement_analytics": {
                "status_distribution": status_distribution,
                "framework_distribution": framework_stats,
                "avg_completion_percentage": round(completion_data.get("avg_completion", 0), 2),
                "total_controls": completion_data.get("total_controls", 0),
                "completed_controls": completion_data.get("completed_controls", 0)
            },
            "system_health": {
                "recent_activity_count": recent_activity_count,
                "system_uptime": "99.9%",  # TODO: Calculate actual uptime
                "last_backup": datetime.utcnow() - timedelta(hours=6),  # TODO: Actual backup info
                "storage_usage": "2.3 GB"  # TODO: Calculate actual storage
            },
            "quick_actions": [
                {"action": "create_user", "label": "Create New User", "count": 0},
                {"action": "create_engagement", "label": "Create New Engagement", "count": 0},
                {"action": "pending_reviews", "label": "Pending Reviews", "count": 0},
                {"action": "system_alerts", "label": "System Alerts", "count": 0}
            ]
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )

# =====================================
# ENHANCED USER MANAGEMENT ENDPOINTS
# =====================================

@admin_portal_router.get("/users/advanced")
@require_admin
async def get_advanced_user_list(
    current_user: MVP1User = Depends(get_current_user),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get advanced user listing with filtering and pagination"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        # Apply filters
        if role:
            query["role"] = role
        if status:
            query["status"] = status
        if department:
            query["department"] = {"$regex": department, "$options": "i"}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get users with pagination
        users = await DatabaseOperations.find_many(
            "mvp1_users",
            query,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        
        # Get total count for pagination
        total_count = await DatabaseOperations.count_documents("mvp1_users", query)
        
        # Get engagement names for assigned engagements
        engagement_ids = set()
        for user in users:
            engagement_ids.update(user.get("assigned_engagements", []))
        
        engagements_map = {}
        if engagement_ids:
            engagements = await DatabaseOperations.find_many(
                "mvp1_engagements",
                {"id": {"$in": list(engagement_ids)}},
                projection={"id": 1, "name": 1}
            )
            engagements_map = {eng["id"]: eng["name"] for eng in engagements}
        
        # Format user data
        formatted_users = []
        for user in users:
            assigned_engagement_names = [
                engagements_map.get(eng_id, f"Unknown ({eng_id})")
                for eng_id in user.get("assigned_engagements", [])
            ]
            
            formatted_users.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "department": user.get("department"),
                "job_title": user.get("job_title"),
                "status": user["status"],
                "assigned_engagements": assigned_engagement_names,
                "last_login": user.get("last_login"),
                "created_at": user["created_at"],
                "permissions_count": len(user.get("permissions", []))
            })
        
        return {
            "users": formatted_users,
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "total_count": total_count,
                "has_next": skip + limit < total_count,
                "has_previous": page > 1
            },
            "filters_applied": {
                "role": role,
                "status": status,
                "department": department,
                "search": search
            }
        }
    except Exception as e:
        logger.error(f"Advanced user list error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user list"
        )

@admin_portal_router.put("/users/{user_id}")
@require_admin
async def update_user(
    user_id: str,
    update_request: UserUpdateRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Update user information"""
    try:
        # Verify user exists and belongs to organization
        existing_user = await DatabaseOperations.find_one(
            "mvp1_users",
            {"id": user_id, "organization_id": current_user.organization_id}
        )
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare update data
        update_data = {}
        changes_made = {}
        
        for field, value in update_request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
                changes_made[field] = {
                    "old": existing_user.get(field),
                    "new": value
                }
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            update_data
        )
        
        # Log the update
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="user_updated",
            action_description=f"User {existing_user['name']} updated by admin",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="user",
            target_id=user_id,
            target_name=existing_user["name"],
            changes_made=changes_made
        )
        
        return {
            "status": "success",
            "message": f"User {existing_user['name']} updated successfully",
            "updated_fields": list(changes_made.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@admin_portal_router.post("/users/bulk-operation")
@require_admin
async def bulk_user_operation(
    bulk_request: BulkUserOperationRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Perform bulk operations on users"""
    try:
        operation = bulk_request.operation
        user_ids = bulk_request.user_ids
        parameters = bulk_request.parameters or {}
        
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        # Verify all users belong to organization
        users = await DatabaseOperations.find_many(
            "mvp1_users",
            {"id": {"$in": user_ids}, "organization_id": current_user.organization_id}
        )
        
        if len(users) != len(user_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some users not found or access denied"
            )
        
        update_data = {"updated_at": datetime.utcnow()}
        operation_description = ""
        
        if operation == "activate":
            update_data["status"] = UserStatus.ACTIVE
            operation_description = "Bulk user activation"
        elif operation == "deactivate":
            update_data["status"] = UserStatus.INACTIVE
            operation_description = "Bulk user deactivation"
        elif operation == "assign_engagement":
            engagement_id = parameters.get("engagement_id")
            if not engagement_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Engagement ID required for assignment"
                )
            
            # Add engagement to assigned engagements
            for user in users:
                current_engagements = set(user.get("assigned_engagements", []))
                current_engagements.add(engagement_id)
                await DatabaseOperations.update_one(
                    "mvp1_users",
                    {"id": user["id"]},
                    {"assigned_engagements": list(current_engagements), "updated_at": datetime.utcnow()}
                )
            
            operation_description = f"Bulk engagement assignment: {engagement_id}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {operation}"
            )
        
        # Perform bulk update (except for assign_engagement which is handled above)
        if operation != "assign_engagement":
            await DatabaseOperations.update_many(
                "mvp1_users",
                {"id": {"$in": user_ids}},
                update_data
            )
        
        # Log bulk operation
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="bulk_user_operation",
            action_description=f"{operation_description} for {len(user_ids)} users",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            changes_made={
                "operation": operation,
                "user_count": len(user_ids),
                "parameters": parameters
            }
        )
        
        return {
            "status": "success",
            "message": f"Bulk operation '{operation}' completed for {len(user_ids)} users",
            "affected_users": len(user_ids)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk user operation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )

# =====================================
# ENHANCED ENGAGEMENT MANAGEMENT ENDPOINTS
# =====================================

@admin_portal_router.get("/engagements/advanced")
@require_admin
async def get_advanced_engagement_list(
    current_user: MVP1User = Depends(get_current_user),
    status: Optional[EngagementStatus] = Query(None),
    framework: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get advanced engagement listing with filtering and team information"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        # Apply filters
        if status:
            query["status"] = status
        if framework:
            query["framework"] = framework
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"client_name": {"$regex": search, "$options": "i"}},
                {"engagement_code": {"$regex": search, "$options": "i"}}
            ]
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get engagements
        engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            query,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        
        # Get total count
        total_count = await DatabaseOperations.count_documents("mvp1_engagements", query)
        
        # Get user information for team members
        all_user_ids = set()
        for eng in engagements:
            all_user_ids.update(eng.get("assigned_analysts", []))
            all_user_ids.update(eng.get("assigned_auditors", []))
            all_user_ids.update(eng.get("leadership_stakeholders", []))
            all_user_ids.add(eng.get("engagement_lead"))
        
        users_map = {}
        if all_user_ids:
            users = await DatabaseOperations.find_many(
                "mvp1_users",
                {"id": {"$in": list(all_user_ids)}},
                projection={"id": 1, "name": 1, "email": 1, "role": 1}
            )
            users_map = {user["id"]: user for user in users}
        
        # Format engagement data
        formatted_engagements = []
        for eng in engagements:
            team_info = {
                "lead": users_map.get(eng.get("engagement_lead"), {}).get("name", "Unassigned"),
                "analysts": [users_map.get(uid, {}).get("name", f"Unknown ({uid})") 
                           for uid in eng.get("assigned_analysts", [])],
                "auditors": [users_map.get(uid, {}).get("name", f"Unknown ({uid})") 
                           for uid in eng.get("assigned_auditors", [])],
                "leadership": [users_map.get(uid, {}).get("name", f"Unknown ({uid})") 
                             for uid in eng.get("leadership_stakeholders", [])]
            }
            
            formatted_engagements.append({
                "id": eng["id"],
                "name": eng["name"],
                "engagement_code": eng["engagement_code"],
                "framework": eng["framework"],
                "client_name": eng["client_name"],
                "target_quarter": eng["target_quarter"],
                "status": eng["status"],
                "completion_percentage": eng.get("completion_percentage", 0),
                "total_controls": eng.get("total_controls", 0),
                "completed_controls": eng.get("completed_controls", 0),
                "team_info": team_info,
                "created_at": eng["created_at"],
                "target_completion_date": eng.get("target_completion_date")
            })
        
        return {
            "engagements": formatted_engagements,
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "total_count": total_count,
                "has_next": skip + limit < total_count,
                "has_previous": page > 1
            },
            "filters_applied": {
                "status": status,
                "framework": framework,
                "search": search
            }
        }
    except Exception as e:
        logger.error(f"Advanced engagement list error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement list"
        )

@admin_portal_router.post("/engagements")
@require_admin
async def create_engagement(
    engagement_request: CreateEngagementRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create new compliance engagement (Admin only)"""
    try:
        # Validate framework is supported
        org_data = await DatabaseOperations.find_one(
            "mvp1_organizations",
            {"id": current_user.organization_id}
        )
        
        supported_frameworks = org_data.get("supported_frameworks", []) if org_data else []
        if engagement_request.framework not in supported_frameworks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Framework {engagement_request.framework} not supported by organization"
            )
        
        # Create engagement
        new_engagement = ComplianceEngagement(
            name=engagement_request.name,
            description=engagement_request.description,
            framework=engagement_request.framework,
            framework_version=engagement_request.framework_version,
            client_name=engagement_request.client_name,
            target_quarter=engagement_request.target_quarter,
            target_completion_date=engagement_request.target_completion_date,
            organization_id=current_user.organization_id,
            engagement_lead=current_user.id,
            assigned_analysts=engagement_request.assigned_analysts or [],
            assigned_auditors=engagement_request.assigned_auditors or [],
            leadership_stakeholders=engagement_request.leadership_stakeholders or [],
            created_by=current_user.id
        )
        
        # Insert to database
        await DatabaseOperations.insert_one("mvp1_engagements", new_engagement.dict())
        
        # Log engagement creation
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            engagement_id=new_engagement.id,
            action_type="engagement_created",
            action_description=f"New engagement created: {new_engagement.name}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="engagement",
            target_id=new_engagement.id,
            target_name=new_engagement.name
        )
        
        return {
            "status": "success",
            "message": "Engagement created successfully",
            "engagement": {
                "id": new_engagement.id,
                "name": new_engagement.name,
                "engagement_code": new_engagement.engagement_code,
                "framework": new_engagement.framework,
                "client_name": new_engagement.client_name,
                "target_quarter": new_engagement.target_quarter,
                "status": new_engagement.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create engagement error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create engagement"
        )

@admin_portal_router.put("/engagements/{engagement_id}")
@require_admin
async def update_engagement(
    engagement_id: str,
    update_request: EngagementUpdateRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Update engagement information"""
    try:
        # Verify engagement exists and belongs to organization
        existing_engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {"id": engagement_id, "organization_id": current_user.organization_id}
        )
        
        if not existing_engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found"
            )
        
        # Prepare update data
        update_data = {}
        changes_made = {}
        
        for field, value in update_request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
                changes_made[field] = {
                    "old": existing_engagement.get(field),
                    "new": value
                }
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update engagement
        await DatabaseOperations.update_one(
            "mvp1_engagements",
            {"id": engagement_id},
            update_data
        )
        
        # Log the update
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            engagement_id=engagement_id,
            action_type="engagement_updated",
            action_description=f"Engagement {existing_engagement['name']} updated by admin",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="engagement",
            target_id=engagement_id,
            target_name=existing_engagement["name"],
            changes_made=changes_made
        )
        
        return {
            "status": "success",
            "message": f"Engagement {existing_engagement['name']} updated successfully",
            "updated_fields": list(changes_made.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update engagement error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update engagement"
        )

@admin_portal_router.delete("/engagements/{engagement_id}")
@require_admin
async def delete_engagement(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Delete engagement (Admin only)"""
    try:
        # Verify engagement exists and belongs to organization
        existing_engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {"id": engagement_id, "organization_id": current_user.organization_id}
        )
        
        if not existing_engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found"
            )
        
        # Check if engagement can be deleted (not in progress)
        if existing_engagement.get("status") in ["in_progress", "under_review"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete engagement that is in progress or under review"
            )
        
        # Delete engagement
        await DatabaseOperations.delete_one(
            "mvp1_engagements",
            {"id": engagement_id}
        )
        
        # Log the deletion
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            engagement_id=engagement_id,
            action_type="engagement_deleted",
            action_description=f"Engagement {existing_engagement['name']} deleted by admin",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="engagement",
            target_id=engagement_id,
            target_name=existing_engagement["name"]
        )
        
        return {
            "status": "success",
            "message": f"Engagement {existing_engagement['name']} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete engagement error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete engagement"
        )

@admin_portal_router.post("/engagements/{engagement_id}/assign-users")
@require_admin
async def assign_users_to_engagement(
    engagement_id: str,
    assignment_request: UserAssignmentRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Assign users to engagement roles"""
    try:
        # Verify engagement exists
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {"id": engagement_id, "organization_id": current_user.organization_id}
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found"
            )
        
        # Verify all users exist and belong to organization
        all_user_ids = (assignment_request.analyst_assignments + 
                       assignment_request.auditor_assignments + 
                       assignment_request.leadership_assignments)
        
        if all_user_ids:
            users = await DatabaseOperations.find_many(
                "mvp1_users",
                {"id": {"$in": all_user_ids}, "organization_id": current_user.organization_id}
            )
            
            if len(users) != len(set(all_user_ids)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some users not found or access denied"
                )
        
        # Update engagement assignments
        update_data = {
            "assigned_analysts": assignment_request.analyst_assignments,
            "assigned_auditors": assignment_request.auditor_assignments,
            "leadership_stakeholders": assignment_request.leadership_assignments,
            "updated_at": datetime.utcnow()
        }
        
        await DatabaseOperations.update_one(
            "mvp1_engagements",
            {"id": engagement_id},
            update_data
        )
        
        # Update user assignments
        for user_id in all_user_ids:
            user = await DatabaseOperations.find_one("mvp1_users", {"id": user_id})
            if user:
                current_engagements = set(user.get("assigned_engagements", []))
                current_engagements.add(engagement_id)
                await DatabaseOperations.update_one(
                    "mvp1_users",
                    {"id": user_id},
                    {"assigned_engagements": list(current_engagements)}
                )
        
        # Log assignment
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            engagement_id=engagement_id,
            action_type="engagement_user_assignment",
            action_description=f"Users assigned to engagement {engagement['name']}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="engagement",
            target_id=engagement_id,
            target_name=engagement["name"],
            changes_made={
                "analysts_assigned": len(assignment_request.analyst_assignments),
                "auditors_assigned": len(assignment_request.auditor_assignments),
                "leadership_assigned": len(assignment_request.leadership_assignments)
            }
        )
        
        return {
            "status": "success",
            "message": f"Users assigned to engagement {engagement['name']} successfully",
            "assignments": {
                "analysts": len(assignment_request.analyst_assignments),
                "auditors": len(assignment_request.auditor_assignments),
                "leadership": len(assignment_request.leadership_assignments)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign users to engagement error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign users to engagement"
        )

# =====================================
# ENHANCED AUDIT LOG ENDPOINTS
# =====================================

@admin_portal_router.get("/audit-logs/advanced")
@require_admin
async def get_advanced_audit_logs(
    current_user: MVP1User = Depends(get_current_user),
    action_type: Optional[str] = Query(None),
    actor_role: Optional[UserRole] = Query(None),
    engagement_id: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get advanced audit logs with comprehensive filtering"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        # Apply filters
        if action_type:
            query["action_type"] = action_type
        if actor_role:
            query["actor_role"] = actor_role
        if engagement_id:
            query["engagement_id"] = engagement_id
        if target_type:
            query["target_type"] = target_type
        if start_date and end_date:
            query["timestamp"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["timestamp"] = {"$gte": start_date}
        elif end_date:
            query["timestamp"] = {"$lte": end_date}
        
        if search:
            query["$or"] = [
                {"action_description": {"$regex": search, "$options": "i"}},
                {"actor_name": {"$regex": search, "$options": "i"}},
                {"target_name": {"$regex": search, "$options": "i"}}
            ]
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get audit logs
        logs = await DatabaseOperations.find_many(
            "mvp1_audit_logs",
            query,
            skip=skip,
            limit=limit,
            sort=[("timestamp", -1)]
        )
        
        # Get total count
        total_count = await DatabaseOperations.count_documents("mvp1_audit_logs", query)
        
        return {
            "audit_logs": logs,
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "total_count": total_count,
                "has_next": skip + limit < total_count,
                "has_previous": page > 1
            },
            "filters_applied": {
                "action_type": action_type,
                "actor_role": actor_role,
                "engagement_id": engagement_id,
                "target_type": target_type,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "search": search
            },
            "summary": {
                "total_activities": total_count,
                "time_range": f"{start_date or 'Beginning'} to {end_date or 'Now'}"
            }
        }
    except Exception as e:
        logger.error(f"Advanced audit logs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )