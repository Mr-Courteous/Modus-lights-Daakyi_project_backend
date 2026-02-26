"""
MVP 1 - Core API Endpoints
Foundational API routes for multi-tenant compliance collaboration platform

Week 1 Focus:
- Authentication and user management APIs
- Organization management endpoints
- Basic engagement creation and management
- Health check and initialization endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from mvp1_models import (
    MVP1User, MVP1Organization, UserRole, UserStatus,
    ComplianceEngagement, EngagementStatus,
    UserCreationRequest, CreateEngagementRequest, 
    DashboardDataResponse, AuditLogEntry
)
from mvp1_auth import (
    MVP1AuthService, get_current_user, get_current_user_optional,
    require_role, require_permission, require_admin, ensure_organization_access
)
from database import DatabaseOperations
import uuid

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Create API router
mvp1_router = APIRouter(prefix="/api/mvp1", tags=["MVP1"])

# =====================================
# INITIALIZATION AND HEALTH ENDPOINTS
# =====================================

@mvp1_router.get("/health")
async def health_check():
    """Health check endpoint for MVP 1 system"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "system": "DAAKYI MVP 1 - Compliance Collaboration Platform",
        "timestamp": datetime.utcnow(),
        "components": {
            "authentication": "operational",
            "database": "operational",
            "multi_tenancy": "operational",
            "role_based_access": "operational"
        },
        "supported_roles": ["admin", "analyst", "auditor", "leadership"],
        "supported_frameworks": ["ISO 27001", "NIST CSF", "SOC 2 Type I", "Ghana CII Directives"]
    }

@mvp1_router.post("/initialize")
async def initialize_system():
    """Initialize MVP 1 system with sample data"""
    try:
        # Create sample organizations
        organizations = await MVP1AuthService.create_sample_organizations()
        
        return {
            "status": "success",
            "message": "MVP 1 system initialized successfully",
            "organizations_created": len(organizations),
            "admin_credentials": {
                "email": "admin@daakyi.com",
                "password": "DaakyiSecure2025!",
                "note": "Use these credentials to log in as admin"
            },
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "industry": org.industry,
                    "supported_frameworks": org.supported_frameworks
                }
                for org in organizations
            ]
        }
    except Exception as e:
        logger.error(f"System initialization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System initialization failed: {str(e)}"
        )

# =====================================
# AUTHENTICATION ENDPOINTS
# =====================================

@mvp1_router.post("/auth/login")
async def login(login_request: dict):
    """Login user with email and password"""
    try:
        email = login_request.get("email")
        password = login_request.get("password")
        organization_id = login_request.get("organization_id")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        result = await MVP1AuthService.login_user(email, password, organization_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@mvp1_router.get("/auth/me")
async def get_current_user_info(current_user: MVP1User = Depends(get_current_user)):
    """Get current user information"""
    # Get organization information
    org_data = await DatabaseOperations.find_one(
        "mvp1_organizations",
        {"id": current_user.organization_id}
    )
    
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "department": current_user.department,
            "job_title": current_user.job_title,
            "permissions": current_user.permissions,
            "status": current_user.status,
            "last_login": current_user.last_login
        },
        "organization": {
            "id": current_user.organization_id,
            "name": org_data.get("name") if org_data else "Unknown",
            "industry": org_data.get("industry") if org_data else None,
            "supported_frameworks": org_data.get("supported_frameworks", []) if org_data else []
        }
    }

@mvp1_router.post("/auth/logout")
async def logout(current_user: MVP1User = Depends(get_current_user)):
    """Logout current user"""
    try:
        # Invalidate session
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": current_user.id},
            {"session_token": None}
        )
        
        # Log logout event
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="user_logout",
            action_description="User logged out",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role
        )
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# =====================================
# USER MANAGEMENT ENDPOINTS (ADMIN ONLY)
# =====================================

@mvp1_router.post("/admin/users")
@require_admin
async def create_user(
    user_request: UserCreationRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create new user (Admin only)"""
    try:
        new_user = await MVP1AuthService.create_user(
            user_request, 
            current_user.id, 
            current_user.organization_id
        )
        
        return {
            "status": "success",
            "message": f"User {new_user.name} created successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "status": new_user.status
            },
            "temporary_password_sent": True  # In production, this would be sent via email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@mvp1_router.get("/admin/users")
@require_admin
async def list_users(
    current_user: MVP1User = Depends(get_current_user),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    limit: int = 50
):
    """List users in organization (Admin only)"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        if role:
            query["role"] = role
        if status:
            query["status"] = status
        
        users = await DatabaseOperations.find_many(
            "mvp1_users",
            query,
            limit=limit,
            sort=[("created_at", -1)]
        )
        
        return {
            "users": [
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "department": user.get("department"),
                    "status": user["status"],
                    "last_login": user.get("last_login"),
                    "created_at": user["created_at"]
                }
                for user in users
            ],
            "total_count": len(users)
        }
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@mvp1_router.put("/admin/users/{user_id}/status")
@require_admin
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: MVP1User = Depends(get_current_user)
):
    """Update user status (Admin only)"""
    try:
        # Verify user belongs to same organization
        target_user = await DatabaseOperations.find_one(
            "mvp1_users",
            {"id": user_id, "organization_id": current_user.organization_id}
        )
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update status
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        )
        
        # Log status change
        await MVP1AuthService._log_audit_event(
            organization_id=current_user.organization_id,
            action_type="user_status_updated",
            action_description=f"User status changed to {new_status}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="user",
            target_id=user_id,
            target_name=target_user["name"]
        )
        
        return {
            "status": "success",
            "message": f"User status updated to {new_status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )

# =====================================
# ORGANIZATION MANAGEMENT ENDPOINTS
# =====================================

@mvp1_router.get("/organizations")
async def get_organizations(current_user: Optional[MVP1User] = Depends(get_current_user_optional)):
    """Get available organizations (for login screen)"""
    try:
        organizations = await DatabaseOperations.find_many(
            "mvp1_organizations",
            {"status": "active"},
            projection={"id": 1, "name": 1, "industry": 1, "size": 1},
            limit=20
        )
        
        return {
            "organizations": [
                {
                    "id": org["id"],
                    "name": org["name"],
                    "industry": org.get("industry"),
                    "size": org.get("size")
                }
                for org in organizations
            ]
        }
    except Exception as e:
        logger.error(f"Get organizations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )

@mvp1_router.get("/organization/info")
async def get_organization_info(current_user: MVP1User = Depends(get_current_user)):
    """Get current user's organization information"""
    try:
        org_data = await DatabaseOperations.find_one(
            "mvp1_organizations",
            {"id": current_user.organization_id}
        )
        
        if not org_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user counts
        user_counts = await DatabaseOperations.count_documents(
            "mvp1_users",
            {"organization_id": current_user.organization_id, "status": "active"}
        )
        
        # Get engagement counts
        engagement_counts = await DatabaseOperations.count_documents(
            "mvp1_engagements",
            {"organization_id": current_user.organization_id}
        )
        
        return {
            "organization": {
                "id": org_data["id"],
                "name": org_data["name"],
                "industry": org_data.get("industry"),
                "size": org_data.get("size"),
                "headquarters_location": org_data.get("headquarters_location"),
                "supported_frameworks": org_data.get("supported_frameworks", []),
                "subscription_tier": org_data.get("subscription_tier", "standard"),
                "created_at": org_data.get("created_at")
            },
            "usage_stats": {
                "active_users": user_counts,
                "total_engagements": engagement_counts,
                "max_users": org_data.get("max_users", 50),
                "max_engagements": org_data.get("max_engagements", 10)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get organization info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization information"
        )

# =====================================
# ENGAGEMENT MANAGEMENT ENDPOINTS
# =====================================

@mvp1_router.post("/engagements")
@require_permission("manage_engagements")
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
            assigned_analysts=engagement_request.assigned_analysts,
            assigned_auditors=engagement_request.assigned_auditors,
            leadership_stakeholders=engagement_request.leadership_stakeholders,
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

@mvp1_router.get("/engagements")
async def list_engagements(
    current_user: MVP1User = Depends(get_current_user),
    status: Optional[EngagementStatus] = None,
    framework: Optional[str] = None,
    limit: int = 20
):
    """List engagements accessible to current user"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        # Role-based filtering
        if current_user.role == UserRole.ANALYST:
            query["assigned_analysts"] = {"$in": [current_user.id]}
        elif current_user.role == UserRole.AUDITOR:
            query["assigned_auditors"] = {"$in": [current_user.id]}
        elif current_user.role == UserRole.LEADERSHIP:
            query["leadership_stakeholders"] = {"$in": [current_user.id]}
        # Admin can see all engagements
        
        if status:
            query["status"] = status
        if framework:
            query["framework"] = framework
        
        engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            query,
            limit=limit,
            sort=[("created_at", -1)]
        )
        
        return {
            "engagements": [
                {
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
                    "created_at": eng["created_at"]
                }
                for eng in engagements
            ],
            "total_count": len(engagements),
            "user_role": current_user.role
        }
    except Exception as e:
        logger.error(f"List engagements error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list engagements"
        )

@mvp1_router.get("/engagements/{engagement_id}")
async def get_engagement_details(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get detailed engagement information"""
    try:
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {"id": engagement_id, "organization_id": current_user.organization_id}
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found"
            )
        
        # Check user access to engagement
        has_access = (
            current_user.role == UserRole.ADMIN or
            current_user.id in engagement.get("assigned_analysts", []) or
            current_user.id in engagement.get("assigned_auditors", []) or
            current_user.id in engagement.get("leadership_stakeholders", [])
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this engagement"
            )
        
        return {
            "engagement": engagement,
            "user_role_in_engagement": current_user.role,
            "user_permissions": current_user.permissions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get engagement details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement details"
        )

# =====================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# =====================================

@mvp1_router.get("/dashboard")
async def get_dashboard_data(current_user: MVP1User = Depends(get_current_user)):
    """Get role-specific dashboard data"""
    try:
        dashboard_data = {
            "user_info": {
                "name": current_user.name,
                "role": current_user.role,
                "organization_id": current_user.organization_id
            },
            "summary_stats": {},
            "recent_activities": [],
            "pending_items": [],
            "quick_actions": []
        }
        
        # Role-specific dashboard data
        if current_user.role == UserRole.ADMIN:
            # Admin dashboard: organization-wide metrics
            total_users = await DatabaseOperations.count_documents(
                "mvp1_users",
                {"organization_id": current_user.organization_id}
            )
            
            total_engagements = await DatabaseOperations.count_documents(
                "mvp1_engagements",
                {"organization_id": current_user.organization_id}
            )
            
            active_engagements = await DatabaseOperations.count_documents(
                "mvp1_engagements",
                {"organization_id": current_user.organization_id, "status": "active"}
            )
            
            dashboard_data["summary_stats"] = {
                "total_users": total_users,
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "system_health": "healthy"
            }
            
            dashboard_data["quick_actions"] = [
                {"action": "create_user", "label": "Create New User"},
                {"action": "create_engagement", "label": "Create New Engagement"},
                {"action": "view_audit_logs", "label": "View Audit Logs"},
                {"action": "manage_organization", "label": "Manage Organization"}
            ]
        
        elif current_user.role == UserRole.ANALYST:
            # Analyst dashboard: assigned engagements and tasks
            assigned_engagements = await DatabaseOperations.find_many(
                "mvp1_engagements",
                {
                    "organization_id": current_user.organization_id,
                    "assigned_analysts": {"$in": [current_user.id]}
                },
                limit=10
            )
            
            dashboard_data["summary_stats"] = {
                "assigned_engagements": len(assigned_engagements),
                "pending_forms": 0,  # TODO: Implement form counting
                "uploaded_evidence": 0,  # TODO: Implement evidence counting
                "completion_rate": 0.0  # TODO: Calculate completion rate
            }
            
            dashboard_data["quick_actions"] = [
                {"action": "complete_intake_form", "label": "Complete Current State Form"},
                {"action": "upload_evidence", "label": "Upload Evidence"},
                {"action": "view_feedback", "label": "View Auditor Feedback"},
                {"action": "check_tasks", "label": "Check AI Recommendations"}
            ]
        
        elif current_user.role == UserRole.AUDITOR:
            # Auditor dashboard: review tasks and feedback
            review_engagements = await DatabaseOperations.find_many(
                "mvp1_engagements",
                {
                    "organization_id": current_user.organization_id,
                    "assigned_auditors": {"$in": [current_user.id]}
                },
                limit=10
            )
            
            dashboard_data["summary_stats"] = {
                "review_engagements": len(review_engagements),
                "pending_reviews": 0,  # TODO: Implement review counting
                "feedback_provided": 0,  # TODO: Implement feedback counting
                "approval_rate": 0.0  # TODO: Calculate approval rate
            }
            
            dashboard_data["quick_actions"] = [
                {"action": "review_submissions", "label": "Review Analyst Submissions"},
                {"action": "provide_feedback", "label": "Provide Feedback"},
                {"action": "approve_evidence", "label": "Review Evidence"},
                {"action": "update_status", "label": "Update Control Status"}
            ]
        
        elif current_user.role == UserRole.LEADERSHIP:
            # Leadership dashboard: high-level metrics and reports
            stakeholder_engagements = await DatabaseOperations.find_many(
                "mvp1_engagements",
                {
                    "organization_id": current_user.organization_id,
                    "leadership_stakeholders": {"$in": [current_user.id]}
                },
                limit=10
            )
            
            dashboard_data["summary_stats"] = {
                "tracked_engagements": len(stakeholder_engagements),
                "overall_compliance": 0.0,  # TODO: Calculate compliance percentage
                "critical_issues": 0,  # TODO: Count critical issues
                "projected_completion": "Q3 2025"  # TODO: Calculate projection
            }
            
            dashboard_data["quick_actions"] = [
                {"action": "view_executive_summary", "label": "View Executive Summary"},
                {"action": "download_reports", "label": "Download Reports"},
                {"action": "check_progress", "label": "Check Progress"},
                {"action": "view_analytics", "label": "View Risk Analytics"}
            ]
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )

# =====================================
# AUDIT LOG ENDPOINTS
# =====================================

@mvp1_router.get("/admin/audit-logs")
@require_admin
async def get_audit_logs(
    current_user: MVP1User = Depends(get_current_user),
    limit: int = 100,
    action_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get audit logs for organization (Admin only)"""
    try:
        query = {"organization_id": current_user.organization_id}
        
        if action_type:
            query["action_type"] = action_type
        if start_date and end_date:
            query["timestamp"] = {"$gte": start_date, "$lte": end_date}
        
        logs = await DatabaseOperations.find_many(
            "mvp1_audit_logs",
            query,
            limit=limit,
            sort=[("timestamp", -1)]
        )
        
        return {
            "audit_logs": logs,
            "total_count": len(logs),
            "filters_applied": {
                "action_type": action_type,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )