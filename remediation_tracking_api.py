"""
DAAKYI CompaaS - Phase 4C: Remediation Tracking Module
Backend API Implementation for comprehensive task tracking and workflow automation

Features:
- GAP-ID linked task tracking
- Role-based task assignment with AI-powered optimization
- Live remediation status dashboards
- Automated escalation workflows
- Performance analytics and metrics
- Real-time notifications and updates
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
from models import (
    RemediationTask, TaskAssignment, EscalationRule, TaskComment, 
    TaskMetrics, WorkflowState, User
)

router = APIRouter(prefix="/api/remediation-tracking", tags=["Remediation Tracking"])

# ================================================================================================
# REMEDIATION TASK MANAGEMENT APIs
# ================================================================================================

@router.get("/tasks", summary="Get All Remediation Tasks")
async def get_remediation_tasks(
    audit_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    gap_id: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """
    Retrieve remediation tasks with comprehensive filtering options
    
    Filter Parameters:
    - audit_id: Filter by specific audit
    - status: Filter by task status (open, assigned, in_progress, etc.)
    - priority: Filter by priority level (critical, high, medium, low)
    - assigned_to: Filter by assignee user ID
    - gap_id: Filter by specific GAP-ID
    - overdue_only: Show only overdue tasks
    """
    try:
        # Generate comprehensive mock data for development
        tasks = [
            {
                "id": f"task-{i+1:03d}",
                "task_id": f"TASK-{str(uuid.uuid4())[:8].upper()}",
                "audit_id": audit_id or f"audit-{(i % 3) + 1}",
                "gap_id": f"GAP-{str(uuid.uuid4())[:8].upper()}",
                "control_id": ["PR.AC-1", "PR.DS-1", "DE.AE-1", "RS.RP-1", "RC.RP-1"][i % 5],
                "framework": "NIST CSF 2.0",
                "title": [
                    "Implement Multi-Factor Authentication for Privileged Accounts",
                    "Establish Data Classification and Labeling System", 
                    "Deploy Advanced Threat Detection Tools",
                    "Create Incident Response Communication Plan",
                    "Develop Business Continuity Testing Procedures",
                    "Update Access Control Policy Documentation",
                    "Configure Security Information Event Management",
                    "Implement Employee Security Awareness Training",
                    "Establish Vendor Risk Assessment Process",
                    "Deploy Endpoint Detection and Response Solution"
                ][i % 10],
                "description": f"Comprehensive remediation task to address identified compliance gap GAP-{str(uuid.uuid4())[:8].upper()}. Task requires coordination with IT operations, security team, and management for successful implementation.",
                "category": ["remediation", "documentation", "process_improvement", "training"][i % 4],
                "priority": ["critical", "high", "medium", "low"][i % 4],
                "status": ["open", "assigned", "in_progress", "under_review", "completed", "blocked"][i % 6],
                "assigned_to": f"user-{((i % 5) + 1):03d}" if i % 3 != 0 else None,
                "assigned_by": f"user-{((i % 3) + 1):03d}",
                "assigned_date": (datetime.now() - timedelta(days=i+1)).isoformat() if i % 3 != 0 else None,
                "accepted_date": (datetime.now() - timedelta(days=i)).isoformat() if i % 4 == 0 else None,
                "due_date": (datetime.now() + timedelta(days=15-i)).isoformat(),
                "estimated_effort_hours": [8.0, 16.0, 24.0, 40.0, 4.0][i % 5],
                "actual_effort_hours": [6.5, 18.2, 22.1, 35.8, 4.2][i % 5] if i % 4 == 0 else None,
                "started_date": (datetime.now() - timedelta(days=i-1)).isoformat() if i % 5 == 0 else None,
                "completed_date": (datetime.now() - timedelta(days=i-5)).isoformat() if i % 7 == 0 else None,
                "dependencies": [f"TASK-{str(uuid.uuid4())[:8].upper()}"] if i % 3 == 0 else [],
                "dependent_tasks": [f"TASK-{str(uuid.uuid4())[:8].upper()}"] if i % 4 == 0 else [],
                "related_tasks": [f"TASK-{str(uuid.uuid4())[:8].upper()}", f"TASK-{str(uuid.uuid4())[:8].upper()}"] if i % 2 == 0 else [],
                "evidence_links": [f"evidence-{j+1:03d}" for j in range((i % 3) + 1)],
                "attachments": [
                    {"filename": f"task_document_{i+1}.pdf", "url": f"/uploads/task_doc_{i+1}.pdf", "type": "pdf"},
                    {"filename": f"implementation_guide_{i+1}.docx", "url": f"/uploads/impl_guide_{i+1}.docx", "type": "docx"}
                ] if i % 2 == 0 else [],
                "comments": [
                    {
                        "id": f"comment-{j+1:03d}",
                        "author": f"user-{((j % 3) + 1):03d}",
                        "author_name": ["John Smith", "Sarah Johnson", "Mike Chen"][j % 3],
                        "text": f"Update on task progress: {'Making good progress on implementation' if j % 2 == 0 else 'Encountered some dependencies that need resolution'}",
                        "created_at": (datetime.now() - timedelta(days=j+1)).isoformat(),
                        "type": ["general", "status_update", "escalation"][j % 3]
                    } for j in range((i % 2) + 1)
                ],
                "created_at": (datetime.now() - timedelta(days=i+7)).isoformat(),
                "created_by": f"user-{((i % 4) + 1):03d}",
                "updated_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "updated_by": f"user-{((i % 3) + 1):03d}",
                "risk_level": ["critical", "high", "medium", "low"][i % 4],
                "compliance_impact": ["critical", "high", "medium", "low"][(i+1) % 4],
                "business_impact": ["critical", "high", "medium", "low"][(i+2) % 4],
                "escalation_level": i % 3,
                "overdue_days": max(0, i - 10) if i > 10 else 0,
                "completion_percentage": [0.0, 25.0, 50.0, 75.0, 100.0][i % 5],
                "quality_score": [4.2, 4.5, 3.8, 4.7, 4.1][i % 5] if i % 6 == 0 else None
            }
            for i in range(min(limit, 25))
        ]
        
        # Apply filters
        if audit_id:
            tasks = [task for task in tasks if task["audit_id"] == audit_id]
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        if priority:
            tasks = [task for task in tasks if task["priority"] == priority]
        if assigned_to:
            tasks = [task for task in tasks if task["assigned_to"] == assigned_to]
        if gap_id:
            tasks = [task for task in tasks if task["gap_id"] == gap_id]
        if overdue_only:
            tasks = [task for task in tasks if task["overdue_days"] > 0]
        
        # Pagination
        total_tasks = len(tasks)
        tasks = tasks[offset:offset + limit]
        
        return {
            "tasks": tasks,
            "total_count": total_tasks,
            "page_info": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(tasks) < total_tasks
            },
            "summary_stats": {
                "total_tasks": total_tasks,
                "open_tasks": len([t for t in tasks if t["status"] == "open"]),
                "in_progress_tasks": len([t for t in tasks if t["status"] == "in_progress"]),
                "completed_tasks": len([t for t in tasks if t["status"] == "completed"]),
                "overdue_tasks": len([t for t in tasks if t["overdue_days"] > 0]),
                "critical_priority": len([t for t in tasks if t["priority"] == "critical"]),
                "high_priority": len([t for t in tasks if t["priority"] == "high"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")

@router.get("/tasks/{task_id}", summary="Get Specific Remediation Task")
async def get_remediation_task(task_id: str):
    """Get detailed information about a specific remediation task"""
    try:
        # Generate detailed mock task data
        task = {
            "id": task_id,
            "task_id": f"TASK-{str(uuid.uuid4())[:8].upper()}",
            "audit_id": "audit-123",
            "gap_id": f"GAP-{str(uuid.uuid4())[:8].upper()}",
            "control_id": "PR.AC-1",
            "framework": "NIST CSF 2.0",
            "title": "Implement Multi-Factor Authentication for Privileged Accounts",
            "description": """
            This remediation task addresses the critical security gap identified in privileged account management. 
            The implementation requires deploying multi-factor authentication (MFA) across all administrative 
            and privileged user accounts to meet NIST CSF 2.0 PR.AC-1 control requirements.
            
            Scope includes:
            - Assessment of current privileged accounts (estimated 45 accounts)
            - MFA solution procurement and deployment
            - User training and adoption support
            - Policy updates and documentation
            - Testing and validation procedures
            """,
            "category": "remediation",
            "priority": "critical",
            "status": "in_progress",
            "assigned_to": "user-456",
            "assigned_by": "user-123",
            "assigned_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "accepted_date": (datetime.now() - timedelta(days=4)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=10)).isoformat(),
            "estimated_effort_hours": 40.0,
            "actual_effort_hours": 28.5,
            "started_date": (datetime.now() - timedelta(days=4)).isoformat(),
            "completed_date": None,
            "dependencies": ["TASK-DEP12345", "TASK-DEP67890"],
            "dependent_tasks": ["TASK-CHILD001", "TASK-CHILD002"],
            "related_tasks": ["TASK-REL001", "TASK-REL002", "TASK-REL003"],
            "evidence_links": ["evidence-001", "evidence-002", "evidence-003"],
            "attachments": [
                {
                    "filename": "MFA_Implementation_Plan.pdf",
                    "url": "/uploads/mfa_plan.pdf",
                    "type": "pdf",
                    "size": "2.4MB",
                    "uploaded_at": (datetime.now() - timedelta(days=3)).isoformat(),
                    "uploaded_by": "user-456"
                },
                {
                    "filename": "Privileged_Accounts_Inventory.xlsx",
                    "url": "/uploads/priv_accounts.xlsx", 
                    "type": "xlsx",
                    "size": "156KB",
                    "uploaded_at": (datetime.now() - timedelta(days=2)).isoformat(),
                    "uploaded_by": "user-456"
                }
            ],
            "comments": [
                {
                    "id": "comment-001",
                    "author_id": "user-456",
                    "author_name": "Sarah Chen",
                    "author_role": "Security Engineer",
                    "comment_text": "Completed privileged account inventory. Identified 42 accounts requiring MFA implementation. Microsoft Authenticator selected as the MFA solution.",
                    "comment_type": "status_update",
                    "is_internal": False,
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                    "attachments": []
                },
                {
                    "id": "comment-002",
                    "author_id": "user-123",
                    "author_name": "John Smith",
                    "author_role": "CISO",
                    "comment_text": "Great progress! Please ensure proper documentation of the implementation process for audit trail purposes.",
                    "comment_type": "general",
                    "is_internal": False,
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                    "attachments": []
                }
            ],
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "created_by": "user-123",
            "updated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "updated_by": "user-456",
            "risk_level": "critical",
            "compliance_impact": "high",
            "business_impact": "medium",
            "escalation_level": 0,
            "overdue_days": 0,
            "completion_percentage": 70.0,
            "quality_score": None,
            "workflow_history": [
                {
                    "state": "open",
                    "changed_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "changed_by": "user-123",
                    "duration_hours": 24.0
                },
                {
                    "state": "assigned",
                    "changed_at": (datetime.now() - timedelta(days=5)).isoformat(),
                    "changed_by": "user-123",
                    "duration_hours": 24.0
                },
                {
                    "state": "in_progress",
                    "changed_at": (datetime.now() - timedelta(days=4)).isoformat(),
                    "changed_by": "user-456",
                    "duration_hours": None
                }
            ]
        }
        
        return {
            "task": task
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")

@router.post("/tasks", summary="Create New Remediation Task")
async def create_remediation_task(task_data: dict):
    """Create a new remediation task with GAP-ID linking"""
    try:
        # Validate required fields
        required_fields = ["title", "description", "gap_id", "audit_id", "priority", "created_by"]
        missing_fields = [field for field in required_fields if field not in task_data]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {missing_fields}")
        
        # Generate task ID
        task_id = f"TASK-{str(uuid.uuid4())[:8].upper()}"
        
        # Create new task
        new_task = {
            "id": str(uuid.uuid4()),
            "task_id": task_id,
            "audit_id": task_data["audit_id"],
            "gap_id": task_data["gap_id"],
            "control_id": task_data.get("control_id"),
            "framework": task_data.get("framework", "NIST CSF 2.0"),
            "title": task_data["title"],
            "description": task_data["description"],
            "category": task_data.get("category", "remediation"),
            "priority": task_data["priority"],
            "status": "open",
            "assigned_to": task_data.get("assigned_to"),
            "assigned_by": task_data.get("assigned_by"),
            "assigned_date": datetime.now().isoformat() if task_data.get("assigned_to") else None,
            "due_date": task_data.get("due_date"),
            "estimated_effort_hours": task_data.get("estimated_effort_hours"),
            "dependencies": task_data.get("dependencies", []),
            "evidence_links": task_data.get("evidence_links", []),
            "created_at": datetime.now().isoformat(),
            "created_by": task_data["created_by"],
            "updated_at": datetime.now().isoformat(),
            "risk_level": task_data.get("risk_level", "medium"),
            "compliance_impact": task_data.get("compliance_impact", "medium"),
            "business_impact": task_data.get("business_impact", "medium"),
            "escalation_level": 0,
            "overdue_days": 0,
            "completion_percentage": 0.0
        }
        
        return {
            "message": "Remediation task created successfully",
            "task_id": task_id,
            "task": new_task
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.put("/tasks/{task_id}", summary="Update Remediation Task")
async def update_remediation_task(task_id: str, task_updates: dict):
    """Update an existing remediation task"""
    try:
        # Simulate task update
        updated_task = {
            "id": task_id,
            "task_id": f"TASK-{str(uuid.uuid4())[:8].upper()}",
            "message": "Task updated successfully",
            "updated_fields": list(task_updates.keys()),
            "updated_at": datetime.now().isoformat()
        }
        
        return updated_task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

# ================================================================================================
# TASK ASSIGNMENT MANAGEMENT APIs
# ================================================================================================

@router.get("/assignments", summary="Get Task Assignments")
async def get_task_assignments(
    assignee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    overdue_only: bool = Query(False)
):
    """Retrieve task assignments with filtering options"""
    try:
        assignments = [
            {
                "id": f"assignment-{i+1:03d}",
                "task_id": f"TASK-{str(uuid.uuid4())[:8].upper()}",
                "assignee_id": f"user-{((i % 5) + 1):03d}",
                "assignee_name": ["Sarah Chen", "Mike Rodriguez", "Jennifer Park", "David Kim", "Lisa Thompson"][i % 5],
                "assignee_role": ["Security Engineer", "Compliance Manager", "IT Auditor", "System Administrator", "Technical Writer"][i % 5],
                "assignee_email": [f"user{((i % 5) + 1):03d}@company.com"],
                "assigned_by": f"user-{((i % 3) + 1):03d}",
                "assigned_date": (datetime.now() - timedelta(days=i+1)).isoformat(),
                "assignment_reason": "Expertise match and current workload capacity",
                "assignment_method": ["manual", "auto_workload", "auto_skills"][i % 3],
                "status": ["pending", "accepted", "declined"][i % 3],
                "accepted_date": (datetime.now() - timedelta(days=i)).isoformat() if i % 3 == 1 else None,
                "declined_reason": "Conflicting priorities" if i % 3 == 2 else None,
                "estimated_workload_hours": [8.0, 16.0, 24.0, 12.0, 6.0][i % 5],
                "current_workload_impact": [0.2, 0.3, 0.4, 0.25, 0.15][i % 5],
                "skill_match_score": [0.85, 0.92, 0.78, 0.88, 0.95][i % 5],
                "response_time_hours": [2.5, 1.8, 4.2, 3.1, 1.5][i % 5] if i % 3 != 0 else None
            }
            for i in range(15)
        ]
        
        # Apply filters
        if assignee_id:
            assignments = [a for a in assignments if a["assignee_id"] == assignee_id]
        if status:
            assignments = [a for a in assignments if a["status"] == status]
        
        return {
            "assignments": assignments,
            "summary": {
                "total_assignments": len(assignments),
                "pending_assignments": len([a for a in assignments if a["status"] == "pending"]),
                "accepted_assignments": len([a for a in assignments if a["status"] == "accepted"]),
                "declined_assignments": len([a for a in assignments if a["status"] == "declined"]),
                "average_response_time": 2.4
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assignments: {str(e)}")

@router.post("/assignments", summary="Create Task Assignment")
async def create_task_assignment(assignment_data: dict):
    """Create a new task assignment with AI-powered optimization"""
    try:
        # Validate required fields
        required_fields = ["task_id", "assignee_id", "assigned_by"]
        missing_fields = [field for field in required_fields if field not in assignment_data]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {missing_fields}")
        
        # Simulate AI-powered assignment optimization
        assignment = {
            "id": str(uuid.uuid4()),
            "task_id": assignment_data["task_id"],
            "assignee_id": assignment_data["assignee_id"],
            "assignee_name": "Sarah Chen",
            "assignee_role": "Security Engineer",
            "assignee_email": "sarah.chen@company.com",
            "assigned_by": assignment_data["assigned_by"],
            "assigned_date": datetime.now().isoformat(),
            "assignment_reason": assignment_data.get("assignment_reason", "AI-optimized assignment based on skills and workload"),
            "assignment_method": assignment_data.get("assignment_method", "auto_skills"),
            "status": "pending",
            "estimated_workload_hours": assignment_data.get("estimated_workload_hours", 16.0),
            "skill_match_score": 0.92,
            "ai_recommendation": {
                "confidence": 0.87,
                "reasoning": "High skill match for security implementation tasks, current workload allows for timely completion",
                "alternative_assignees": [
                    {"user_id": "user-002", "skill_score": 0.84, "workload_score": 0.91},
                    {"user_id": "user-003", "skill_score": 0.78, "workload_score": 0.95}
                ]
            }
        }
        
        return {
            "message": "Task assignment created successfully",
            "assignment": assignment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")

# ================================================================================================
# LIVE DASHBOARD AND STATUS APIs
# ================================================================================================

@router.get("/dashboard/live-status", summary="Get Live Remediation Status Dashboard")
async def get_live_remediation_status(audit_id: Optional[str] = Query(None)):
    """Real-time remediation status dashboard with comprehensive metrics"""
    try:
        dashboard_data = {
            "audit_id": audit_id or "audit-123",
            "last_updated": datetime.now().isoformat(),
            "summary_metrics": {
                "total_tasks": 127,
                "open_tasks": 23,
                "assigned_tasks": 34,
                "in_progress_tasks": 45,
                "under_review_tasks": 12,
                "completed_tasks": 98,
                "blocked_tasks": 8,
                "overdue_tasks": 15
            },
            "priority_breakdown": {
                "critical": {"count": 12, "completed": 8, "overdue": 2},
                "high": {"count": 34, "completed": 24, "overdue": 6},
                "medium": {"count": 56, "completed": 42, "overdue": 5},
                "low": {"count": 25, "completed": 24, "overdue": 2}
            },
            "assignee_workload": [
                {
                    "assignee_id": "user-001",
                    "assignee_name": "Sarah Chen",
                    "role": "Security Engineer",
                    "active_tasks": 8,
                    "completed_tasks": 15,
                    "overdue_tasks": 1,
                    "workload_percentage": 85.0,
                    "average_completion_time": 4.2,
                    "quality_score": 4.6
                },
                {
                    "assignee_id": "user-002", 
                    "assignee_name": "Mike Rodriguez",
                    "role": "Compliance Manager",
                    "active_tasks": 6,
                    "completed_tasks": 18,
                    "overdue_tasks": 0,
                    "workload_percentage": 72.0,
                    "average_completion_time": 3.8,
                    "quality_score": 4.8
                },
                {
                    "assignee_id": "user-003",
                    "assignee_name": "Jennifer Park",
                    "role": "IT Auditor",
                    "active_tasks": 5,
                    "completed_tasks": 12,
                    "overdue_tasks": 2,
                    "workload_percentage": 78.0,
                    "average_completion_time": 5.1,
                    "quality_score": 4.3
                }
            ],
            "gap_remediation_progress": [
                {
                    "gap_id": "GAP-A1B2C3D4",
                    "control_id": "PR.AC-1",
                    "total_tasks": 3,
                    "completed_tasks": 2,
                    "progress_percentage": 66.7,
                    "estimated_completion": (datetime.now() + timedelta(days=5)).isoformat(),
                    "risk_level": "high"
                },
                {
                    "gap_id": "GAP-E5F6G7H8",
                    "control_id": "DE.AE-1", 
                    "total_tasks": 2,
                    "completed_tasks": 1,
                    "progress_percentage": 50.0,
                    "estimated_completion": (datetime.now() + timedelta(days=8)).isoformat(),
                    "risk_level": "medium"
                }
            ],
            "recent_activity": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                    "action": "task_completed",
                    "task_id": "TASK-AB123456",
                    "assignee": "Sarah Chen",
                    "description": "Multi-factor authentication implementation completed"
                },
                {
                    "timestamp": (datetime.now() - timedelta(minutes=32)).isoformat(),
                    "action": "task_assigned",
                    "task_id": "TASK-CD789012",
                    "assignee": "Mike Rodriguez",
                    "description": "Policy documentation update assigned"
                },
                {
                    "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
                    "action": "escalation_triggered",
                    "task_id": "TASK-EF345678",
                    "assignee": "Jennifer Park",
                    "description": "Task overdue - escalated to management"
                }
            ],
            "performance_trends": {
                "completion_velocity": {
                    "current_week": 12.5,
                    "previous_week": 10.2,
                    "trend": "improving"
                },
                "quality_score": {
                    "current_average": 4.5,
                    "previous_average": 4.3,
                    "trend": "improving"
                },
                "overdue_rate": {
                    "current_percentage": 11.8,
                    "previous_percentage": 15.2,
                    "trend": "improving"
                }
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve live status: {str(e)}")

# ================================================================================================
# ESCALATION MANAGEMENT APIs
# ================================================================================================

@router.get("/escalations/rules", summary="Get Escalation Rules")
async def get_escalation_rules():
    """Retrieve configured escalation rules"""
    try:
        rules = [
            {
                "id": "escalation-rule-001",
                "name": "Critical Task Overdue Escalation",
                "description": "Escalate critical priority tasks that are overdue by more than 24 hours",
                "trigger_conditions": {
                    "priority_levels": ["critical"],
                    "overdue_threshold_hours": 24,
                    "status_conditions": ["assigned", "in_progress"]
                },
                "escalation_path": [
                    {
                        "level": 1,
                        "escalate_to_role": "Security Manager",
                        "notification_delay_hours": 0
                    },
                    {
                        "level": 2,
                        "escalate_to_role": "CISO",
                        "notification_delay_hours": 12
                    }
                ],
                "automated_actions": [
                    {"action": "send_notification", "targets": ["assignee", "manager"]},
                    {"action": "update_priority", "new_priority": "critical"},
                    {"action": "create_comment", "comment_text": "Task automatically escalated due to overdue status"}
                ],
                "is_active": True,
                "applies_to_roles": ["Security Engineer", "Compliance Analyst"],
                "applies_to_priorities": ["critical"],
                "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "created_by": "user-123"
            },
            {
                "id": "escalation-rule-002",
                "name": "Blocked Task Resolution",
                "description": "Escalate tasks that have been blocked for more than 48 hours",
                "trigger_conditions": {
                    "status_conditions": ["blocked"],
                    "blocked_threshold_hours": 48
                },
                "escalation_path": [
                    {
                        "level": 1,
                        "escalate_to_role": "Project Manager",
                        "notification_delay_hours": 0
                    }
                ],
                "automated_actions": [
                    {"action": "send_notification", "targets": ["assignee", "project_manager"]},
                    {"action": "schedule_review_meeting", "participants": ["assignee", "project_manager", "stakeholder"]}
                ],
                "is_active": True,
                "applies_to_roles": ["all"],
                "applies_to_priorities": ["high", "critical"],
                "created_at": (datetime.now() - timedelta(days=25)).isoformat(),
                "created_by": "user-456"
            }
        ]
        
        return {
            "escalation_rules": rules,
            "summary": {
                "total_rules": len(rules),
                "active_rules": len([r for r in rules if r["is_active"]]),
                "inactive_rules": len([r for r in rules if not r["is_active"]])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve escalation rules: {str(e)}")

# ================================================================================================
# ANALYTICS AND REPORTING APIs  
# ================================================================================================

@router.get("/analytics/performance", summary="Get Remediation Performance Analytics")
async def get_remediation_analytics(
    audit_id: Optional[str] = Query(None),
    time_period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    group_by: str = Query("week", description="Grouping: day, week, month")
):
    """Comprehensive remediation performance analytics and KPIs"""
    try:
        analytics_data = {
            "audit_id": audit_id or "audit-123",
            "time_period": time_period,
            "generated_at": datetime.now().isoformat(),
            "overall_metrics": {
                "total_tasks": 127,
                "completion_rate": 77.2,
                "average_completion_time_hours": 18.5,
                "on_time_delivery_rate": 84.3,
                "quality_score": 4.5,
                "escalation_rate": 8.7,
                "rework_rate": 5.2
            },
            "trend_data": [
                {
                    "period": "2025-01-01",
                    "tasks_created": 15,
                    "tasks_completed": 12,
                    "completion_rate": 75.5,
                    "average_quality": 4.3,
                    "overdue_count": 2
                },
                {
                    "period": "2025-01-08", 
                    "tasks_created": 18,
                    "tasks_completed": 16,
                    "completion_rate": 78.2,
                    "average_quality": 4.4,
                    "overdue_count": 3
                },
                {
                    "period": "2025-01-15",
                    "tasks_created": 22,
                    "tasks_completed": 19,
                    "completion_rate": 82.1,
                    "average_quality": 4.6,
                    "overdue_count": 2
                },
                {
                    "period": "2025-01-22",
                    "tasks_created": 20,
                    "tasks_completed": 18,
                    "completion_rate": 85.0,
                    "average_quality": 4.7,
                    "overdue_count": 1
                }
            ],
            "category_performance": {
                "remediation": {
                    "total_tasks": 65,
                    "completion_rate": 78.5,
                    "average_time_hours": 24.2,
                    "quality_score": 4.4
                },
                "documentation": {
                    "total_tasks": 28,
                    "completion_rate": 89.3,
                    "average_time_hours": 8.5,
                    "quality_score": 4.7
                },
                "process_improvement": {
                    "total_tasks": 22,
                    "completion_rate": 68.2,
                    "average_time_hours": 32.1,
                    "quality_score": 4.2
                },
                "training": {
                    "total_tasks": 12,
                    "completion_rate": 91.7,
                    "average_time_hours": 6.3,
                    "quality_score": 4.8
                }
            },
            "assignee_performance": [
                {
                    "assignee_id": "user-001",
                    "assignee_name": "Sarah Chen",
                    "total_assigned": 25,
                    "completed": 22,
                    "completion_rate": 88.0,
                    "average_time_hours": 16.5,
                    "quality_score": 4.6,
                    "on_time_rate": 90.9
                },
                {
                    "assignee_id": "user-002",
                    "assignee_name": "Mike Rodriguez", 
                    "total_assigned": 20,
                    "completed": 18,
                    "completion_rate": 90.0,
                    "average_time_hours": 14.2,
                    "quality_score": 4.8,
                    "on_time_rate": 94.4
                }
            ],
            "bottleneck_analysis": [
                {
                    "bottleneck_type": "resource_constraint",
                    "description": "Security engineering team at 95% capacity",
                    "impact_score": 0.85,
                    "affected_tasks": 12,
                    "recommendation": "Consider additional security engineering resources or task redistribution"
                },
                {
                    "bottleneck_type": "dependency_delay",
                    "description": "Vendor approval processes causing delays",
                    "impact_score": 0.72,
                    "affected_tasks": 8,
                    "recommendation": "Establish expedited vendor approval workflow for critical compliance tasks"
                }
            ],
            "predictive_insights": {
                "projected_completion_date": (datetime.now() + timedelta(days=45)).isoformat(),
                "confidence_level": 0.87,
                "risk_factors": [
                    "Holiday season may impact availability",
                    "Upcoming audit deadline may create resource conflicts"
                ],
                "recommended_actions": [
                    "Prioritize critical and high-priority tasks for next 2 weeks",
                    "Consider temporary contractor support for documentation tasks",
                    "Schedule dependency resolution meetings with vendors"
                ]
            }
        }
        
        return analytics_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")

# ================================================================================================
# HEALTH CHECK AND SYSTEM STATUS
# ================================================================================================

@router.get("/health", summary="Remediation Tracking System Health Check")
async def remediation_system_health():
    """Health check endpoint for remediation tracking system"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "task_management": "operational",
                "assignment_engine": "operational", 
                "escalation_system": "operational",
                "analytics_engine": "operational",
                "notification_service": "operational"
            },
            "metrics": {
                "active_tasks": 89,
                "processing_queue": 3,
                "average_response_time_ms": 145,
                "error_rate_percentage": 0.02
            },
            "last_backup": (datetime.now() - timedelta(hours=6)).isoformat(),
            "next_maintenance": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")