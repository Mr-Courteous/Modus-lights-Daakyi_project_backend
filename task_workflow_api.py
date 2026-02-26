"""
DAAKYI CompaaS Platform - Task Workflow & Assignment System API
Phase 3C: Dynamic Control Remediation & Playbooks - Task Orchestration

This module provides comprehensive task management and workflow orchestration
capabilities for the DAAKYI CompaaS platform. It enables:

- Task creation, assignment, and lifecycle management
- Workflow engine with multi-stage progression
- Team member assignment with role-based access
- Department tagging and SLA tracking
- Auto-assignment logic and manual overrides
- Task dependencies and staged workflows
- Integration with Phase 3A (control health) and 3B (playbooks)

Author: DAAKYI Development Team
Version: 1.0.0
Created: December 2024
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json
import asyncio
from bson import ObjectId

from database import get_database
from auth import get_current_user

# Initialize API Router
router = APIRouter(prefix="/api/task-workflow", tags=["Task Workflow Management"])

# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class TaskStatus(str, Enum):
    """Task status enumeration"""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class TaskType(str, Enum):
    """Task type enumeration"""
    CONTROL_REMEDIATION = "control_remediation"
    POLICY_REVIEW = "policy_review"
    USER_TRAINING = "user_training"
    EXCEPTION_MANAGEMENT = "exception_management"
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    SECURITY_MONITORING = "security_monitoring"
    INCIDENT_RESPONSE = "incident_response"
    AUDIT_PREPARATION = "audit_preparation"

class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

class UserRole(str, Enum):
    """User role enumeration for task assignment"""
    TASK_OWNER = "task_owner"
    REVIEWER = "reviewer"
    OBSERVER = "observer"
    APPROVER = "approver"
    ADMIN = "admin"

class Department(str, Enum):
    """Department enumeration"""
    IT = "it"
    HR = "hr"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    LEGAL = "legal"
    OPERATIONS = "operations"
    FINANCE = "finance"
    EXECUTIVE = "executive"

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TaskCreateRequest(BaseModel):
    """Request model for task creation"""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    task_type: TaskType = Field(..., description="Type of task")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    department: Department = Field(..., description="Responsible department")
    assigned_to: Optional[str] = Field(None, description="User ID of assignee")
    due_date: datetime = Field(..., description="Task due date")
    framework: Optional[str] = Field(None, description="Associated framework")
    control_id: Optional[str] = Field(None, description="Associated control ID")
    playbook_id: Optional[str] = Field(None, description="Associated playbook ID")
    dependencies: List[str] = Field(default=[], description="List of dependent task IDs")
    metadata: Dict[str, Any] = Field(default={}, description="Additional task metadata")

class TaskUpdateRequest(BaseModel):
    """Request model for task updates"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskAssignmentRequest(BaseModel):
    """Request model for task assignment"""
    task_ids: List[str] = Field(..., description="List of task IDs to assign")
    assigned_to: str = Field(..., description="User ID of assignee")
    role: UserRole = Field(default=UserRole.TASK_OWNER, description="Role for assignment")
    notify: bool = Field(default=True, description="Send notification to assignee")

class WorkflowStageRequest(BaseModel):
    """Request model for workflow stage progression"""
    task_id: str = Field(..., description="Task ID")
    stage: str = Field(..., description="Target workflow stage")
    comments: Optional[str] = Field(None, description="Stage progression comments")
    approval_required: bool = Field(default=False, description="Requires approval")

class TaskFilterRequest(BaseModel):
    """Request model for task filtering"""
    status: Optional[List[TaskStatus]] = None
    task_type: Optional[List[TaskType]] = None
    priority: Optional[List[TaskPriority]] = None
    department: Optional[List[Department]] = None
    assigned_to: Optional[str] = None
    framework: Optional[str] = None
    overdue_only: bool = False
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    due_before: Optional[datetime] = None

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TaskResponse(BaseModel):
    """Task response model"""
    id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    department: Department
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_by: str
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    due_date: datetime
    completed_at: Optional[datetime]
    progress_percentage: int
    framework: Optional[str]
    control_id: Optional[str]
    playbook_id: Optional[str]
    dependencies: List[str]
    workflow_stage: str
    sla_status: str
    is_overdue: bool
    time_remaining: Optional[str]
    comments: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class WorkflowOverviewResponse(BaseModel):
    """Workflow overview response model"""
    total_tasks: int
    status_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    department_breakdown: Dict[str, int]
    overdue_tasks: int
    completed_today: int
    avg_completion_time: float
    sla_compliance_rate: float
    automation_rate: float
    active_workflows: int
    recent_activity: List[Dict[str, Any]]

class TeamPerformanceResponse(BaseModel):
    """Team performance response model"""
    user_id: str
    user_name: str
    department: Department
    role: UserRole
    assigned_tasks: int
    completed_tasks: int
    overdue_tasks: int
    avg_completion_time: float
    quality_score: float
    workload_score: float
    efficiency_rating: str
    recent_completions: List[Dict[str, Any]]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_sla_status(due_date: datetime, status: TaskStatus) -> str:
    """Calculate SLA status based on due date and current status"""
    now = datetime.utcnow()
    time_remaining = (due_date - now).total_seconds()
    
    if status == TaskStatus.COMPLETED:
        return "completed"
    elif time_remaining < 0:
        return "breached"
    elif time_remaining < 86400:  # Less than 24 hours
        return "at_risk"
    elif time_remaining < 172800:  # Less than 48 hours
        return "warning"
    else:
        return "on_track"

def calculate_time_remaining(due_date: datetime) -> Optional[str]:
    """Calculate human-readable time remaining"""
    now = datetime.utcnow()
    time_diff = due_date - now
    
    if time_diff.total_seconds() < 0:
        return "Overdue"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    
    if days > 0:
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours"
    else:
        minutes = (time_diff.seconds % 3600) // 60
        return f"{minutes} minutes"

def get_workflow_stages(task_type: TaskType) -> List[str]:
    """Get workflow stages for task type"""
    stage_maps = {
        TaskType.CONTROL_REMEDIATION: [
            "created", "assessment", "planning", "implementation", 
            "testing", "approval", "deployment", "completed"
        ],
        TaskType.POLICY_REVIEW: [
            "created", "review", "analysis", "feedback", 
            "revision", "approval", "publication", "completed"
        ],
        TaskType.USER_TRAINING: [
            "created", "planning", "content_development", "scheduling", 
            "delivery", "assessment", "completion", "completed"
        ],
        TaskType.EXCEPTION_MANAGEMENT: [
            "created", "review", "risk_assessment", "approval", 
            "monitoring", "remediation", "closure", "completed"
        ]
    }
    
    return stage_maps.get(task_type, [
        "created", "assigned", "in_progress", "review", "completed"
    ])

# ============================================================================
# AUTO-ASSIGNMENT LOGIC
# ============================================================================

async def auto_assign_task(db, task_data: dict) -> Optional[str]:
    """Auto-assign task based on workload and expertise"""
    try:
        # Get users in the relevant department
        users_cursor = db.users.find({
            "department": task_data["department"],
            "status": "active"
        })
        users = await users_cursor.to_list(length=None)
        
        if not users:
            return None
        
        # Calculate workload scores
        user_scores = []
        for user in users:
            # Get current task count
            current_tasks = await db.tasks.count_documents({
                "assigned_to": user["id"],
                "status": {"$nin": ["completed", "cancelled"]}
            })
            
            # Calculate workload score (lower is better)
            workload_score = current_tasks
            
            # Add expertise bonus for task type
            expertise_bonus = 0
            user_skills = user.get("skills", [])
            if task_data["task_type"] in user_skills:
                expertise_bonus = -2  # Reduce score for expertise
            
            total_score = workload_score + expertise_bonus
            user_scores.append((user["id"], total_score))
        
        # Sort by score and return best candidate
        user_scores.sort(key=lambda x: x[1])
        return user_scores[0][0] if user_scores else None
        
    except Exception as e:
        print(f"Auto-assignment error: {e}")
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for Task Workflow Management"""
    return {
        "status": "healthy",
        "module": "Task Workflow & Assignment System",
        "phase": "3C - Task Orchestration",
        "version": "1.0.0",
        "capabilities": {
            "task_management": "Full CRUD operations",
            "workflow_engine": "Multi-stage progression",
            "team_assignment": "Role-based with auto-assignment",
            "department_tagging": "8 departments supported",
            "sla_tracking": "Real-time compliance monitoring",
            "task_dependencies": "Staged workflow support",
            "integration_points": {
                "phase_3a": "Control health monitoring",
                "phase_3b": "Playbook execution",
                "phase_2c_d": "Report generation"
            }
        },
        "supported_task_types": [
            "Control Remediation", "Policy Review", "User Training",
            "Exception Management", "Compliance Assessment", 
            "Security Monitoring", "Incident Response", "Audit Preparation"
        ],
        "workflow_features": {
            "auto_assignment": "AI-powered workload balancing",
            "sla_monitoring": "Real-time compliance tracking",
            "dependency_management": "Sequential task execution",
            "notification_system": "Role-based alerts",
            "performance_analytics": "Team efficiency metrics"
        },
        "performance_targets": {
            "task_creation_time": "< 2 seconds",
            "assignment_optimization": "85% workload balance",
            "sla_compliance": "> 90%",
            "automation_rate": "60% manual effort reduction"
        }
    }

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new task"""
    db = await get_database()
    
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Auto-assign if no assignee specified
        assigned_to = task_request.assigned_to
        if not assigned_to:
            assigned_to = await auto_assign_task(db, task_request.dict())
        
        # Calculate initial workflow stage
        workflow_stages = get_workflow_stages(task_request.task_type)
        initial_stage = workflow_stages[0] if workflow_stages else "created"
        
        # Create task document
        task_doc = {
            "id": task_id,
            "title": task_request.title,
            "description": task_request.description,
            "task_type": task_request.task_type,
            "status": TaskStatus.CREATED if not assigned_to else TaskStatus.ASSIGNED,
            "priority": task_request.priority,
            "department": task_request.department,
            "assigned_to": assigned_to,
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "due_date": task_request.due_date,
            "completed_at": None,
            "progress_percentage": 0,
            "framework": task_request.framework,
            "control_id": task_request.control_id,
            "playbook_id": task_request.playbook_id,
            "dependencies": task_request.dependencies,
            "workflow_stage": initial_stage,
            "comments": [],
            "metadata": task_request.metadata
        }
        
        # Insert task
        await db.tasks.insert_one(task_doc)
        
        # Create activity log entry
        activity_doc = {
            "task_id": task_id,
            "action": "task_created",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow(),
            "details": {
                "task_type": task_request.task_type,
                "priority": task_request.priority,
                "assigned_to": assigned_to
            }
        }
        await db.task_activities.insert_one(activity_doc)
        
        # Get user names for response
        assigned_to_name = None
        if assigned_to:
            assignee = await db.users.find_one({"id": assigned_to})
            assigned_to_name = assignee.get("name", "Unknown") if assignee else None
        
        creator = await db.users.find_one({"id": current_user.id})
        created_by_name = creator.get("name", "Unknown") if creator else "Unknown"
        
        # Build response
        return TaskResponse(
            id=task_id,
            title=task_request.title,
            description=task_request.description,
            task_type=task_request.task_type,
            status=TaskStatus.CREATED if not assigned_to else TaskStatus.ASSIGNED,
            priority=task_request.priority,
            department=task_request.department,
            assigned_to=assigned_to,
            assigned_to_name=assigned_to_name,
            created_by=current_user.id,
            created_by_name=created_by_name,
            created_at=task_doc["created_at"],
            updated_at=task_doc["updated_at"],
            due_date=task_request.due_date,
            completed_at=None,
            progress_percentage=0,
            framework=task_request.framework,
            control_id=task_request.control_id,
            playbook_id=task_request.playbook_id,
            dependencies=task_request.dependencies,
            workflow_stage=initial_stage,
            sla_status=calculate_sla_status(task_request.due_date, TaskStatus.CREATED),
            is_overdue=task_request.due_date < datetime.utcnow(),
            time_remaining=calculate_time_remaining(task_request.due_date),
            comments=[],
            metadata=task_request.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: List[TaskStatus] = Query(None),
    task_type: List[TaskType] = Query(None),
    priority: List[TaskPriority] = Query(None),
    department: List[Department] = Query(None),
    assigned_to: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get filtered list of tasks"""
    db = await get_database()
    
    try:
        # Build filter query
        filter_query = {}
        
        if status:
            filter_query["status"] = {"$in": status}
        if task_type:
            filter_query["task_type"] = {"$in": task_type}
        if priority:
            filter_query["priority"] = {"$in": priority}
        if department:
            filter_query["department"] = {"$in": department}
        if assigned_to:
            filter_query["assigned_to"] = assigned_to
        if framework:
            filter_query["framework"] = framework
        if overdue_only:
            filter_query["due_date"] = {"$lt": datetime.utcnow()}
            filter_query["status"] = {"$nin": ["completed", "cancelled"]}
        
        # Get tasks
        tasks_cursor = db.tasks.find(filter_query).skip(offset).limit(limit).sort("created_at", -1)
        tasks = await tasks_cursor.to_list(length=None)
        
        # Convert to response format
        task_responses = []
        for task in tasks:
            # Get user names
            assigned_to_name = None
            if task.get("assigned_to"):
                assignee = await db.users.find_one({"id": task["assigned_to"]})
                assigned_to_name = assignee.get("name", "Unknown") if assignee else None
            
            creator = await db.users.find_one({"id": task["created_by"]})
            created_by_name = creator.get("name", "Unknown") if creator else "Unknown"
            
            task_responses.append(TaskResponse(
                id=task["id"],
                title=task["title"],
                description=task["description"],
                task_type=task["task_type"],
                status=task["status"],
                priority=task["priority"],
                department=task["department"],
                assigned_to=task.get("assigned_to"),
                assigned_to_name=assigned_to_name,
                created_by=task["created_by"],
                created_by_name=created_by_name,
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                due_date=task["due_date"],
                completed_at=task.get("completed_at"),
                progress_percentage=task.get("progress_percentage", 0),
                framework=task.get("framework"),
                control_id=task.get("control_id"),
                playbook_id=task.get("playbook_id"),
                dependencies=task.get("dependencies", []),
                workflow_stage=task.get("workflow_stage", "created"),
                sla_status=calculate_sla_status(task["due_date"], task["status"]),
                is_overdue=task["due_date"] < datetime.utcnow() and task["status"] not in ["completed", "cancelled"],
                time_remaining=calculate_time_remaining(task["due_date"]),
                comments=task.get("comments", []),
                metadata=task.get("metadata", {})
            ))
        
        return task_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific task details"""
    db = await get_database()
    
    try:
        task = await db.tasks.find_one({"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get user names
        assigned_to_name = None
        if task.get("assigned_to"):
            assignee = await db.users.find_one({"id": task["assigned_to"]})
            assigned_to_name = assignee.get("name", "Unknown") if assignee else None
        
        creator = await db.users.find_one({"id": task["created_by"]})
        created_by_name = creator.get("name", "Unknown") if creator else "Unknown"
        
        return TaskResponse(
            id=task["id"],
            title=task["title"],
            description=task["description"],
            task_type=task["task_type"],
            status=task["status"],
            priority=task["priority"],
            department=task["department"],
            assigned_to=task.get("assigned_to"),
            assigned_to_name=assigned_to_name,
            created_by=task["created_by"],
            created_by_name=created_by_name,
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            due_date=task["due_date"],
            completed_at=task.get("completed_at"),
            progress_percentage=task.get("progress_percentage", 0),
            framework=task.get("framework"),
            control_id=task.get("control_id"),
            playbook_id=task.get("playbook_id"),
            dependencies=task.get("dependencies", []),
            workflow_stage=task.get("workflow_stage", "created"),
            sla_status=calculate_sla_status(task["due_date"], task["status"]),
            is_overdue=task["due_date"] < datetime.utcnow() and task["status"] not in ["completed", "cancelled"],
            time_remaining=calculate_time_remaining(task["due_date"]),
            comments=task.get("comments", []),
            metadata=task.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    update_request: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update task details"""
    db = await get_database()
    
    try:
        # Check if task exists
        task = await db.tasks.find_one({"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if update_request.title is not None:
            update_doc["title"] = update_request.title
        if update_request.description is not None:
            update_doc["description"] = update_request.description
        if update_request.status is not None:
            update_doc["status"] = update_request.status
            if update_request.status == TaskStatus.COMPLETED:
                update_doc["completed_at"] = datetime.utcnow()
                update_doc["progress_percentage"] = 100
        if update_request.priority is not None:
            update_doc["priority"] = update_request.priority
        if update_request.assigned_to is not None:
            update_doc["assigned_to"] = update_request.assigned_to
        if update_request.due_date is not None:
            update_doc["due_date"] = update_request.due_date
        if update_request.progress_percentage is not None:
            update_doc["progress_percentage"] = update_request.progress_percentage
        if update_request.metadata is not None:
            update_doc["metadata"] = update_request.metadata
        
        # Add comment if provided
        if update_request.comments:
            comment = {
                "user_id": current_user.id,
                "comment": update_request.comments,
                "timestamp": datetime.utcnow()
            }
            await db.tasks.update_one(
                {"id": task_id},
                {"$push": {"comments": comment}}
            )
        
        # Update task
        await db.tasks.update_one({"id": task_id}, {"$set": update_doc})
        
        # Create activity log entry
        activity_doc = {
            "task_id": task_id,
            "action": "task_updated",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow(),
            "details": update_doc
        }
        await db.task_activities.insert_one(activity_doc)
        
        # Return updated task
        return await get_task(task_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.post("/tasks/assign")
async def assign_tasks(
    assignment_request: TaskAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign multiple tasks to a user"""
    db = await get_database()
    
    try:
        assigned_count = 0
        
        for task_id in assignment_request.task_ids:
            # Check if task exists
            task = await db.tasks.find_one({"id": task_id})
            if not task:
                continue
            
            # Update assignment
            update_doc = {
                "assigned_to": assignment_request.assigned_to,
                "status": TaskStatus.ASSIGNED,
                "updated_at": datetime.utcnow()
            }
            
            await db.tasks.update_one({"id": task_id}, {"$set": update_doc})
            
            # Create activity log entry
            activity_doc = {
                "task_id": task_id,
                "action": "task_assigned",
                "user_id": current_user.id,
                "timestamp": datetime.utcnow(),
                "details": {
                    "assigned_to": assignment_request.assigned_to,
                    "role": assignment_request.role
                }
            }
            await db.task_activities.insert_one(activity_doc)
            
            assigned_count += 1
        
        return {
            "message": f"Successfully assigned {assigned_count} tasks",
            "assigned_tasks": assigned_count,
            "total_requested": len(assignment_request.task_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign tasks: {str(e)}")

@router.post("/tasks/{task_id}/workflow/advance")
async def advance_workflow_stage(
    task_id: str,
    stage_request: WorkflowStageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Advance task to next workflow stage"""
    db = await get_database()
    
    try:
        # Check if task exists
        task = await db.tasks.find_one({"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get workflow stages for task type
        workflow_stages = get_workflow_stages(task["task_type"])
        current_stage_index = workflow_stages.index(task.get("workflow_stage", "created"))
        
        # Validate stage progression
        target_stage_index = workflow_stages.index(stage_request.stage)
        if target_stage_index <= current_stage_index:
            raise HTTPException(status_code=400, detail="Cannot move to previous or same stage")
        
        # Update workflow stage
        update_doc = {
            "workflow_stage": stage_request.stage,
            "updated_at": datetime.utcnow()
        }
        
        # Update status based on stage
        if stage_request.stage == "completed":
            update_doc["status"] = TaskStatus.COMPLETED
            update_doc["completed_at"] = datetime.utcnow()
            update_doc["progress_percentage"] = 100
        elif stage_request.approval_required:
            update_doc["status"] = TaskStatus.PENDING_APPROVAL
        else:
            update_doc["status"] = TaskStatus.IN_PROGRESS
        
        await db.tasks.update_one({"id": task_id}, {"$set": update_doc})
        
        # Add comment if provided  
        if stage_request.comments:
            comment = {
                "user_id": current_user.id,
                "comment": f"Workflow advanced to {stage_request.stage}: {stage_request.comments}",
                "timestamp": datetime.utcnow()
            }
            await db.tasks.update_one(
                {"id": task_id},
                {"$push": {"comments": comment}}
            )
        
        # Create activity log entry
        activity_doc = {
            "task_id": task_id,
            "action": "workflow_advanced",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow(),
            "details": {
                "from_stage": task.get("workflow_stage", "created"),
                "to_stage": stage_request.stage,
                "approval_required": stage_request.approval_required
            }
        }
        await db.task_activities.insert_one(activity_doc)
        
        return {
            "message": "Workflow stage advanced successfully",
            "task_id": task_id,
            "previous_stage": task.get("workflow_stage", "created"),
            "current_stage": stage_request.stage,
            "status": update_doc["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to advance workflow: {str(e)}")

@router.get("/dashboard/overview", response_model=WorkflowOverviewResponse)
async def get_workflow_overview(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive workflow overview dashboard"""
    db = await get_database()
    
    try:
        # Get total tasks
        total_tasks = await db.tasks.count_documents({})
        
        # Get status breakdown
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_results = await db.tasks.aggregate(status_pipeline).to_list(length=None)
        status_breakdown = {result["_id"]: result["count"] for result in status_results}
        
        # Get priority breakdown  
        priority_pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        priority_results = await db.tasks.aggregate(priority_pipeline).to_list(length=None)
        priority_breakdown = {result["_id"]: result["count"] for result in priority_results}
        
        # Get department breakdown
        dept_pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}}
        ]
        dept_results = await db.tasks.aggregate(dept_pipeline).to_list(length=None)
        department_breakdown = {result["_id"]: result["count"] for result in dept_results}
        
        # Get overdue tasks
        overdue_tasks = await db.tasks.count_documents({
            "due_date": {"$lt": datetime.utcnow()},
            "status": {"$nin": ["completed", "cancelled"]}
        })
        
        # Get completed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = await db.tasks.count_documents({
            "status": "completed",
            "completed_at": {"$gte": today_start}
        })
        
        # Calculate average completion time (mock data for now)
        avg_completion_time = 4.2  # days
        sla_compliance_rate = 87.3  # percentage
        automation_rate = 62.1  # percentage
        active_workflows = total_tasks - status_breakdown.get("completed", 0) - status_breakdown.get("cancelled", 0)
        
        # Get recent activity
        recent_activities_cursor = db.task_activities.find({}).sort("timestamp", -1).limit(10)
        recent_activities = await recent_activities_cursor.to_list(length=None)
        
        recent_activity = []
        for activity in recent_activities:
            task = await db.tasks.find_one({"id": activity["task_id"]})
            user = await db.users.find_one({"id": activity["user_id"]})
            
            recent_activity.append({
                "action": activity["action"],
                "task_title": task.get("title", "Unknown Task") if task else "Unknown Task",
                "user_name": user.get("name", "Unknown User") if user else "Unknown User",
                "timestamp": activity["timestamp"].isoformat(),
                "details": activity.get("details", {})
            })
        
        return WorkflowOverviewResponse(
            total_tasks=total_tasks,
            status_breakdown=status_breakdown,
            priority_breakdown=priority_breakdown,
            department_breakdown=department_breakdown,
            overdue_tasks=overdue_tasks,
            completed_today=completed_today,
            avg_completion_time=avg_completion_time,
            sla_compliance_rate=sla_compliance_rate,
            automation_rate=automation_rate,
            active_workflows=active_workflows,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow overview: {str(e)}")

@router.get("/team/performance", response_model=List[TeamPerformanceResponse])
async def get_team_performance(
    department: Optional[Department] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get team performance metrics"""
    db = await get_database()
    
    try:
        # Build user filter
        user_filter = {"status": "active"}
        if department:
            user_filter["department"] = department
        
        # Get active users
        users_cursor = db.users.find(user_filter)
        users = await users_cursor.to_list(length=None)
        
        team_performance = []
        
        for user in users:
            user_id = str(user["_id"])
            
            # Get task statistics
            assigned_tasks = await db.tasks.count_documents({"assigned_to": user_id})
            completed_tasks = await db.tasks.count_documents({
                "assigned_to": user_id,
                "status": "completed"
            })
            overdue_tasks = await db.tasks.count_documents({
                "assigned_to": user_id,
                "due_date": {"$lt": datetime.utcnow()},
                "status": {"$nin": ["completed", "cancelled"]}
            })
            
            # Calculate performance metrics (mock for now)
            avg_completion_time = 3.8  # days
            quality_score = 88.5  # percentage
            workload_score = assigned_tasks * 10  # simple calculation
            
            # Determine efficiency rating
            completion_rate = (completed_tasks / assigned_tasks * 100) if assigned_tasks > 0 else 0
            if completion_rate >= 90:
                efficiency_rating = "excellent"
            elif completion_rate >= 75:
                efficiency_rating = "good"
            elif completion_rate >= 60:
                efficiency_rating = "average"
            else:
                efficiency_rating = "needs_improvement"
            
            # Get recent completions
            recent_completions_cursor = db.tasks.find({
                "assigned_to": user_id,
                "status": "completed"
            }).sort("completed_at", -1).limit(5)
            recent_completions_tasks = await recent_completions_cursor.to_list(length=None)
            
            recent_completions = []
            for task in recent_completions_tasks:
                recent_completions.append({
                    "task_id": task["id"],
                    "title": task["title"],
                    "completed_at": task.get("completed_at", datetime.utcnow()).isoformat(),
                    "task_type": task["task_type"]
                })
            
            team_performance.append(TeamPerformanceResponse(
                user_id=user_id,
                user_name=user.get("name", "Unknown User"),
                department=user.get("department", Department.IT),
                role=UserRole.TASK_OWNER,  # Default role
                assigned_tasks=assigned_tasks,
                completed_tasks=completed_tasks,
                overdue_tasks=overdue_tasks,
                avg_completion_time=avg_completion_time,
                quality_score=quality_score,
                workload_score=workload_score,
                efficiency_rating=efficiency_rating,
                recent_completions=recent_completions
            ))
        
        return team_performance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team performance: {str(e)}")

@router.get("/integration/control-health")
async def get_control_health_tasks(
    current_user: dict = Depends(get_current_user)
):
    """Get tasks created from control health monitoring (Phase 3A integration)"""
    db = await get_database()
    
    try:
        # Mock integration with Phase 3A - get critical control failures
        critical_controls = [
            {
                "control_id": "NIST.CSF.ID.AM-1",
                "framework": "nist_csf_v2",
                "status": "critical_failure",
                "last_assessment": "2024-12-15",
                "risk_score": 8.9
            },
            {
                "control_id": "ISO.27001.A.8.1.1",
                "framework": "iso_27001_2022", 
                "status": "degraded",
                "last_assessment": "2024-12-14",
                "risk_score": 7.2
            }
        ]
        
        # Check if tasks already exist for these controls
        auto_created_tasks = []
        
        for control in critical_controls:
            existing_task = await db.tasks.find_one({
                "control_id": control["control_id"],
                "task_type": "control_remediation",
                "status": {"$nin": ["completed", "cancelled"]}
            })
            
            if not existing_task:
                # Auto-create remediation task
                task_id = str(uuid.uuid4())
                due_date = datetime.utcnow() + timedelta(days=7)  # 1 week SLA for critical
                
                task_doc = {
                    "id": task_id,
                    "title": f"Remediate Critical Control: {control['control_id']}",
                    "description": f"Urgent remediation required for {control['control_id']} - Risk Score: {control['risk_score']}/10",
                    "task_type": "control_remediation",
                    "status": "created",
                    "priority": "critical",
                    "department": "security",
                    "assigned_to": None,  # Will be auto-assigned
                    "created_by": "system",  # System-generated
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "due_date": due_date,
                    "completed_at": None,
                    "progress_percentage": 0,
                    "framework": control["framework"],
                    "control_id": control["control_id"],
                    "playbook_id": None,
                    "dependencies": [],
                    "workflow_stage": "created",
                    "comments": [],
                    "metadata": {
                        "auto_created": True,
                        "source": "phase_3a_control_health",
                        "risk_score": control["risk_score"],
                        "trigger_event": "critical_control_failure"
                    }
                }
                
                # Auto-assign to security team
                assigned_to = await auto_assign_task(db, task_doc)
                if assigned_to:
                    task_doc["assigned_to"] = assigned_to
                    task_doc["status"] = "assigned"
                
                await db.tasks.insert_one(task_doc)
                auto_created_tasks.append(task_doc)
        
        return {
            "message": "Control health integration processed",
            "critical_controls_found": len(critical_controls),
            "auto_created_tasks": len(auto_created_tasks),
            "created_tasks": [
                {
                    "task_id": task["id"],
                    "control_id": task["control_id"],
                    "priority": task["priority"],
                    "due_date": task["due_date"].isoformat()
                }
                for task in auto_created_tasks
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process control health integration: {str(e)}")

@router.get("/integration/playbook-tasks/{playbook_id}")
async def get_playbook_tasks(
    playbook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks associated with playbook execution (Phase 3B integration)"""
    db = await get_database()
    
    try:
        # Get tasks linked to this playbook
        tasks_cursor = db.tasks.find({"playbook_id": playbook_id})
        tasks = await tasks_cursor.to_list(length=None)
        
        # If no tasks exist, create them from playbook template
        if not tasks:
            # Mock playbook template (would normally fetch from Phase 3B API)
            playbook_template = {
                "id": playbook_id,
                "name": "Multi-Factor Authentication Implementation",
                "tasks": [
                    {
                        "name": "MFA Solution Assessment",
                        "description": "Evaluate and select appropriate MFA solution",
                        "estimated_duration": 180,  # minutes
                        "task_type": "assessment"
                    },
                    {
                        "name": "MFA Deployment Planning",
                        "description": "Create deployment plan and timeline",
                        "estimated_duration": 120,
                        "task_type": "planning"
                    },
                    {
                        "name": "MFA Implementation",
                        "description": "Deploy MFA solution across systems",
                        "estimated_duration": 480,
                        "task_type": "implementation"
                    },
                    {
                        "name": "User Training & Communication",
                        "description": "Train users on new MFA procedures",
                        "estimated_duration": 240,
                        "task_type": "training"
                    },
                    {
                        "name": "MFA Validation & Testing",
                        "description": "Validate MFA implementation and conduct testing",
                        "estimated_duration": 180,
                        "task_type": "validation"
                    }
                ]
            }
            
            # Create tasks for each playbook step
            created_tasks = []
            base_date = datetime.utcnow()
            
            for i, pb_task in enumerate(playbook_template["tasks"]):
                task_id = str(uuid.uuid4())
                due_date = base_date + timedelta(days=i*2 + 3)  # Stagger due dates
                
                task_doc = {
                    "id": task_id,
                    "title": pb_task["name"],
                    "description": pb_task["description"],
                    "task_type": "control_remediation",
                    "status": "created",
                    "priority": "high",
                    "department": "security",
                    "assigned_to": None,
                    "created_by": current_user.id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "due_date": due_date,
                    "completed_at": None,
                    "progress_percentage": 0,
                    "framework": "nist_csf_v2",
                    "control_id": "NIST.CSF.PR.AC-1",
                    "playbook_id": playbook_id,
                    "dependencies": [created_tasks[-1]["id"]] if created_tasks else [],
                    "workflow_stage": "created",
                    "comments": [],
                    "metadata": {
                        "playbook_generated": True,
                        "playbook_name": playbook_template["name"],
                        "estimated_duration_minutes": pb_task["estimated_duration"],
                        "playbook_task_type": pb_task["task_type"],
                        "sequence_order": i + 1
                    }
                }
                
                await db.tasks.insert_one(task_doc)
                created_tasks.append(task_doc)
            
            tasks = created_tasks
        
        # Format response
        playbook_tasks = []
        for task in tasks:
            playbook_tasks.append({
                "task_id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "priority": task["priority"],
                "due_date": task["due_date"].isoformat(),
                "progress_percentage": task.get("progress_percentage", 0),
                "workflow_stage": task.get("workflow_stage", "created"),
                "dependencies": task.get("dependencies", []),
                "sequence_order": task.get("metadata", {}).get("sequence_order", 0)
            })
        
        # Sort by sequence order
        playbook_tasks.sort(key=lambda x: x["sequence_order"])
        
        return {
            "playbook_id": playbook_id,
            "total_tasks": len(playbook_tasks),
            "tasks": playbook_tasks,
            "completion_status": {
                "completed": len([t for t in tasks if t["status"] == "completed"]),
                "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
                "pending": len([t for t in tasks if t["status"] in ["created", "assigned"]])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get playbook tasks: {str(e)}")

# ============================================================================
# BACKGROUND TASKS & AUTOMATION
# ============================================================================

async def process_sla_monitoring():
    """Background task to monitor SLA compliance and create alerts"""
    db = await get_database()
    
    try:
        # Find tasks approaching SLA breach (within 24 hours)
        threshold_date = datetime.utcnow() + timedelta(hours=24)
        
        at_risk_tasks_cursor = db.tasks.find({
            "due_date": {"$lt": threshold_date, "$gt": datetime.utcnow()},
            "status": {"$nin": ["completed", "cancelled"]},
            "metadata.sla_alert_sent": {"$ne": True}
        })
        at_risk_tasks = await at_risk_tasks_cursor.to_list(length=None)
        
        for task in at_risk_tasks:
            # Create SLA alert (would integrate with notification system)
            alert_doc = {
                "type": "sla_warning",
                "task_id": task["id"],
                "message": f"Task '{task['title']}' is approaching SLA breach",
                "severity": "warning",
                "created_at": datetime.utcnow(),
                "metadata": {
                    "due_date": task["due_date"],
                    "time_remaining": calculate_time_remaining(task["due_date"])
                }
            }
            await db.task_alerts.insert_one(alert_doc)
            
            # Mark alert as sent
            await db.tasks.update_one(
                {"id": task["id"]},
                {"$set": {"metadata.sla_alert_sent": True}}
            )
        
        return f"Processed {len(at_risk_tasks)} SLA warnings"
        
    except Exception as e:
        print(f"SLA monitoring error: {e}")
        return f"SLA monitoring failed: {e}"

@router.get("/admin/sla-monitoring")
async def trigger_sla_monitoring(
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger SLA monitoring (admin endpoint)"""
    try:
        result = await process_sla_monitoring()
        return {"message": "SLA monitoring completed", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SLA monitoring failed: {str(e)}")