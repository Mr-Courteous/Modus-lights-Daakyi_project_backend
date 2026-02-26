"""
DAAKYI CompaaS - Audit Readiness Tracker API
Comprehensive audit preparation management system with enhanced AI capabilities
"""
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from bson import ObjectId
import logging

# Database and AI service imports
from database import get_database
from ai_service import ai_service
from auth import get_current_user
from models import User

# Enhanced AI imports
from enhanced_ai_analytics import enhanced_ai_engine, TemporalDataPoint
from dynamic_remediation_engine import dynamic_remediation_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit-readiness", tags=["audit-readiness"])

# Pydantic Models for Audit Readiness Tracker

# Phase 3: Gap Analysis Models
class EvidenceGap(BaseModel):
    gap_id: str = Field(default_factory=lambda: f"GAP-{str(uuid.uuid4())[:8].upper()}")
    control_id: str
    control_title: str
    framework: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    gap_description: str
    evidence_required: List[str] = []
    evidence_provided: List[str] = []
    evidence_sufficiency_score: float  # 0.0 to 1.0
    remediation_timeline: int  # days to remediate
    remediation_effort: str  # 'low', 'medium', 'high', 'very_high'
    business_impact: str  # 'critical', 'high', 'medium', 'low'
    current_maturity_level: int  # 1-5 scale
    target_maturity_level: int  # 1-5 scale
    assigned_to: List[str] = []  # User IDs
    milestone_dependency: Optional[str] = None  # Milestone ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GapAnalysisSummary(BaseModel):
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    overall_coverage_score: float  # 0.0 to 1.0
    evidence_completion_rate: float  # 0.0 to 1.0
    estimated_remediation_days: int
    framework_distribution: Dict[str, int]
    maturity_assessment: Dict[str, float]

class ControlEvidenceMapping(BaseModel):
    control_id: str
    control_title: str
    framework: str
    evidence_requirements: List[str]
    evidence_artifacts: List[Dict[str, Any]]  # Links to evidence files
    coverage_percentage: float  # 0.0 to 100.0
    gap_status: str  # 'no_gap', 'minor_gap', 'major_gap', 'critical_gap'
    last_reviewed: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

class EnhancedDashboardMetrics(BaseModel):
    readiness_trends: List[Dict[str, Any]]
    predictive_forecasts: Dict[str, Any]
    risk_indicators: Dict[str, Any]
    improvement_recommendations: List[str]
    benchmark_comparisons: Dict[str, float]

# Phase 4A: Milestone Performance Intelligence Models
class GapClosureVelocity(BaseModel):
    velocity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audit_id: str
    gap_id: str
    closure_date: datetime
    days_to_closure: int
    original_timeline: int
    velocity_score: float  # actual_days / planned_days (lower is better)
    complexity_factor: str  # 'low', 'medium', 'high', 'very_high'
    team_size: int
    resource_utilization: float  # 0.0 to 1.0
    blockers_encountered: List[str] = []
    acceleration_factors: List[str] = []

class TimelineRiskFactor(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audit_id: str
    milestone_id: Optional[str] = None
    risk_type: str  # 'resource', 'dependency', 'complexity', 'external', 'technical'
    risk_description: str
    probability: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0
    risk_score: float  # probability * impact
    timeline_impact_days: int
    mitigation_strategies: List[str] = []
    current_status: str  # 'identified', 'mitigating', 'resolved', 'accepted'
    owner: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceHeatMapData(BaseModel):
    team_member_id: str
    name: str
    role: str
    current_workload: float  # 0.0 to 1.0 (percentage)
    capacity: float  # 0.0 to 1.0 (percentage)
    utilization_rate: float  # workload / capacity
    assigned_gaps: List[str] = []  # GAP-IDs
    assigned_milestones: List[str] = []  # Milestone IDs
    expertise_areas: List[str] = []
    availability_forecast: Dict[str, float] = {}  # date -> availability
    burnout_risk: str  # 'low', 'medium', 'high', 'critical'
    performance_trend: str  # 'improving', 'stable', 'declining'

class PerformanceKPI(BaseModel):
    kpi_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audit_id: str
    kpi_name: str
    kpi_type: str  # 'velocity', 'quality', 'resource', 'timeline', 'risk'
    current_value: float
    target_value: float
    baseline_value: float
    trend_direction: str  # 'up', 'down', 'stable'
    performance_rating: str  # 'excellent', 'good', 'average', 'poor', 'critical'
    measurement_unit: str
    calculation_method: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    historical_values: List[Dict[str, Any]] = []  # date-value pairs

class MilestonePerformanceMetrics(BaseModel):
    milestone_id: str
    milestone_name: str
    planned_start: datetime
    planned_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    completion_percentage: float  # 0.0 to 100.0
    velocity_score: float  # planned_duration / actual_duration
    quality_score: float  # 0.0 to 100.0
    effort_variance: float  # actual_effort / planned_effort
    blockers_count: int
    dependencies_satisfied: bool
    team_performance: Dict[str, float] = {}  # team_member -> performance_score
    risk_mitigation_effectiveness: float  # 0.0 to 1.0

class AuditMilestone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    due_date: datetime
    status: str  # 'not_started', 'in_progress', 'completed', 'overdue'
    category: str  # 'preparation', 'documentation', 'review', 'remediation'
    priority: str  # 'low', 'medium', 'high', 'critical'
    assigned_to: List[str] = []  # User IDs
    dependencies: List[str] = []  # Milestone IDs that must be completed first
    completion_percentage: int = 0
    evidence_required: List[str] = []
    evidence_collected: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AuditArtifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: str  # 'policy', 'procedure', 'evidence', 'report', 'log', 'screenshot'
    status: str  # 'missing', 'draft', 'review', 'approved', 'expired'
    priority: str  # 'low', 'medium', 'high', 'critical'
    framework_controls: List[str] = []  # Control IDs this artifact supports
    file_path: Optional[str] = None
    file_size: Optional[str] = None
    owner: str  # User ID
    reviewers: List[str] = []
    due_date: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None
    version: str = "1.0"
    ai_confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AuditSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audit_name: str
    audit_type: str  # 'internal', 'external', 'certification', 'surveillance'
    framework: str  # 'NIST CSF 2.0', 'ISO 27001:2022', 'SOC 2', 'GDPR'
    scheduled_date: datetime
    preparation_start: datetime
    audit_duration_days: int = 5
    status: str  # 'scheduled', 'preparing', 'in_progress', 'completed', 'cancelled'
    auditor_organization: Optional[str] = None
    audit_scope: List[str] = []  # Areas/departments to be audited
    team_lead: str  # User ID
    preparation_team: List[str] = []  # User IDs
    milestones: List[str] = []  # Milestone IDs
    readiness_score: float = 0.0  # 0-100 calculated score
    confidence_level: str = "medium"  # 'low', 'medium', 'high'
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReadinessAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audit_id: str
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    overall_score: float = 0.0  # 0-100
    category_scores: Dict[str, float] = {}  # Category: score mapping
    gap_count: int = 0
    high_priority_gaps: int = 0
    documentation_completeness: float = 0.0
    evidence_availability: float = 0.0
    team_preparedness: float = 0.0
    ai_insights: List[str] = []
    recommendations: List[str] = []
    predicted_outcome: str = "medium"  # 'low', 'medium', 'high' confidence
    confidence_intervals: Dict[str, Dict[str, float]] = {}
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditTeamMember(BaseModel):
    user_id: str
    name: str
    email: str
    role: str  # 'lead', 'coordinator', 'specialist', 'reviewer'
    expertise_areas: List[str] = []
    workload_percentage: int = 0  # Current workload 0-100
    assigned_milestones: List[str] = []
    assigned_artifacts: List[str] = []

class CreateAuditScheduleRequest(BaseModel):
    audit_name: str
    audit_type: str
    framework: str
    scheduled_date: datetime
    preparation_start: datetime
    audit_duration_days: int = 5
    auditor_organization: Optional[str] = None
    audit_scope: List[str] = []
    team_lead: str
    preparation_team: List[str] = []

class UpdateMilestoneRequest(BaseModel):
    status: Optional[str] = None
    completion_percentage: Optional[int] = None
    evidence_collected: Optional[List[str]] = None
    assigned_to: Optional[List[str]] = None

# API Endpoints

@router.get("/dashboard")
async def get_audit_readiness_dashboard(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive audit readiness dashboard overview"""
    try:
        # Mock data for development - in production, this would aggregate from database
        current_time = datetime.utcnow()
        
        dashboard_data = {
            "summary": {
                "upcoming_audits": 2,
                "active_preparations": 1,
                "overdue_milestones": 3,
                "completion_rate": 78.5,
                "average_readiness_score": 84.2,
                "total_artifacts": 147,
                "approved_artifacts": 112,
                "pending_reviews": 8
            },
            "upcoming_audits": [
                {
                    "id": "audit-001",
                    "audit_name": "Q2 2025 ISO 27001:2022 Certification Audit",
                    "framework": "ISO 27001:2022",
                    "audit_type": "certification",
                    "scheduled_date": current_time + timedelta(days=45),
                    "preparation_start": current_time - timedelta(days=15),
                    "readiness_score": 87.3,
                    "confidence_level": "high",
                    "status": "preparing",
                    "days_remaining": 45,
                    "team_lead": "Sarah Johnson",
                    "preparation_team": ["John Smith", "Lisa Davis", "Mike Chen"],
                    "critical_gaps": 2,
                    "overdue_items": 1
                },
                {
                    "id": "audit-002", 
                    "audit_name": "NIST CSF 2.0 Internal Assessment Review",
                    "framework": "NIST CSF 2.0",
                    "audit_type": "internal",
                    "scheduled_date": current_time + timedelta(days=78),
                    "preparation_start": current_time + timedelta(days=48),
                    "readiness_score": 71.8,
                    "confidence_level": "medium",
                    "status": "scheduled",
                    "days_remaining": 78,
                    "team_lead": "John Smith",
                    "preparation_team": ["Sarah Johnson", "Mike Chen"],
                    "critical_gaps": 5,
                    "overdue_items": 0
                }
            ],
            "readiness_trends": [
                {"date": "2025-01-20", "score": 76.2},
                {"date": "2025-01-21", "score": 78.1},
                {"date": "2025-01-22", "score": 79.8},
                {"date": "2025-01-23", "score": 82.4},
                {"date": "2025-01-24", "score": 84.2},
                {"date": "2025-01-25", "score": 84.2},
                {"date": "2025-01-26", "score": 84.2}
            ],
            "critical_milestones": [
                {
                    "id": "milestone-001",
                    "name": "Complete ISMS Documentation Review",
                    "audit_id": "audit-001",
                    "due_date": current_time + timedelta(days=12),
                    "status": "in_progress",
                    "priority": "critical",
                    "completion_percentage": 65,
                    "assigned_to": ["Sarah Johnson", "Lisa Davis"],
                    "overdue": False
                },
                {
                    "id": "milestone-002",
                    "name": "Vendor Risk Assessment Updates",
                    "audit_id": "audit-001", 
                    "due_date": current_time + timedelta(days=8),
                    "status": "in_progress",
                    "priority": "high",
                    "completion_percentage": 40,
                    "assigned_to": ["Mike Chen"],
                    "overdue": False
                },
                {
                    "id": "milestone-003",
                    "name": "Employee Security Training Records",
                    "audit_id": "audit-001",
                    "due_date": current_time - timedelta(days=2),
                    "status": "in_progress", 
                    "priority": "critical",
                    "completion_percentage": 25,
                    "assigned_to": ["John Smith"],
                    "overdue": True
                }
            ],
            "ai_insights": {
                "predictive_score": 87.3,
                "confidence_interval": {"lower": 83.1, "upper": 91.5},
                "risk_factors": [
                    "Training records completion behind schedule",
                    "Vendor assessments require expedited reviews",
                    "Documentation version control needs attention"
                ],
                "recommendations": [
                    "Prioritize completing overdue training records",
                    "Schedule additional vendor assessment reviews",
                    "Implement automated documentation tracking",
                    "Consider extending preparation timeline by 1 week"
                ],
                "success_probability": 0.89
            }
        }
        
        logger.info(f"Retrieved audit readiness dashboard for user {current_user.id}")
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Error getting audit readiness dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit readiness dashboard")

@router.get("/schedules")
async def get_audit_schedules(
    status: Optional[str] = None,
    framework: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all audit schedules with optional filtering"""
    try:
        current_time = datetime.utcnow()
        
        # Mock audit schedules data
        mock_schedules = [
            {
                "id": "audit-001",
                "audit_name": "Q2 2025 ISO 27001:2022 Certification Audit",
                "audit_type": "certification",
                "framework": "ISO 27001:2022",
                "scheduled_date": current_time + timedelta(days=45),
                "preparation_start": current_time - timedelta(days=15),
                "audit_duration_days": 3,
                "status": "preparing",
                "auditor_organization": "SecureAudit Pro",
                "audit_scope": ["Information Security", "Risk Management", "Business Continuity"],
                "team_lead": "user-001",
                "preparation_team": ["user-002", "user-003", "user-004"],
                "readiness_score": 87.3,
                "confidence_level": "high",
                "created_by": current_user.id,
                "created_at": current_time - timedelta(days=30),
                "updated_at": current_time - timedelta(hours=2)
            },
            {
                "id": "audit-002",
                "audit_name": "NIST CSF 2.0 Internal Assessment Review", 
                "audit_type": "internal",
                "framework": "NIST CSF 2.0",
                "scheduled_date": current_time + timedelta(days=78),
                "preparation_start": current_time + timedelta(days=48),
                "audit_duration_days": 5,
                "status": "scheduled",
                "auditor_organization": None,
                "audit_scope": ["Governance", "Risk Management", "Asset Management"],
                "team_lead": "user-002",
                "preparation_team": ["user-001", "user-004"],
                "readiness_score": 71.8,
                "confidence_level": "medium",
                "created_by": current_user.id,
                "created_at": current_time - timedelta(days=20),
                "updated_at": current_time - timedelta(days=5)
            }
        ]
        
        # Apply filters
        filtered_schedules = mock_schedules
        if status:
            filtered_schedules = [s for s in filtered_schedules if s["status"] == status]
        if framework:
            filtered_schedules = [s for s in filtered_schedules if framework.lower() in s["framework"].lower()]
        
        logger.info(f"Retrieved {len(filtered_schedules)} audit schedules")
        return {"schedules": filtered_schedules}
    
    except Exception as e:
        logger.error(f"Error getting audit schedules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit schedules")

@router.post("/schedules")
async def create_audit_schedule(
    schedule_request: CreateAuditScheduleRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a new audit schedule"""
    try:
        schedule_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Create schedule document
        schedule_data = {
            "id": schedule_id,
            "audit_name": schedule_request.audit_name,
            "audit_type": schedule_request.audit_type,
            "framework": schedule_request.framework,
            "scheduled_date": schedule_request.scheduled_date,
            "preparation_start": schedule_request.preparation_start,
            "audit_duration_days": schedule_request.audit_duration_days,
            "status": "scheduled",
            "auditor_organization": schedule_request.auditor_organization,
            "audit_scope": schedule_request.audit_scope,
            "team_lead": schedule_request.team_lead,
            "preparation_team": schedule_request.preparation_team,
            "milestones": [],
            "readiness_score": 0.0,
            "confidence_level": "medium",
            "created_by": current_user.id,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # Insert into database (mock for development)
        # In production, this would actually insert into the database
        # result = await db.audit_schedules.insert_one(schedule_data)
        
        # Schedule background task to create default milestones
        background_tasks.add_task(
            create_default_milestones,
            schedule_id,
            schedule_request.framework,
            schedule_request.preparation_start,
            schedule_request.scheduled_date
        )
        
        logger.info(f"Created audit schedule: {schedule_id}")
        
        return {
            "schedule": schedule_data,
            "message": "Audit schedule created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating audit schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create audit schedule")

@router.get("/{audit_id}/milestones")
async def get_audit_milestones(
    audit_id: str,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get milestones for a specific audit"""
    try:
        current_time = datetime.utcnow()
        
        # Mock milestones data
        mock_milestones = [
            {
                "id": "milestone-001",
                "name": "Complete ISMS Documentation Review",
                "description": "Review and update all Information Security Management System documentation including policies, procedures, and work instructions",
                "due_date": current_time + timedelta(days=12),
                "status": "in_progress",
                "category": "documentation",
                "priority": "critical",
                "assigned_to": ["user-001", "user-002"],
                "dependencies": [],
                "completion_percentage": 65,
                "evidence_required": ["policy_documents", "procedure_updates", "approval_records"],
                "evidence_collected": ["policy_documents", "procedure_updates"],
                "created_at": current_time - timedelta(days=10),
                "updated_at": current_time - timedelta(hours=4)
            },
            {
                "id": "milestone-002",
                "name": "Vendor Risk Assessment Updates",
                "description": "Complete risk assessments for all critical vendors and update vendor management documentation",
                "due_date": current_time + timedelta(days=8),
                "status": "in_progress",
                "category": "review",
                "priority": "high",
                "assigned_to": ["user-003"],
                "dependencies": ["milestone-004"],
                "completion_percentage": 40,
                "evidence_required": ["vendor_assessments", "risk_matrices", "mitigation_plans"],
                "evidence_collected": ["vendor_assessments"],
                "created_at": current_time - timedelta(days=8),
                "updated_at": current_time - timedelta(days=1)
            },
            {
                "id": "milestone-003",
                "name": "Employee Security Training Records",
                "description": "Ensure all employees have completed required security awareness training and maintain updated training records",
                "due_date": current_time - timedelta(days=2),
                "status": "in_progress",
                "category": "preparation",
                "priority": "critical",
                "assigned_to": ["user-004"],
                "dependencies": [],
                "completion_percentage": 25,
                "evidence_required": ["training_records", "completion_certificates", "attendance_logs"],
                "evidence_collected": [],
                "created_at": current_time - timedelta(days=12),
                "updated_at": current_time - timedelta(days=3)
            },
            {
                "id": "milestone-004",
                "name": "Asset Inventory Verification",
                "description": "Verify and update complete asset inventory including hardware, software, and data assets",
                "due_date": current_time + timedelta(days=5),
                "status": "completed",
                "category": "preparation",
                "priority": "medium",
                "assigned_to": ["user-002", "user-003"],
                "dependencies": [],
                "completion_percentage": 100,
                "evidence_required": ["asset_register", "verification_reports", "reconciliation_logs"],
                "evidence_collected": ["asset_register", "verification_reports", "reconciliation_logs"],
                "created_at": current_time - timedelta(days=20),
                "updated_at": current_time - timedelta(days=1)
            }
        ]
        
        # Apply status filter if provided
        filtered_milestones = mock_milestones
        if status:
            filtered_milestones = [m for m in filtered_milestones if m["status"] == status]
        
        logger.info(f"Retrieved {len(filtered_milestones)} milestones for audit {audit_id}")
        return {"milestones": filtered_milestones}
    
    except Exception as e:
        logger.error(f"Error getting audit milestones: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit milestones")

@router.put("/{audit_id}/milestones/{milestone_id}")
async def update_milestone(
    audit_id: str,
    milestone_id: str,
    update_request: UpdateMilestoneRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update a specific milestone"""
    try:
        # In production, this would update the database
        update_data = {
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.id
        }
        
        # Add fields that were provided
        if update_request.status:
            update_data["status"] = update_request.status
        if update_request.completion_percentage is not None:
            update_data["completion_percentage"] = update_request.completion_percentage
        if update_request.evidence_collected is not None:
            update_data["evidence_collected"] = update_request.evidence_collected
        if update_request.assigned_to is not None:
            update_data["assigned_to"] = update_request.assigned_to
        
        # Mock response
        logger.info(f"Updated milestone {milestone_id} for audit {audit_id}")
        
        return {
            "message": "Milestone updated successfully",
            "milestone_id": milestone_id,
            "audit_id": audit_id,
            "updated_fields": list(update_data.keys())
        }
    
    except Exception as e:
        logger.error(f"Error updating milestone: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update milestone")

@router.get("/{audit_id}/readiness-assessment")
async def get_readiness_assessment(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get AI-powered readiness assessment for an audit"""
    try:
        current_time = datetime.utcnow()
        
        # Mock readiness assessment with AI insights
        assessment = {
            "id": str(uuid.uuid4()),
            "audit_id": audit_id,
            "assessment_date": current_time,
            "overall_score": 87.3,
            "category_scores": {
                "documentation": 89.2,
                "evidence_collection": 84.7,
                "team_preparedness": 91.1,
                "process_maturity": 85.8,
                "compliance_gaps": 82.4
            },
            "gap_count": 8,
            "high_priority_gaps": 2,
            "documentation_completeness": 89.2,
            "evidence_availability": 84.7,
            "team_preparedness": 91.1,
            "ai_insights": [
                "Training record completion is the primary risk factor affecting readiness score",
                "Documentation review process is performing above industry benchmarks",
                "Vendor risk assessments show strong improvement trend",
                "Team coordination metrics indicate high preparedness level"
            ],
            "recommendations": [
                "Prioritize completion of employee training records (2-day impact on timeline)",
                "Schedule additional vendor assessment review sessions",
                "Consider parallel processing of documentation reviews to accelerate timeline",
                "Implement daily standup meetings for final 14 days of preparation"
            ],
            "predicted_outcome": "high",
            "confidence_intervals": {
                "overall_score": {"lower": 83.1, "upper": 91.5},
                "success_probability": {"lower": 0.85, "upper": 0.93},
                "completion_on_time": {"lower": 0.78, "upper": 0.86}
            },
            "risk_factors": [
                {
                    "factor": "Overdue training records",
                    "impact": "high",
                    "probability": 0.85,
                    "mitigation": "Expedite training completion with dedicated resources"
                },
                {
                    "factor": "Vendor assessment delays",
                    "impact": "medium", 
                    "probability": 0.6,
                    "mitigation": "Parallel review process with additional reviewers"
                }
            ],
            "success_factors": [
                {
                    "factor": "Strong documentation foundation",
                    "contribution": "high",
                    "confidence": 0.92
                },
                {
                    "factor": "Experienced audit team",
                    "contribution": "high",
                    "confidence": 0.89
                },
                {
                    "factor": "Proactive preparation timeline",
                    "contribution": "medium",
                    "confidence": 0.78
                }
            ],
            "created_by": current_user.id,
            "created_at": current_time
        }
        
        logger.info(f"Generated readiness assessment for audit {audit_id}")
        return assessment
    
    except Exception as e:
        logger.error(f"Error getting readiness assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate readiness assessment")

@router.get("/{audit_id}/timeline")
async def get_audit_timeline(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get Gantt-style timeline for audit preparation"""
    try:
        current_time = datetime.utcnow()
        
        # Mock timeline data with Gantt chart structure
        timeline = {
            "audit_id": audit_id,
            "timeline_start": current_time - timedelta(days=15),
            "timeline_end": current_time + timedelta(days=45),
            "current_date": current_time,
            "audit_date": current_time + timedelta(days=45),
            "phases": [
                {
                    "id": "phase-001",
                    "name": "Initial Preparation",
                    "start_date": current_time - timedelta(days=15),
                    "end_date": current_time + timedelta(days=5),
                    "status": "in_progress",
                    "completion_percentage": 75,
                    "color": "#3b82f6"
                },
                {
                    "id": "phase-002", 
                    "name": "Documentation Review",
                    "start_date": current_time - timedelta(days=5),
                    "end_date": current_time + timedelta(days=15),
                    "status": "in_progress",
                    "completion_percentage": 60,
                    "color": "#f59e0b"
                },
                {
                    "id": "phase-003",
                    "name": "Evidence Collection",
                    "start_date": current_time + timedelta(days=5),
                    "end_date": current_time + timedelta(days=25),
                    "status": "scheduled",
                    "completion_percentage": 0,
                    "color": "#10b981"
                },
                {
                    "id": "phase-004",
                    "name": "Final Review & Validation",
                    "start_date": current_time + timedelta(days=20),
                    "end_date": current_time + timedelta(days=40),
                    "status": "scheduled", 
                    "completion_percentage": 0,
                    "color": "#8b5cf6"
                }
            ],
            "milestones": [
                {
                    "id": "milestone-001",
                    "name": "ISMS Documentation Complete",
                    "date": current_time + timedelta(days=12),
                    "status": "upcoming",
                    "critical": True
                },
                {
                    "id": "milestone-002",
                    "name": "All Training Records Updated",
                    "date": current_time + timedelta(days=20),
                    "status": "upcoming", 
                    "critical": True
                },
                {
                    "id": "milestone-003",
                    "name": "Vendor Assessments Complete",
                    "date": current_time + timedelta(days=25),
                    "status": "upcoming",
                    "critical": False
                },
                {
                    "id": "milestone-004",
                    "name": "Audit Preparation Complete",
                    "date": current_time + timedelta(days=40),
                    "status": "upcoming",
                    "critical": True
                }
            ],
            "dependencies": [
                {
                    "from": "phase-001",
                    "to": "phase-002",
                    "type": "finish_to_start"
                },
                {
                    "from": "phase-002", 
                    "to": "phase-003",
                    "type": "finish_to_start"
                },
                {
                    "from": "phase-003",
                    "to": "phase-004",
                    "type": "finish_to_start"
                }
            ]
        }
        
        logger.info(f"Retrieved timeline for audit {audit_id}")
        return timeline
    
    except Exception as e:
        logger.error(f"Error getting audit timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit timeline")

@router.get("/analytics/stats")
async def get_audit_readiness_analytics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get audit readiness analytics and statistics"""
    try:
        # Mock analytics data
        stats = {
            "summary": {
                "total_audits": 12,
                "completed_audits": 8,
                "active_preparations": 2,
                "scheduled_audits": 2,
                "average_readiness_score": 84.2,
                "success_rate": 0.92,
                "average_preparation_time": 45  # days
            },
            "framework_distribution": [
                {"framework": "ISO 27001:2022", "count": 5, "percentage": 42},
                {"framework": "NIST CSF 2.0", "count": 4, "percentage": 33},
                {"framework": "SOC 2", "count": 2, "percentage": 17},
                {"framework": "GDPR", "count": 1, "percentage": 8}
            ],
            "audit_type_distribution": [
                {"type": "certification", "count": 6, "percentage": 50},
                {"type": "internal", "count": 4, "percentage": 33},
                {"type": "surveillance", "count": 2, "percentage": 17}
            ],
            "readiness_trends": [
                {"month": "2024-12", "average_score": 78.4, "audits": 2},
                {"month": "2025-01", "average_score": 84.2, "audits": 3},
                {"month": "2025-02", "average_score": 87.1, "audits": 1}
            ],
            "common_gaps": [
                {"gap": "Training record completeness", "frequency": 8, "average_impact": "high"},
                {"gap": "Vendor risk assessment updates", "frequency": 6, "average_impact": "medium"},
                {"gap": "Documentation version control", "frequency": 5, "average_impact": "low"},
                {"gap": "Asset inventory accuracy", "frequency": 4, "average_impact": "medium"}
            ],
            "team_performance": {
                "average_milestone_completion": 0.87,
                "on_time_delivery_rate": 0.83,
                "team_utilization": 0.76,
                "collaboration_score": 0.91
            }
        }
        
        logger.info("Retrieved audit readiness analytics")
        return stats
    
    except Exception as e:
        logger.error(f"Error getting audit readiness analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@router.get("/{audit_id}/enhanced-forecast")
async def get_enhanced_readiness_forecast(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get enhanced AI-powered readiness forecast with confidence intervals"""
    try:
        # Get audit details (in production, fetch from database)
        current_readiness = 87.3
        framework = "ISO 27001:2022"
        days_remaining = 45
        
        # Generate enhanced forecast using AI engine
        forecast = enhanced_ai_engine.generate_risk_weighted_forecast(
            audit_id=audit_id,
            current_readiness=current_readiness,
            framework=framework,
            days_remaining=days_remaining
        )
        
        logger.info(f"Generated enhanced forecast for audit {audit_id}")
        return forecast
    
    except Exception as e:
        logger.error(f"Error generating enhanced forecast: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate enhanced forecast")

@router.get("/{audit_id}/temporal-analysis")
async def get_temporal_trend_analysis(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive temporal trend analysis for audit readiness"""
    try:
        # Mock historical data (in production, fetch from database)
        current_time = datetime.utcnow()
        historical_data = []
        
        # Generate 30 days of mock historical data
        for i in range(30):
            date = current_time - timedelta(days=29-i)
            base_score = 70 + (i * 0.8) + (i % 7) * 2  # Gradual improvement with weekly cycles
            
            historical_data.append(TemporalDataPoint(
                timestamp=date,
                readiness_score=min(95, base_score),
                confidence=0.8 + (i * 0.005),
                contributing_factors={
                    "documentation_completeness": min(95, 60 + i * 1.2),
                    "team_preparedness": min(90, 65 + i * 0.9),
                    "evidence_quality": min(88, 55 + i * 1.1),
                    "process_maturity": min(92, 50 + i * 1.4)
                },
                milestone_completion=min(100, 30 + i * 2.3),
                evidence_quality=min(90, 50 + i * 1.3)
            ))
        
        # Perform temporal analysis
        analysis = enhanced_ai_engine.analyze_temporal_trends(
            audit_id=audit_id,
            historical_data=historical_data
        )
        
        logger.info(f"Generated temporal analysis for audit {audit_id}")
        return analysis
    
    except Exception as e:
        logger.error(f"Error generating temporal analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate temporal analysis")

@router.post("/{audit_id}/intelligent-recommendations")
async def get_intelligent_remediation_recommendations(
    audit_id: str,
    organizational_context: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get AI-powered contextual remediation recommendations"""
    try:
        # Mock identified gaps (in production, fetch from gap analysis)
        identified_gaps = [
            {
                "gap_id": "gap_001",
                "title": "Training Record Completeness",
                "description": "Employee security awareness training records are incomplete for 25% of staff",
                "type": "training",
                "severity": "critical",
                "complexity": "organization_wide",
                "controls": ["ISO27001_A.7.2.2", "ISO27001_A.6.1.1"],
                "dependencies": [],
                "assigned_team": ["HR", "Security Team"]
            },
            {
                "gap_id": "gap_002", 
                "title": "Vendor Risk Assessment Updates",
                "description": "Critical vendor risk assessments are outdated and require comprehensive review",
                "type": "process",
                "severity": "high",
                "complexity": "cross_functional",
                "controls": ["ISO27001_A.15.1.1", "ISO27001_A.15.2.1"],
                "dependencies": ["vendor_contact"],
                "assigned_team": ["Procurement", "Risk Management"]
            },
            {
                "gap_id": "gap_003",
                "title": "Documentation Version Control",
                "description": "Policy and procedure documents lack proper version control and approval workflows",
                "type": "documentation",
                "severity": "medium",
                "complexity": "departmental",
                "controls": ["ISO27001_A.5.1.1", "ISO27001_A.5.1.2"],
                "dependencies": [],
                "assigned_team": ["Compliance", "Quality Assurance"]
            }
        ]
        
        # Get framework from audit (mock)
        framework = "ISO 27001:2022"
        
        # Mock timeline constraints
        timeline_constraints = {
            "audit_date": datetime.utcnow() + timedelta(days=45),
            "aggressive": organizational_context.get("aggressive_timeline", False),
            "critical_milestones": 3
        }
        
        # Generate intelligent recommendations
        recommendations = dynamic_remediation_engine.generate_contextual_recommendations(
            audit_id=audit_id,
            framework=framework,
            identified_gaps=identified_gaps,
            organizational_context=organizational_context,
            timeline_constraints=timeline_constraints
        )
        
        logger.info(f"Generated intelligent recommendations for audit {audit_id}")
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating intelligent recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate intelligent recommendations")

@router.get("/{audit_id}/confidence-analysis")
async def get_confidence_interval_analysis(
    audit_id: str,
    confidence_level: float = 0.95,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed confidence interval analysis for readiness predictions"""
    try:
        # Mock current readiness data
        base_score = 87.3
        historical_variance = 0.08  # 8% historical variance
        sample_size = 45
        
        # Calculate enhanced confidence intervals
        confidence_interval = enhanced_ai_engine.calculate_enhanced_confidence_intervals(
            base_score=base_score,
            historical_variance=historical_variance,
            sample_size=sample_size,
            confidence_level=confidence_level
        )
        
        # Additional analysis
        analysis_results = {
            "audit_id": audit_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "base_readiness_score": base_score,
            "confidence_interval": {
                "lower_bound": confidence_interval.lower_bound,
                "upper_bound": confidence_interval.upper_bound,
                "confidence_level": confidence_interval.confidence_level,
                "method": confidence_interval.method,
                "sample_size": confidence_interval.sample_size
            },
            "statistical_metadata": {
                "historical_variance": historical_variance,
                "margin_of_error": (confidence_interval.upper_bound - confidence_interval.lower_bound) / 2,
                "precision_level": "high" if confidence_interval.upper_bound - confidence_interval.lower_bound < 10 else "moderate",
                "reliability_score": min(100, sample_size * 2),  # Simple reliability metric
            },
            "interpretation": {
                "confidence_description": f"We are {int(confidence_level * 100)}% confident that the true readiness score lies between {confidence_interval.lower_bound}% and {confidence_interval.upper_bound}%",
                "precision_assessment": f"The prediction has a margin of error of ±{round((confidence_interval.upper_bound - confidence_interval.lower_bound) / 2, 1)} percentage points",
                "recommendation": "High confidence interval" if confidence_interval.upper_bound - confidence_interval.lower_bound < 8 else "Consider collecting more data points for improved precision"
            }
        }
        
        logger.info(f"Generated confidence interval analysis for audit {audit_id}")
        return analysis_results
    
    except Exception as e:
        logger.error(f"Error generating confidence interval analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate confidence interval analysis")

# =====================================
# PHASE 3: GAP ANALYSIS ENDPOINTS
# =====================================

@router.get("/{audit_id}/gap-analysis")
async def get_gap_analysis(
    audit_id: str,
    framework: Optional[str] = None,
    severity_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive gap analysis for audit readiness"""
    try:
        # Mock gap analysis data - in production, this would query the database
        current_time = datetime.utcnow()
        
        # Generate mock evidence gaps
        mock_gaps = [
            EvidenceGap(
                gap_id="GAP-A1B2C3D4",
                control_id="GV.OC-01",
                control_title="Organizational Cybersecurity Strategy",
                framework="NIST CSF 2.0",
                severity="critical",
                gap_description="Missing comprehensive cybersecurity strategy document with board approval",
                evidence_required=["Strategy Document", "Board Resolution", "Implementation Plan"],
                evidence_provided=["Draft Strategy"],
                evidence_sufficiency_score=0.33,
                remediation_timeline=30,
                remediation_effort="high",
                business_impact="critical",
                current_maturity_level=2,
                target_maturity_level=4,
                assigned_to=["user-123", "user-456"],
                milestone_dependency="milestone-001"
            ),
            EvidenceGap(
                gap_id="GAP-E5F6G7H8",
                control_id="PR.AA-01",
                control_title="Identity and Access Management",
                framework="NIST CSF 2.0",
                severity="high",
                gap_description="Incomplete privileged access management controls documentation",
                evidence_required=["PAM Policy", "Access Reviews", "Role Matrix"],
                evidence_provided=["PAM Policy", "Partial Access Reviews"],
                evidence_sufficiency_score=0.67,
                remediation_timeline=21,
                remediation_effort="medium",
                business_impact="high",
                current_maturity_level=3,
                target_maturity_level=4,
                assigned_to=["user-789"],
                milestone_dependency="milestone-002"
            ),
            EvidenceGap(
                gap_id="GAP-I9J0K1L2",
                control_id="PR.DS-01",
                control_title="Data-at-Rest Protection",
                framework="NIST CSF 2.0",
                severity="medium",
                gap_description="Data classification and encryption standards need updates",
                evidence_required=["Data Classification Policy", "Encryption Standards", "Implementation Guide"],
                evidence_provided=["Data Classification Policy", "Encryption Standards"],
                evidence_sufficiency_score=0.75,
                remediation_timeline=14,
                remediation_effort="low",
                business_impact="medium",
                current_maturity_level=3,
                target_maturity_level=4,
                assigned_to=["user-101"],
                milestone_dependency=None
            ),
            EvidenceGap(
                gap_id="GAP-M3N4O5P6",
                control_id="RS.RP-01",
                control_title="Response Planning",
                framework="NIST CSF 2.0",
                severity="high",
                gap_description="Incident response plan lacks recent tabletop exercise documentation",
                evidence_required=["IR Plan", "Tabletop Exercise Reports", "Training Records"],
                evidence_provided=["IR Plan"],
                evidence_sufficiency_score=0.40,
                remediation_timeline=45,
                remediation_effort="medium",
                business_impact="high",
                current_maturity_level=2,
                target_maturity_level=4,
                assigned_to=["user-202", "user-303"],
                milestone_dependency="milestone-003"
            ),
            EvidenceGap(
                gap_id="GAP-Q7R8S9T0",
                control_id="DE.CM-01",
                control_title="Continuous Monitoring",
                framework="NIST CSF 2.0",
                severity="low",
                gap_description="Monitoring dashboards need minor configuration updates",
                evidence_required=["Monitoring Plan", "Dashboard Screenshots", "Alert Configurations"],
                evidence_provided=["Monitoring Plan", "Dashboard Screenshots", "Partial Alert Configs"],
                evidence_sufficiency_score=0.85,
                remediation_timeline=7,
                remediation_effort="low",
                business_impact="low",
                current_maturity_level=4,
                target_maturity_level=4,
                assigned_to=["user-404"],
                milestone_dependency=None
            )
        ]
        
        # Apply filters if provided
        if framework:
            mock_gaps = [gap for gap in mock_gaps if gap.framework == framework]
        if severity_filter:
            mock_gaps = [gap for gap in mock_gaps if gap.severity == severity_filter]
        
        # Calculate summary statistics
        total_gaps = len(mock_gaps)
        critical_gaps = len([g for g in mock_gaps if g.severity == "critical"])
        high_gaps = len([g for g in mock_gaps if g.severity == "high"])
        medium_gaps = len([g for g in mock_gaps if g.severity == "medium"])
        low_gaps = len([g for g in mock_gaps if g.severity == "low"])
        
        overall_coverage = sum(gap.evidence_sufficiency_score for gap in mock_gaps) / len(mock_gaps) if mock_gaps else 1.0
        evidence_completion = sum(len(gap.evidence_provided) / max(len(gap.evidence_required), 1) for gap in mock_gaps) / len(mock_gaps) if mock_gaps else 1.0
        total_remediation_days = max([gap.remediation_timeline for gap in mock_gaps]) if mock_gaps else 0
        
        framework_dist = {}
        for gap in mock_gaps:
            framework_dist[gap.framework] = framework_dist.get(gap.framework, 0) + 1
        
        maturity_assessment = {
            "average_current_maturity": sum(gap.current_maturity_level for gap in mock_gaps) / len(mock_gaps) if mock_gaps else 4.0,
            "average_target_maturity": sum(gap.target_maturity_level for gap in mock_gaps) / len(mock_gaps) if mock_gaps else 4.0,
            "maturity_gap": sum(gap.target_maturity_level - gap.current_maturity_level for gap in mock_gaps) / len(mock_gaps) if mock_gaps else 0.0
        }
        
        summary = GapAnalysisSummary(
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_gaps,
            medium_priority_gaps=medium_gaps,
            low_priority_gaps=low_gaps,
            overall_coverage_score=overall_coverage,
            evidence_completion_rate=evidence_completion,
            estimated_remediation_days=total_remediation_days,
            framework_distribution=framework_dist,
            maturity_assessment=maturity_assessment
        )
        
        return {
            "audit_id": audit_id,
            "analysis_timestamp": current_time.isoformat(),
            "summary": summary,
            "gaps": mock_gaps,
            "ai_insights": {
                "priority_recommendation": "Focus on critical gaps first - cybersecurity strategy document is blocking multiple other controls",
                "efficiency_tip": "Consider grouping similar evidence collection activities to reduce overall remediation time",
                "risk_assessment": f"Current gap profile indicates {critical_gaps + high_gaps} high-impact vulnerabilities requiring immediate attention"
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving gap analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve gap analysis")

@router.get("/{audit_id}/control-evidence-mapping")
async def get_control_evidence_mapping(
    audit_id: str,
    framework: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed control-to-evidence mapping with real-time scoring"""
    try:
        # Mock control evidence mapping - in production, this would query actual evidence files
        mock_mappings = [
            ControlEvidenceMapping(
                control_id="GV.OC-01",
                control_title="Organizational Cybersecurity Strategy",
                framework="NIST CSF 2.0",
                evidence_requirements=[
                    "Cybersecurity Strategy Document",
                    "Board Approval/Resolution",
                    "Annual Review Documentation",
                    "Implementation Roadmap"
                ],
                evidence_artifacts=[
                    {"id": "evidence-001", "name": "Draft_Strategy_2024.pdf", "status": "draft", "upload_date": "2024-01-15"},
                    {"id": "evidence-002", "name": "Strategy_Implementation_Plan.docx", "status": "pending_review", "upload_date": "2024-01-20"}
                ],
                coverage_percentage=45.0,
                gap_status="major_gap",
                last_reviewed=datetime.utcnow() - timedelta(days=5),
                reviewer_notes="Missing board approval documentation and final strategy version"
            ),
            ControlEvidenceMapping(
                control_id="PR.AA-01",
                control_title="Identity and Access Management",
                framework="NIST CSF 2.0",
                evidence_requirements=[
                    "Access Management Policy",
                    "Role-Based Access Control Matrix",
                    "Quarterly Access Reviews",
                    "Privileged Access Management Procedures"
                ],
                evidence_artifacts=[
                    {"id": "evidence-003", "name": "Access_Management_Policy_v3.1.pdf", "status": "approved", "upload_date": "2024-01-10"},
                    {"id": "evidence-004", "name": "RBAC_Matrix_Q1_2024.xlsx", "status": "approved", "upload_date": "2024-01-25"},
                    {"id": "evidence-005", "name": "Q4_2023_Access_Review.pdf", "status": "pending_update", "upload_date": "2024-01-05"}
                ],
                coverage_percentage=75.0,
                gap_status="minor_gap",
                last_reviewed=datetime.utcnow() - timedelta(days=2),
                reviewer_notes="Need Q1 2024 access review and updated PAM procedures"
            ),
            ControlEvidenceMapping(
                control_id="PR.DS-01",
                control_title="Data-at-Rest Protection",
                framework="NIST CSF 2.0",
                evidence_requirements=[
                    "Data Classification Policy",
                    "Encryption Standards",
                    "Key Management Procedures",
                    "Data Loss Prevention Configuration"
                ],
                evidence_artifacts=[
                    {"id": "evidence-006", "name": "Data_Classification_Policy_v2.0.pdf", "status": "approved", "upload_date": "2024-01-08"},
                    {"id": "evidence-007", "name": "Encryption_Standards_2024.pdf", "status": "approved", "upload_date": "2024-01-12"},
                    {"id": "evidence-008", "name": "Key_Management_SOP.docx", "status": "approved", "upload_date": "2024-01-18"},
                    {"id": "evidence-009", "name": "DLP_Config_Screenshots.pdf", "status": "approved", "upload_date": "2024-01-22"}
                ],
                coverage_percentage=95.0,
                gap_status="no_gap",
                last_reviewed=datetime.utcnow() - timedelta(days=1),
                reviewer_notes="All evidence complete and up-to-date"
            ),
            ControlEvidenceMapping(
                control_id="RS.RP-01",
                control_title="Response Planning",
                framework="NIST CSF 2.0",
                evidence_requirements=[
                    "Incident Response Plan",
                    "Tabletop Exercise Reports",
                    "Response Team Training Records",
                    "Communication Templates"
                ],
                evidence_artifacts=[
                    {"id": "evidence-010", "name": "Incident_Response_Plan_v4.2.pdf", "status": "approved", "upload_date": "2024-01-14"},
                    {"id": "evidence-011", "name": "Communication_Templates.docx", "status": "approved", "upload_date": "2024-01-16"}
                ],
                coverage_percentage=50.0,
                gap_status="major_gap",
                last_reviewed=datetime.utcnow() - timedelta(days=7),
                reviewer_notes="Missing recent tabletop exercise documentation and training records"
            ),
            ControlEvidenceMapping(
                control_id="DE.CM-01",
                control_title="Continuous Monitoring",
                framework="NIST CSF 2.0",
                evidence_requirements=[
                    "Monitoring Strategy",
                    "SIEM Configuration Documentation",
                    "Alert Tuning Reports",
                    "Monitoring Dashboard Screenshots"
                ],
                evidence_artifacts=[
                    {"id": "evidence-012", "name": "Monitoring_Strategy_2024.pdf", "status": "approved", "upload_date": "2024-01-11"},
                    {"id": "evidence-013", "name": "SIEM_Config_Guide.pdf", "status": "approved", "upload_date": "2024-01-13"},
                    {"id": "evidence-014", "name": "Alert_Tuning_Report_Q1.pdf", "status": "approved", "upload_date": "2024-01-17"},
                    {"id": "evidence-015", "name": "Monitoring_Dashboards_Jan2024.pdf", "status": "approved", "upload_date": "2024-01-19"}
                ],
                coverage_percentage=90.0,
                gap_status="minor_gap",
                last_reviewed=datetime.utcnow() - timedelta(days=3),
                reviewer_notes="Minor updates needed for new monitoring tools integration"
            )
        ]
        
        # Apply framework filter if provided
        if framework:
            mock_mappings = [mapping for mapping in mock_mappings if mapping.framework == framework]
        
        # Calculate overall statistics
        total_controls = len(mock_mappings)
        average_coverage = sum(mapping.coverage_percentage for mapping in mock_mappings) / total_controls if total_controls > 0 else 0.0
        
        gap_distribution = {
            "no_gap": len([m for m in mock_mappings if m.gap_status == "no_gap"]),
            "minor_gap": len([m for m in mock_mappings if m.gap_status == "minor_gap"]),
            "major_gap": len([m for m in mock_mappings if m.gap_status == "major_gap"]),
            "critical_gap": len([m for m in mock_mappings if m.gap_status == "critical_gap"])
        }
        
        return {
            "audit_id": audit_id,
            "mapping_timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_controls_analyzed": total_controls,
                "average_coverage_percentage": round(average_coverage, 1),
                "gap_distribution": gap_distribution,
                "evidence_artifacts_total": sum(len(m.evidence_artifacts) for m in mock_mappings)
            },
            "control_mappings": mock_mappings,
            "ai_insights": {
                "coverage_trend": "improving" if average_coverage > 70 else "needs_attention",
                "priority_controls": [m.control_id for m in mock_mappings if m.gap_status in ["major_gap", "critical_gap"]],
                "recommendation": f"Focus on {gap_distribution['major_gap'] + gap_distribution['critical_gap']} controls with significant gaps"
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving control evidence mapping: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve control evidence mapping")

@router.get("/{audit_id}/enhanced-dashboard-metrics")
async def get_enhanced_dashboard_metrics(
    audit_id: str,
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get enhanced dashboard intelligence with predictive analytics and trends"""
    try:
        current_time = datetime.utcnow()
        
        # Generate readiness trends over time
        readiness_trends = []
        for i in range(timeframe_days):
            date = current_time - timedelta(days=timeframe_days - i)
            # Simulate readiness progression with some variance
            base_score = 65 + (i * 0.8) + (i % 7) * 2  # Gradual improvement with weekly cycles
            trend_point = {
                "date": date.isoformat(),
                "readiness_score": min(95, max(50, base_score + (i % 3 - 1) * 3)),  # Add some noise
                "critical_gaps": max(0, 8 - (i // 5)),  # Decreasing critical gaps
                "evidence_completion": min(100, 40 + (i * 1.2)),
                "milestone_completion": min(100, 30 + (i * 1.5))
            }
            readiness_trends.append(trend_point)
        
        # Predictive forecasting using enhanced AI
        try:
            # Prepare historical data for prediction
            historical_data = [
                TemporalDataPoint(
                    timestamp=datetime.fromisoformat(point["date"]),
                    readiness_score=point["readiness_score"],
                    confidence=0.85,  # Default confidence
                    contributing_factors={
                        "evidence_completion": point["evidence_completion"],
                        "critical_gaps": point["critical_gaps"]
                    },
                    milestone_completion=point["milestone_completion"],
                    evidence_quality=point["evidence_completion"] / 100.0  # Convert to 0-1 scale
                ) for point in readiness_trends[-14:]  # Use last 14 days for prediction
            ]
            
            # Get enhanced forecast
            forecast = enhanced_ai_engine.generate_enhanced_readiness_forecast(
                audit_id=audit_id,
                historical_data=historical_data,
                framework="NIST CSF 2.0",
                target_date=current_time + timedelta(days=30)
            )
            
            predictive_forecasts = {
                "30_day_projection": {
                    "optimistic_score": forecast.scenarios["optimistic"]["final_score"],
                    "realistic_score": forecast.scenarios["realistic"]["final_score"],
                    "pessimistic_score": forecast.scenarios["pessimistic"]["final_score"],
                    "confidence_interval": f"{forecast.confidence_intervals.lower_bound:.1f}% - {forecast.confidence_intervals.upper_bound:.1f}%",
                    "success_probability": forecast.monte_carlo_results.success_probability
                },
                "milestone_predictions": [
                    {
                        "milestone": "Evidence Collection Complete",
                        "predicted_date": (current_time + timedelta(days=18)).isoformat(),
                        "probability": 0.85
                    },
                    {
                        "milestone": "Internal Review Complete",
                        "predicted_date": (current_time + timedelta(days=25)).isoformat(),
                        "probability": 0.78
                    },
                    {
                        "milestone": "Audit Ready",
                        "predicted_date": (current_time + timedelta(days=30)).isoformat(),
                        "probability": forecast.monte_carlo_results.success_probability
                    }
                ]
            }
            
        except Exception as e:
            logger.warning(f"Enhanced forecast failed, using fallback: {str(e)}")
            predictive_forecasts = {
                "30_day_projection": {
                    "optimistic_score": 92.0,
                    "realistic_score": 87.5,
                    "pessimistic_score": 82.0,
                    "confidence_interval": "85.2% - 89.8%",
                    "success_probability": 0.73
                },
                "milestone_predictions": [
                    {
                        "milestone": "Evidence Collection Complete",
                        "predicted_date": (current_time + timedelta(days=18)).isoformat(),
                        "probability": 0.85
                    },
                    {
                        "milestone": "Internal Review Complete",
                        "predicted_date": (current_time + timedelta(days=25)).isoformat(),
                        "probability": 0.78
                    },
                    {
                        "milestone": "Audit Ready",
                        "predicted_date": (current_time + timedelta(days=30)).isoformat(),
                        "probability": 0.73
                    }
                ]
            }
        
        # Risk indicators
        risk_indicators = {
            "velocity_risk": "medium",  # Based on current progress rate
            "resource_risk": "low",     # Based on team capacity
            "complexity_risk": "high",  # Based on remaining gaps
            "timeline_risk": "medium",  # Based on remaining time
            "risk_score": 2.5,  # 1-5 scale
            "key_risks": [
                "Critical gaps in cybersecurity strategy documentation may delay final approval",
                "Incident response tabletop exercise scheduling depends on external facilitator availability",
                "Q1 access reviews pending completion by security team"
            ]
        }
        
        # AI-generated improvement recommendations
        improvement_recommendations = [
            "Prioritize completion of cybersecurity strategy document - this is blocking 3 other controls",
            "Schedule incident response tabletop exercise for next week to meet timeline requirements",
            "Implement parallel evidence collection for PR.AA-01 and PR.DS-01 controls to optimize resource usage",
            "Consider extending timeline by 5 days to ensure thorough evidence review and quality assurance"
        ]
        
        # Benchmark comparisons (simulated industry benchmarks)
        benchmark_comparisons = {
            "industry_average_readiness": 78.5,
            "peer_organizations_average": 82.1,
            "best_in_class_score": 94.2,
            "percentile_ranking": 72.0  # 72nd percentile
        }
        
        enhanced_metrics = EnhancedDashboardMetrics(
            readiness_trends=readiness_trends,
            predictive_forecasts=predictive_forecasts,
            risk_indicators=risk_indicators,
            improvement_recommendations=improvement_recommendations,
            benchmark_comparisons=benchmark_comparisons
        )
        
        return {
            "audit_id": audit_id,
            "metrics_timestamp": current_time.isoformat(),
            "timeframe_days": timeframe_days,
            "enhanced_metrics": enhanced_metrics,
            "ai_summary": {
                "overall_trajectory": "positive_with_concerns",
                "key_insight": f"Readiness score improving at {((readiness_trends[-1]['readiness_score'] - readiness_trends[0]['readiness_score']) / timeframe_days):.1f} points per day, but critical gaps need immediate attention",
                "recommendation": "Focus next 7 days on critical gap remediation to maintain positive trajectory"
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving enhanced dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve enhanced dashboard metrics")

@router.post("/{audit_id}/update-gap")
async def update_evidence_gap(
    audit_id: str,
    gap_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update evidence gap status and details"""
    try:
        # In production, this would update the actual database record
        logger.info(f"Mock: Updated gap {gap_id} for audit {audit_id} with data: {update_data}")
        
        # Simulate successful update
        updated_gap = {
            "gap_id": gap_id,
            "audit_id": audit_id,
            "updated_fields": list(update_data.keys()),
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": current_user.id,
            "status": "updated"
        }
        
        return updated_gap
        
    except Exception as e:
        logger.error(f"Error updating evidence gap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update evidence gap")

@router.get("/{audit_id}/exportable-scorecard")
async def generate_exportable_scorecard(
    audit_id: str,
    format: str = "summary",  # "summary", "detailed", "executive"
    export_format: str = "json",  # "json", "pdf", "docx"
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Generate exportable AI-enhanced scorecard"""
    try:
        current_time = datetime.utcnow()
        
        # Get comprehensive audit data for scorecard
        scorecard_data = {
            "audit_id": audit_id,
            "generated_at": current_time.isoformat(),
            "generated_by": current_user.name,
            "format": format,
            "export_format": export_format,
            
            # Executive Summary
            "executive_summary": {
                "overall_readiness_score": 87.3,
                "audit_date": (current_time + timedelta(days=30)).isoformat(),
                "days_remaining": 30,
                "framework": "NIST CSF 2.0",
                "organization": "TechCorp Industries",  # In production, get from user context
                "audit_type": "External Certification Audit",
                "status": "On Track with Minor Concerns"
            },
            
            # Key Metrics
            "key_metrics": {
                "total_controls": 22,
                "controls_ready": 18,
                "controls_in_progress": 3,
                "controls_not_started": 1,
                "evidence_completion_rate": 82.4,
                "critical_gaps": 1,
                "high_priority_gaps": 2,
                "medium_priority_gaps": 3,
                "low_priority_gaps": 1
            },
            
            # AI Insights
            "ai_insights": {
                "readiness_trend": "Improving (3.2% increase over last 14 days)",
                "predicted_final_score": "89.2% (±2.1% confidence interval)",
                "success_probability": "87% chance of achieving target readiness",
                "key_risk_factors": [
                    "Cybersecurity strategy documentation pending board approval",
                    "Incident response tabletop exercise scheduled for week 3",
                    "Privileged access management controls require evidence updates"
                ],
                "recommendations": [
                    "Escalate strategy document approval to maintain timeline",
                    "Prepare backup tabletop exercise facilitator",
                    "Allocate additional resources to access management documentation"
                ]
            },
            
            # Framework Breakdown
            "framework_analysis": {
                "NIST CSF 2.0": {
                    "govern": {"score": 85.2, "gaps": 1, "status": "good"},
                    "identify": {"score": 91.4, "gaps": 0, "status": "excellent"},
                    "protect": {"score": 88.7, "gaps": 2, "status": "good"},
                    "detect": {"score": 84.1, "gaps": 1, "status": "good"},
                    "respond": {"score": 79.3, "gaps": 2, "status": "needs_attention"},
                    "recover": {"score": 86.9, "gaps": 1, "status": "good"}
                }
            },
            
            # Timeline Analysis
            "timeline_analysis": {
                "milestones_completed": 8,
                "milestones_on_track": 4,
                "milestones_at_risk": 2,
                "critical_path_items": [
                    "Cybersecurity Strategy Approval (Due: 15 days)",
                    "Incident Response Exercise (Due: 21 days)",
                    "Final Evidence Review (Due: 28 days)"
                ],
                "buffer_time": "2 days available for contingency"
            }
        }
        
        # Add detailed information if requested
        if format == "detailed":
            scorecard_data["detailed_gap_analysis"] = {
                "critical_gaps": [
                    {
                        "gap_id": "GAP-A1B2C3D4",
                        "control": "GV.OC-01 - Organizational Cybersecurity Strategy",
                        "description": "Missing board approval for cybersecurity strategy",
                        "remediation_plan": "Schedule board meeting, prepare executive summary",
                        "timeline": "15 days",
                        "assigned_to": "CISO, Board Secretary"
                    }
                ],
                "control_status_detail": [
                    {
                        "control_id": "GV.OC-01",
                        "title": "Organizational Cybersecurity Strategy",
                        "evidence_required": 4,
                        "evidence_provided": 2,
                        "coverage": "50%",
                        "status": "In Progress",
                        "notes": "Draft strategy complete, awaiting board approval"
                    }
                    # Additional controls would be listed here
                ]
            }
        
        # Add executive-level insights if requested
        if format == "executive":
            scorecard_data["executive_insights"] = {
                "business_impact_assessment": "Low risk - audit preparation on track with manageable gaps",
                "resource_requirements": "Current resource allocation sufficient with minor adjustments needed",
                "compliance_outlook": "High confidence in successful audit completion",
                "strategic_recommendations": [
                    "Establish board governance review cycle for cybersecurity strategy updates",
                    "Implement quarterly incident response exercise program",
                    "Consider automation tools for access management compliance documentation"
                ],
                "next_review_date": (current_time + timedelta(days=7)).isoformat()
            }
        
        # In production, this could trigger PDF/DOCX generation for export formats
        if export_format in ["pdf", "docx"]:
            scorecard_data["export_info"] = {
                "status": "generated",
                "download_url": f"/api/audit-readiness/{audit_id}/download-scorecard/{format}",
                "file_size": "2.4 MB",
                "expires_at": (current_time + timedelta(hours=24)).isoformat()
            }
        
        return scorecard_data
        
    except Exception as e:
        logger.error(f"Error generating exportable scorecard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate exportable scorecard")

# =====================================
# PHASE 4A: MILESTONE PERFORMANCE INTELLIGENCE ENDPOINTS
# =====================================

@router.get("/{audit_id}/gap-closure-velocity")
async def get_gap_closure_velocity(
    audit_id: str,
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get gap closure velocity analytics and performance metrics"""
    try:
        current_time = datetime.utcnow()
        
        # Mock gap closure velocity data - in production, fetch from database
        mock_velocity_data = [
            GapClosureVelocity(
                audit_id=audit_id,
                gap_id="GAP-A1B2C3D4",
                closure_date=current_time - timedelta(days=5),
                days_to_closure=25,
                original_timeline=30,
                velocity_score=0.83,  # 25/30 = faster than planned
                complexity_factor="high",
                team_size=3,
                resource_utilization=0.85,
                blockers_encountered=["Board approval delay", "External vendor coordination"],
                acceleration_factors=["Dedicated task force", "Executive priority", "Parallel processing"]
            ),
            GapClosureVelocity(
                audit_id=audit_id,
                gap_id="GAP-E5F6G7H8",
                closure_date=current_time - timedelta(days=12),
                days_to_closure=18,
                original_timeline=21,
                velocity_score=0.86,  # 18/21 = ahead of schedule
                complexity_factor="medium",
                team_size=2,
                resource_utilization=0.90,
                blockers_encountered=["Initial access delays"],
                acceleration_factors=["Clear requirements", "Experienced team", "Good documentation"]
            ),
            GapClosureVelocity(
                audit_id=audit_id,
                gap_id="GAP-I9J0K1L2",
                closure_date=current_time - timedelta(days=20),
                days_to_closure=10,
                original_timeline=14,
                velocity_score=0.71,  # 10/14 = significantly ahead
                complexity_factor="low",
                team_size=1,
                resource_utilization=0.75,
                blockers_encountered=[],
                acceleration_factors=["Existing templates", "Quick approval process"]
            ),
            GapClosureVelocity(
                audit_id=audit_id,
                gap_id="GAP-M3N4O5P6",
                closure_date=current_time - timedelta(days=8),
                days_to_closure=35,
                original_timeline=45,
                velocity_score=0.78,  # 35/45 = ahead of schedule
                complexity_factor="very_high",
                team_size=5,
                resource_utilization=0.95,
                blockers_encountered=["External facilitator availability", "Calendar coordination", "Budget approval"],
                acceleration_factors=["Cross-functional team", "Management support", "Clear priorities"]
            )
        ]
        
        # Calculate analytics
        total_gaps_closed = len(mock_velocity_data)
        average_velocity_score = sum(gv.velocity_score for gv in mock_velocity_data) / total_gaps_closed
        average_days_saved = sum(gv.original_timeline - gv.days_to_closure for gv in mock_velocity_data) / total_gaps_closed
        
        # Complexity distribution
        complexity_distribution = {}
        for gv in mock_velocity_data:
            complexity_distribution[gv.complexity_factor] = complexity_distribution.get(gv.complexity_factor, 0) + 1
        
        # Team performance insights
        team_performance = {
            "average_team_size": sum(gv.team_size for gv in mock_velocity_data) / total_gaps_closed,
            "average_resource_utilization": sum(gv.resource_utilization for gv in mock_velocity_data) / total_gaps_closed,
            "teams_above_90_utilization": len([gv for gv in mock_velocity_data if gv.resource_utilization > 0.9]),
            "high_velocity_teams": len([gv for gv in mock_velocity_data if gv.velocity_score < 0.8])  # Lower score = faster
        }
        
        # Trend analysis over time
        velocity_trends = []
        weekly_data = {}
        for gv in mock_velocity_data:
            week_key = gv.closure_date.strftime("%Y-W%U")
            if week_key not in weekly_data:
                weekly_data[week_key] = []
            weekly_data[week_key].append(gv.velocity_score)
        
        for week, scores in weekly_data.items():
            velocity_trends.append({
                "week": week,
                "average_velocity": sum(scores) / len(scores),
                "gaps_closed": len(scores),
                "performance_rating": "excellent" if sum(scores) / len(scores) < 0.8 else "good" if sum(scores) / len(scores) < 0.9 else "average"
            })
        
        return {
            "audit_id": audit_id,
            "analysis_timestamp": current_time.isoformat(),
            "timeframe_days": timeframe_days,
            "summary_metrics": {
                "total_gaps_closed": total_gaps_closed,
                "average_velocity_score": round(average_velocity_score, 3),
                "average_days_saved": round(average_days_saved, 1),
                "velocity_performance": "excellent" if average_velocity_score < 0.8 else "good" if average_velocity_score < 0.9 else "needs_improvement",
                "total_time_saved": sum(gv.original_timeline - gv.days_to_closure for gv in mock_velocity_data)
            },
            "complexity_analysis": {
                "distribution": complexity_distribution,
                "high_complexity_velocity": round(sum(gv.velocity_score for gv in mock_velocity_data if gv.complexity_factor in ["high", "very_high"]) / max(len([gv for gv in mock_velocity_data if gv.complexity_factor in ["high", "very_high"]]), 1), 3),
                "low_complexity_velocity": round(sum(gv.velocity_score for gv in mock_velocity_data if gv.complexity_factor in ["low", "medium"]) / max(len([gv for gv in mock_velocity_data if gv.complexity_factor in ["low", "medium"]]), 1), 3)
            },
            "team_performance": team_performance,
            "velocity_trends": velocity_trends,
            "gap_closure_details": mock_velocity_data,
            "ai_insights": {
                "key_finding": f"Gap closure velocity averaging {average_velocity_score:.1%}, saving {average_days_saved:.1f} days per gap on average",
                "performance_drivers": [
                    "Cross-functional teams demonstrate 15% better velocity than single-department teams",
                    "Clear requirements and existing templates accelerate closure by 25%",
                    "Executive sponsorship reduces blockers by 40%"
                ],
                "recommendations": [
                    "Replicate high-velocity team structures for remaining gaps",
                    "Create template library based on successful closure patterns",
                    "Implement early blocker identification process"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving gap closure velocity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve gap closure velocity")

@router.get("/{audit_id}/timeline-risk-forecast")
async def get_timeline_risk_forecast(
    audit_id: str,
    forecast_horizon_days: int = 45,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get timeline risk forecasting with mitigation strategies"""
    try:
        current_time = datetime.utcnow()
        
        # Mock timeline risk factors - in production, analyze current project state
        mock_risk_factors = [
            TimelineRiskFactor(
                audit_id=audit_id,
                milestone_id="milestone-001",
                risk_type="dependency",
                risk_description="Board approval meeting scheduled during CEO travel period",
                probability=0.75,
                impact_score=0.85,
                risk_score=0.64,  # 0.75 * 0.85
                timeline_impact_days=7,
                mitigation_strategies=[
                    "Schedule emergency board meeting via video conference",
                    "Delegate approval authority to COO",
                    "Prepare comprehensive pre-read materials"
                ],
                current_status="identified",
                owner="user-123"
            ),
            TimelineRiskFactor(
                audit_id=audit_id,
                milestone_id="milestone-002",
                risk_type="resource",
                risk_description="Key security engineer on planned vacation during critical phase",
                probability=0.95,
                impact_score=0.60,
                risk_score=0.57,  # 0.95 * 0.60
                timeline_impact_days=5,
                mitigation_strategies=[
                    "Cross-train backup security engineer",
                    "Document all critical procedures",
                    "Adjust timeline to accommodate vacation"
                ],
                current_status="mitigating",
                owner="user-456"
            ),
            TimelineRiskFactor(
                audit_id=audit_id,
                milestone_id="milestone-003",
                risk_type="external",
                risk_description="Third-party security assessment vendor may have scheduling conflicts",
                probability=0.40,
                impact_score=0.90,
                risk_score=0.36,  # 0.40 * 0.90
                timeline_impact_days=14,
                mitigation_strategies=[
                    "Identify backup assessment vendors",
                    "Negotiate priority scheduling agreement",
                    "Consider in-house assessment capability"
                ],
                current_status="identified",
                owner="user-789"
            ),
            TimelineRiskFactor(
                audit_id=audit_id,
                risk_type="complexity",
                risk_description="Multi-framework compliance mapping more complex than initially estimated",
                probability=0.65,
                impact_score=0.70,
                risk_score=0.46,  # 0.65 * 0.70
                timeline_impact_days=10,
                mitigation_strategies=[
                    "Allocate additional analysis resources",
                    "Use automated mapping tools",
                    "Engage external compliance consultant"
                ],
                current_status="identified",
                owner="user-101"
            ),
            TimelineRiskFactor(
                audit_id=audit_id,
                risk_type="technical",
                risk_description="Legacy system documentation extraction challenges",
                probability=0.55,
                impact_score=0.50,
                risk_score=0.28,  # 0.55 * 0.50
                timeline_impact_days=3,
                mitigation_strategies=[
                    "Engage original system developers",
                    "Use alternative documentation sources",
                    "Accept higher-level documentation if detailed unavailable"
                ],
                current_status="mitigating",
                owner="user-202"
            )
        ]
        
        # Calculate forecast metrics
        total_risk_exposure = sum(rf.timeline_impact_days * rf.probability for rf in mock_risk_factors)
        high_probability_risks = [rf for rf in mock_risk_factors if rf.probability > 0.7]
        high_impact_risks = [rf for rf in mock_risk_factors if rf.impact_score > 0.8]
        critical_risks = [rf for rf in mock_risk_factors if rf.risk_score > 0.5]
        
        # Risk category analysis
        risk_by_category = {}
        impact_by_category = {}
        for rf in mock_risk_factors:
            risk_by_category[rf.risk_type] = risk_by_category.get(rf.risk_type, 0) + 1
            impact_by_category[rf.risk_type] = impact_by_category.get(rf.risk_type, 0) + rf.timeline_impact_days
        
        # Timeline scenarios
        baseline_timeline = 45  # Original timeline
        optimistic_scenario = baseline_timeline + min(3, int(total_risk_exposure * 0.2))
        realistic_scenario = baseline_timeline + int(total_risk_exposure * 0.6)
        pessimistic_scenario = baseline_timeline + int(total_risk_exposure * 1.0)
        
        # Monte Carlo simulation (simplified)
        simulation_results = []
        for i in range(100):
            scenario_impact = 0
            for rf in mock_risk_factors:
                # Simple Monte Carlo: random probability check
                import random
                if random.random() < rf.probability:
                    scenario_impact += rf.timeline_impact_days * random.uniform(0.5, 1.0)
            simulation_results.append(baseline_timeline + scenario_impact)
        
        monte_carlo_stats = {
            "mean_timeline": sum(simulation_results) / len(simulation_results),
            "median_timeline": sorted(simulation_results)[len(simulation_results) // 2],
            "p90_timeline": sorted(simulation_results)[int(len(simulation_results) * 0.9)],
            "probability_on_time": len([r for r in simulation_results if r <= baseline_timeline]) / len(simulation_results),
            "probability_within_buffer": len([r for r in simulation_results if r <= baseline_timeline + 7]) / len(simulation_results)
        }
        
        return {
            "audit_id": audit_id,
            "forecast_timestamp": current_time.isoformat(),
            "forecast_horizon_days": forecast_horizon_days,
            "baseline_timeline": baseline_timeline,
            "risk_summary": {
                "total_risk_factors": len(mock_risk_factors),
                "critical_risks": len(critical_risks),
                "high_probability_risks": len(high_probability_risks),
                "high_impact_risks": len(high_impact_risks),
                "total_risk_exposure_days": round(total_risk_exposure, 1),
                "risk_mitigation_coverage": len([rf for rf in mock_risk_factors if rf.current_status == "mitigating"]) / len(mock_risk_factors),
                "overall_risk_level": "high" if len(critical_risks) >= 3 else "medium" if len(critical_risks) >= 1 else "low",
                "probability_of_delay": max(0.1, min(0.9, total_risk_exposure / (baseline_timeline * 2))),
                "expected_delay_days": int(total_risk_exposure * 0.6)
            },
            "scenario_analysis": {
                "optimistic": {
                    "timeline_days": optimistic_scenario,
                    "probability": 0.90,
                    "assumptions": "All mitigation strategies successful, no new risks emerge"
                },
                "realistic": {
                    "timeline_days": realistic_scenario,
                    "probability": 0.70,
                    "assumptions": "60% of identified risks materialize with average impact"
                },
                "pessimistic": {
                    "timeline_days": pessimistic_scenario,
                    "probability": 0.10,
                    "assumptions": "All identified risks materialize with maximum impact"
                }
            },
            "monte_carlo_simulation": {
                "iterations": 100,
                "success_probability": monte_carlo_stats["probability_on_time"],
                "confidence_interval": f"{monte_carlo_stats['probability_within_buffer']:.1%} probability within 7-day buffer",
                "risk_distribution": {
                    "mean_timeline": monte_carlo_stats["mean_timeline"],
                    "median_timeline": monte_carlo_stats["median_timeline"],
                    "p90_timeline": monte_carlo_stats["p90_timeline"]
                }
            },
            "risk_category_analysis": {
                "distribution": risk_by_category,
                "impact_by_category": impact_by_category,
                "highest_risk_category": max(risk_by_category.keys(), key=lambda k: impact_by_category[k])
            },
            "risk_factors": mock_risk_factors,
            "mitigation_priorities": [
                {
                    "risk_factor": rf.risk_description,
                    "risk_id": rf.risk_id,
                    "impact_score": rf.impact_score,
                    "probability": rf.probability,
                    "priority": "critical" if rf.risk_score > 0.5 else "high" if rf.risk_score > 0.3 else "medium",
                    "action_required": "immediate" if rf.current_status == "identified" and rf.risk_score > 0.5 else "within_week",
                    "owner": rf.owner
                } for rf in sorted(mock_risk_factors, key=lambda x: x.risk_score, reverse=True)
            ],
            "ai_insights": {
                "key_finding": f"Timeline at risk: {int(monte_carlo_stats['probability_on_time'] * 100)}% probability of meeting original timeline",
                "critical_risks": [rf.risk_description for rf in critical_risks],
                "recommendations": [
                    f"Focus immediate attention on {len(critical_risks)} critical risks",
                    "Implement daily risk monitoring for dependency and external risks",
                    f"Consider timeline buffer of {int(realistic_scenario - baseline_timeline)} days for realistic planning"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating timeline risk forecast: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate timeline risk forecast")

@router.get("/{audit_id}/resource-heatmap")
async def get_resource_heatmap(
    audit_id: str,
    include_forecast: bool = True,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get resource utilization heatmap with capacity analysis"""
    try:
        current_time = datetime.utcnow()
        
        # Mock resource heatmap data - in production, aggregate from project assignments
        mock_resource_data = [
            ResourceHeatMapData(
                team_member_id="user-123",
                name="Sarah Chen",
                role="CISO",
                current_workload=0.85,
                capacity=1.0,
                utilization_rate=0.85,
                assigned_gaps=["GAP-A1B2C3D4", "GAP-M3N4O5P6"],
                assigned_milestones=["milestone-001", "milestone-004"],
                expertise_areas=["Governance", "Strategy", "Risk Management"],
                availability_forecast={
                    "2025-01-15": 0.90,
                    "2025-01-22": 0.80,
                    "2025-01-29": 0.85,
                    "2025-02-05": 0.75  # Board meeting preparation
                },
                burnout_risk="medium",
                performance_trend="stable"
            ),
            ResourceHeatMapData(
                team_member_id="user-456",
                name="Michael Rodriguez",
                role="Security Engineer",
                current_workload=0.95,
                capacity=1.0,
                utilization_rate=0.95,
                assigned_gaps=["GAP-E5F6G7H8", "GAP-I9J0K1L2"],
                assigned_milestones=["milestone-002", "milestone-003"],
                expertise_areas=["Access Management", "Encryption", "Technical Controls"],
                availability_forecast={
                    "2025-01-15": 0.95,
                    "2025-01-22": 0.00,  # Planned vacation
                    "2025-01-29": 0.00,  # Planned vacation
                    "2025-02-05": 0.90
                },
                burnout_risk="high",
                performance_trend="declining"
            ),
            ResourceHeatMapData(
                team_member_id="user-789",
                name="Jennifer Park",
                role="Compliance Manager",
                current_workload=0.70,
                capacity=1.0,
                utilization_rate=0.70,
                assigned_gaps=["GAP-Q7R8S9T0"],
                assigned_milestones=["milestone-003"],
                expertise_areas=["Documentation", "Process Management", "Training"],
                availability_forecast={
                    "2025-01-15": 0.70,
                    "2025-01-22": 0.85,  # Can cover for Michael
                    "2025-01-29": 0.85,
                    "2025-02-05": 0.70
                },
                burnout_risk="low",
                performance_trend="improving"
            ),
            ResourceHeatMapData(
                team_member_id="user-101",
                name="David Kim",
                role="IT Auditor",
                current_workload=0.60,
                capacity=0.80,  # Part-time consultant
                utilization_rate=0.75,
                assigned_gaps=["GAP-M3N4O5P6"],
                assigned_milestones=["milestone-004"],
                expertise_areas=["Audit Procedures", "Evidence Collection", "Multi-framework"],
                availability_forecast={
                    "2025-01-15": 0.75,
                    "2025-01-22": 0.75,
                    "2025-01-29": 0.80,
                    "2025-02-05": 0.60  # Other client commitment
                },
                burnout_risk="low",
                performance_trend="stable"
            ),
            ResourceHeatMapData(
                team_member_id="user-202",
                name="Lisa Thompson",
                role="Technical Writer",
                current_workload=0.50,
                capacity=1.0,
                utilization_rate=0.50,
                assigned_gaps=["GAP-I9J0K1L2"],
                assigned_milestones=["milestone-001"],
                expertise_areas=["Documentation", "Process Documentation", "Training Materials"],
                availability_forecast={
                    "2025-01-15": 0.60,
                    "2025-01-22": 0.80,  # Document sprint
                    "2025-01-29": 0.70,
                    "2025-02-05": 0.50
                },
                burnout_risk="low",
                performance_trend="stable"
            )
        ]
        
        # Calculate analytics
        team_size = len(mock_resource_data)
        total_workload = sum(rd.current_workload for rd in mock_resource_data)
        total_capacity = sum(rd.capacity for rd in mock_resource_data)
        overall_utilization = total_workload / total_capacity if total_capacity > 0 else 0
        
        # Capacity analysis
        over_utilized = [rd for rd in mock_resource_data if rd.utilization_rate > 0.90]
        under_utilized = [rd for rd in mock_resource_data if rd.utilization_rate < 0.60]
        optimal_utilized = [rd for rd in mock_resource_data if 0.60 <= rd.utilization_rate <= 0.90]
        
        # Burnout risk analysis
        burnout_distribution = {}
        for rd in mock_resource_data:
            burnout_distribution[rd.burnout_risk] = burnout_distribution.get(rd.burnout_risk, 0) + 1
        
        # Role capacity mapping
        role_capacity = {}
        role_workload = {}
        for rd in mock_resource_data:
            if rd.role not in role_capacity:
                role_capacity[rd.role] = 0
                role_workload[rd.role] = 0
            role_capacity[rd.role] += rd.capacity
            role_workload[rd.role] += rd.current_workload
        
        # Weekly forecast analysis
        weekly_forecasts = {}
        forecast_dates = ["2025-01-15", "2025-01-22", "2025-01-29", "2025-02-05"]
        
        for date in forecast_dates:
            week_capacity = 0
            week_workload = 0
            for rd in mock_resource_data:
                available = rd.availability_forecast.get(date, rd.utilization_rate)
                week_capacity += rd.capacity
                week_workload += available * rd.capacity
            
            weekly_forecasts[date] = {
                "utilization_rate": week_workload / week_capacity if week_capacity > 0 else 0,
                "capacity_shortfall": max(0, week_workload - week_capacity),
                "available_capacity": max(0, week_capacity - week_workload)
            }
        
        # Critical periods identification
        critical_periods = []
        for date, forecast in weekly_forecasts.items():
            if forecast["utilization_rate"] > 0.95:
                critical_periods.append({
                    "week": date,
                    "issue": "over_capacity",
                    "severity": "high" if forecast["utilization_rate"] > 1.0 else "medium",
                    "recommendation": "Reassign non-critical tasks or extend timeline"
                })
            elif forecast["utilization_rate"] < 0.50:
                critical_periods.append({
                    "week": date,
                    "issue": "under_utilized",
                    "severity": "low",
                    "recommendation": "Accelerate timeline or assign additional tasks"
                })
        
        return {
            "audit_id": audit_id,
            "analysis_timestamp": current_time.isoformat(),
            "team_overview": {
                "team_size": team_size,
                "total_capacity": round(total_capacity, 2),
                "total_workload": round(total_workload, 2),
                "overall_utilization": round(overall_utilization, 3),
                "capacity_status": "optimal" if 0.70 <= overall_utilization <= 0.85 else "over_capacity" if overall_utilization > 0.85 else "under_utilized"
            },
            "capacity_analysis": {
                "over_utilized_count": len(over_utilized),
                "optimal_utilized_count": len(optimal_utilized),
                "under_utilized_count": len(under_utilized),
                "over_utilized_members": [rd.name for rd in over_utilized],
                "under_utilized_members": [rd.name for rd in under_utilized],
                "capacity_efficiency": overall_utilization,
                "capacity_shortage": max(0, total_workload - total_capacity),
                "available_capacity": max(0, total_capacity - total_workload)
            },
            "burnout_risk_analysis": {
                "distribution": burnout_distribution,
                "high_risk_members": [rd.name for rd in mock_resource_data if rd.burnout_risk in ["high", "critical"]],
                "declining_performance": [rd.name for rd in mock_resource_data if rd.performance_trend == "declining"]
            },
            "role_capacity_analysis": {
                "role_utilization": {role: round(role_workload[role] / role_capacity[role], 3) for role in role_capacity.keys()},
                "critical_roles": [role for role, util in {role: role_workload[role] / role_capacity[role] for role in role_capacity.keys()}.items() if util > 0.90],
                "capacity_gaps": [role for role, util in {role: role_workload[role] / role_capacity[role] for role in role_capacity.keys()}.items() if util > 1.0]
            },
            "weekly_capacity_forecast": weekly_forecasts if include_forecast else {},
            "critical_periods": critical_periods,
            "team_heatmap": mock_resource_data,
            "optimization_recommendations": [
                {
                    "priority": "high",
                    "recommendation": f"Address {len(over_utilized)} over-utilized team members",
                    "action": "Redistribute workload or extend timeline"
                },
                {
                    "priority": "medium", 
                    "recommendation": f"Leverage {len(under_utilized)} under-utilized team members",
                    "action": "Cross-train for critical skills or accelerate timeline"
                },
                {
                    "priority": "high" if len([rd for rd in mock_resource_data if rd.burnout_risk == "high"]) > 0 else "low",
                    "recommendation": "Monitor burnout risk indicators",
                    "action": "Implement workload balancing and stress management measures"
                }
            ],
            "ai_insights": {
                "key_finding": f"Team operating at {overall_utilization:.1%} capacity with {len(critical_periods)} critical periods identified",
                "efficiency_opportunities": [
                    "Cross-training Lisa Thompson in technical controls could provide Michael Rodriguez backup",
                    "Jennifer Park has available capacity to absorb documentation tasks during Michael's vacation",
                    "David Kim's part-time availability is well-utilized but could be increased for sprint periods"
                ],
                "risk_alerts": [
                    f"Michael Rodriguez at {mock_resource_data[1].utilization_rate:.0%} utilization with declining performance trend",
                    "Week of 2025-01-22 shows capacity constraint due to planned vacation"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating resource heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate resource heatmap")

@router.get("/{audit_id}/performance-kpis")
async def get_performance_kpis(
    audit_id: str,
    kpi_category: Optional[str] = None,  # 'velocity', 'quality', 'resource', 'timeline', 'risk'
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive performance KPIs and metrics dashboard"""
    try:
        current_time = datetime.utcnow()
        
        # Mock performance KPI data - in production, calculate from real metrics
        mock_kpis = [
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Gap Closure Velocity",
                kpi_type="velocity",
                current_value=0.83,
                target_value=0.80,
                baseline_value=1.0,
                trend_direction="up",
                performance_rating="excellent",
                measurement_unit="ratio",
                calculation_method="actual_days / planned_days (lower is better)",
                historical_values=[
                    {"date": "2025-01-01", "value": 1.0},
                    {"date": "2025-01-08", "value": 0.95},
                    {"date": "2025-01-15", "value": 0.87},
                    {"date": "2025-01-22", "value": 0.83}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Evidence Quality Score",
                kpi_type="quality",
                current_value=87.3,
                target_value=90.0,
                baseline_value=75.0,
                trend_direction="up",
                performance_rating="good",
                measurement_unit="percentage",
                calculation_method="weighted_average(ai_confidence, completeness, relevance)",
                historical_values=[
                    {"date": "2025-01-01", "value": 75.0},
                    {"date": "2025-01-08", "value": 79.2},
                    {"date": "2025-01-15", "value": 84.1},
                    {"date": "2025-01-22", "value": 87.3}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Team Utilization Rate",
                kpi_type="resource",
                current_value=78.5,
                target_value=80.0,
                baseline_value=65.0,
                trend_direction="up",
                performance_rating="good",
                measurement_unit="percentage",
                calculation_method="total_workload / total_capacity * 100",
                historical_values=[
                    {"date": "2025-01-01", "value": 65.0},
                    {"date": "2025-01-08", "value": 71.2},
                    {"date": "2025-01-15", "value": 75.8},
                    {"date": "2025-01-22", "value": 78.5}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Timeline Adherence",
                kpi_type="timeline",
                current_value=92.0,
                target_value=95.0,
                baseline_value=85.0,
                trend_direction="stable",
                performance_rating="good",
                measurement_unit="percentage",
                calculation_method="milestones_on_time / total_milestones * 100",
                historical_values=[
                    {"date": "2025-01-01", "value": 85.0},
                    {"date": "2025-01-08", "value": 88.5},
                    {"date": "2025-01-15", "value": 91.0},
                    {"date": "2025-01-22", "value": 92.0}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Risk Mitigation Rate",
                kpi_type="risk",
                current_value=68.0,
                target_value=75.0,
                baseline_value=45.0,
                trend_direction="up",
                performance_rating="average",
                measurement_unit="percentage",
                calculation_method="risks_mitigated / total_identified_risks * 100",
                historical_values=[
                    {"date": "2025-01-01", "value": 45.0},
                    {"date": "2025-01-08", "value": 52.0},
                    {"date": "2025-01-15", "value": 61.0},
                    {"date": "2025-01-22", "value": 68.0}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Stakeholder Engagement Score",
                kpi_type="quality",
                current_value=84.2,
                target_value=85.0,
                baseline_value=70.0,
                trend_direction="up",
                performance_rating="good",
                measurement_unit="score",
                calculation_method="weighted_average(response_rate, meeting_attendance, deliverable_approval)",
                historical_values=[
                    {"date": "2025-01-01", "value": 70.0},
                    {"date": "2025-01-08", "value": 76.3},
                    {"date": "2025-01-15", "value": 81.1},
                    {"date": "2025-01-22", "value": 84.2}
                ]
            ),
            PerformanceKPI(
                audit_id=audit_id,
                kpi_name="Budget Variance",
                kpi_type="resource",
                current_value=-5.2,  # Negative means under budget
                target_value=0.0,
                baseline_value=10.0,
                trend_direction="down",
                performance_rating="excellent",
                measurement_unit="percentage",
                calculation_method="(actual_spend - budget) / budget * 100",
                historical_values=[
                    {"date": "2025-01-01", "value": 0.0},
                    {"date": "2025-01-08", "value": -2.1},
                    {"date": "2025-01-15", "value": -3.8},
                    {"date": "2025-01-22", "value": -5.2}
                ]
            )
        ]
        
        # Apply category filter if provided
        if kpi_category:
            mock_kpis = [kpi for kpi in mock_kpis if kpi.kpi_type == kpi_category]
        
        # Calculate summary statistics
        total_kpis = len(mock_kpis)
        excellent_kpis = len([kpi for kpi in mock_kpis if kpi.performance_rating == "excellent"])
        good_kpis = len([kpi for kpi in mock_kpis if kpi.performance_rating == "good"])
        average_kpis = len([kpi for kpi in mock_kpis if kpi.performance_rating == "average"])
        poor_kpis = len([kpi for kpi in mock_kpis if kpi.performance_rating == "poor"])
        
        # Trend analysis
        improving_kpis = len([kpi for kpi in mock_kpis if kpi.trend_direction == "up"])
        stable_kpis = len([kpi for kpi in mock_kpis if kpi.trend_direction == "stable"])
        declining_kpis = len([kpi for kpi in mock_kpis if kpi.trend_direction == "down"])
        
        # Target achievement analysis
        on_target_kpis = []
        above_target_kpis = []
        below_target_kpis = []
        
        for kpi in mock_kpis:
            if kpi.kpi_name == "Budget Variance":  # Lower is better for budget variance
                if kpi.current_value <= kpi.target_value:
                    on_target_kpis.append(kpi.kpi_name)
                else:
                    below_target_kpis.append(kpi.kpi_name)
            else:  # Higher is better for most KPIs
                if abs(kpi.current_value - kpi.target_value) <= (kpi.target_value * 0.05):  # Within 5%
                    on_target_kpis.append(kpi.kpi_name)
                elif kpi.current_value > kpi.target_value:
                    above_target_kpis.append(kpi.kpi_name)
                else:
                    below_target_kpis.append(kpi.kpi_name)
        
        # Category performance breakdown
        category_performance = {}
        for kpi in mock_kpis:
            if kpi.kpi_type not in category_performance:
                category_performance[kpi.kpi_type] = {
                    "count": 0,
                    "excellent": 0,
                    "good": 0,
                    "average": 0,
                    "poor": 0
                }
            category_performance[kpi.kpi_type]["count"] += 1
            category_performance[kpi.kpi_type][kpi.performance_rating] += 1
        
        # Calculate composite scores
        composite_scores = {}
        for category in category_performance.keys():
            category_kpis = [kpi for kpi in mock_kpis if kpi.kpi_type == category]
            if category_kpis:
                # Normalize all KPIs to 0-100 scale for composite calculation
                normalized_scores = []
                for kpi in category_kpis:
                    if kpi.kpi_name == "Budget Variance":  # Invert for budget variance
                        normalized_score = max(0, 100 + kpi.current_value)  # Convert negative variance to positive score
                    elif kpi.measurement_unit == "ratio":
                        normalized_score = min(100, (1 / kpi.current_value) * 100)  # Invert ratio (lower is better)
                    else:
                        normalized_score = kpi.current_value
                    normalized_scores.append(normalized_score)
                
                composite_scores[category] = sum(normalized_scores) / len(normalized_scores)
        
        return {
            "audit_id": audit_id,
            "analysis_timestamp": current_time.isoformat(),
            "kpi_category_filter": kpi_category,
            "kpi_summary": {
                "total_kpis": total_kpis,
                "performance_distribution": {
                    "excellent": excellent_kpis,
                    "good": good_kpis,
                    "average": average_kpis,
                    "poor": poor_kpis
                },
                "trend_analysis": {
                    "improving": improving_kpis,
                    "stable": stable_kpis,
                    "declining": declining_kpis
                },
                "target_achievement": {
                    "on_target": len(on_target_kpis),
                    "above_target": len(above_target_kpis),
                    "below_target": len(below_target_kpis)
                },
                "overall_health": "excellent" if excellent_kpis >= total_kpis * 0.5 else "good" if good_kpis + excellent_kpis >= total_kpis * 0.7 else "needs_improvement"
            },
            "category_performance": category_performance,
            "composite_scores": composite_scores,
            "kpi_data": mock_kpis,
            "target_achievement_details": {
                "on_target_kpis": on_target_kpis,
                "above_target_kpis": above_target_kpis,
                "below_target_kpis": below_target_kpis
            },
            "performance_insights": {
                "best_performing_category": max(composite_scores.keys(), key=lambda k: composite_scores[k]) if composite_scores else None,
                "needs_attention_category": min(composite_scores.keys(), key=lambda k: composite_scores[k]) if composite_scores else None,
                "trending_positively": [kpi.kpi_name for kpi in mock_kpis if kpi.trend_direction == "up" and kpi.performance_rating in ["good", "excellent"]],
                "attention_required": [kpi.kpi_name for kpi in mock_kpis if kpi.performance_rating in ["poor", "average"] or kpi.trend_direction == "down"]
            },
            "ai_insights": {
                "key_finding": f"Performance health: {excellent_kpis + good_kpis}/{total_kpis} KPIs meeting or exceeding expectations",
                "trending_positively": [kpi.kpi_name for kpi in mock_kpis if kpi.trend_direction == "up" and kpi.performance_rating in ["good", "excellent"]],
                "attention_required": [kpi.kpi_name for kpi in mock_kpis if kpi.performance_rating in ["poor", "average"] or kpi.trend_direction == "down"],
                "recommendations": [
                    f"Focus on improving {len(below_target_kpis)} below-target KPIs: {', '.join(below_target_kpis[:3])}{'...' if len(below_target_kpis) > 3 else ''}",
                    f"Leverage success in {max(composite_scores.keys(), key=lambda k: composite_scores[k]) if composite_scores else 'N/A'} category as best practice model",
                    "Continue momentum on improving KPIs while maintaining strong performers"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving performance KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance KPIs")

@router.get("/{audit_id}/milestone-performance")
async def get_milestone_performance_metrics(
    audit_id: str,
    milestone_id: Optional[str] = None,
    include_predictions: bool = True,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed milestone performance analytics and predictions"""
    try:
        current_time = datetime.utcnow()
        
        # Mock milestone performance data - in production, aggregate from project tracking
        mock_milestone_metrics = [
            MilestonePerformanceMetrics(
                milestone_id="milestone-001",
                milestone_name="ISMS Documentation Complete",
                planned_start=current_time - timedelta(days=30),
                planned_end=current_time - timedelta(days=10),
                actual_start=current_time - timedelta(days=28),
                actual_end=current_time - timedelta(days=8),
                completion_percentage=100.0,
                velocity_score=0.90,  # 18 actual days / 20 planned days
                quality_score=92.5,
                effort_variance=0.85,  # Actual effort was 85% of planned
                blockers_count=2,
                dependencies_satisfied=True,
                team_performance={
                    "user-123": 95.0,  # Sarah Chen
                    "user-202": 90.0,  # Lisa Thompson
                    "user-456": 88.0   # Michael Rodriguez
                },
                risk_mitigation_effectiveness=0.85
            ),
            MilestonePerformanceMetrics(
                milestone_id="milestone-002",
                milestone_name="All Training Records Updated",
                planned_start=current_time - timedelta(days=25),
                planned_end=current_time - timedelta(days=5),
                actual_start=current_time - timedelta(days=23),
                actual_end=None,  # Still in progress
                completion_percentage=75.0,
                velocity_score=0.88,  # On track for early completion
                quality_score=89.2,
                effort_variance=1.05,  # Slightly over planned effort
                blockers_count=1,
                dependencies_satisfied=True,
                team_performance={
                    "user-789": 92.0,  # Jennifer Park
                    "user-456": 87.0   # Michael Rodriguez
                },
                risk_mitigation_effectiveness=0.90
            ),
            MilestonePerformanceMetrics(
                milestone_id="milestone-003",
                milestone_name="Vendor Assessments Complete",
                planned_start=current_time - timedelta(days=20),
                planned_end=current_time + timedelta(days=5),
                actual_start=current_time - timedelta(days=18),
                actual_end=None,  # Still in progress
                completion_percentage=60.0,
                velocity_score=1.12,  # Behind schedule
                quality_score=85.7,
                effort_variance=1.20,  # 20% over planned effort
                blockers_count=3,
                dependencies_satisfied=False,
                team_performance={
                    "user-789": 85.0,  # Jennifer Park
                    "user-101": 88.0   # David Kim
                },
                risk_mitigation_effectiveness=0.70
            ),
            MilestonePerformanceMetrics(
                milestone_id="milestone-004",
                milestone_name="Audit Preparation Complete",
                planned_start=current_time + timedelta(days=5),
                planned_end=current_time + timedelta(days=25),
                actual_start=None,  # Not started
                actual_end=None,
                completion_percentage=0.0,
                velocity_score=1.0,  # Baseline
                quality_score=0.0,
                effort_variance=1.0,  # Planned
                blockers_count=0,
                dependencies_satisfied=False,  # Depends on milestone-003
                team_performance={},
                risk_mitigation_effectiveness=0.0
            )
        ]
        
        # Apply milestone filter if provided
        if milestone_id:
            mock_milestone_metrics = [mm for mm in mock_milestone_metrics if mm.milestone_id == milestone_id]
        
        # Calculate overall analytics
        total_milestones = len(mock_milestone_metrics)
        completed_milestones = len([mm for mm in mock_milestone_metrics if mm.completion_percentage == 100.0])
        in_progress_milestones = len([mm for mm in mock_milestone_metrics if 0 < mm.completion_percentage < 100.0])
        not_started_milestones = len([mm for mm in mock_milestone_metrics if mm.completion_percentage == 0.0])
        
        # Performance aggregations
        active_milestones = [mm for mm in mock_milestone_metrics if mm.completion_percentage > 0]
        if active_milestones:
            average_velocity = sum(mm.velocity_score for mm in active_milestones) / len(active_milestones)
            average_quality = sum(mm.quality_score for mm in active_milestones) / len(active_milestones)
            average_effort_variance = sum(mm.effort_variance for mm in active_milestones) / len(active_milestones)
            total_blockers = sum(mm.blockers_count for mm in mock_milestone_metrics)
        else:
            average_velocity = average_quality = average_effort_variance = total_blockers = 0
        
        # Risk analysis
        at_risk_milestones = [
            mm for mm in mock_milestone_metrics 
            if mm.velocity_score > 1.05 or mm.blockers_count > 2 or not mm.dependencies_satisfied
        ]
        
        # Team performance aggregation
        team_performance_summary = {}
        for mm in mock_milestone_metrics:
            for user_id, performance in mm.team_performance.items():
                if user_id not in team_performance_summary:
                    team_performance_summary[user_id] = []
                team_performance_summary[user_id].append(performance)
        
        # Calculate average team performance per user
        average_team_performance = {
            user_id: sum(performances) / len(performances)
            for user_id, performances in team_performance_summary.items()
        }
        
        # Predictions for future milestones (if enabled)
        predictions = {}
        if include_predictions and active_milestones:
            future_milestones = [mm for mm in mock_milestone_metrics if mm.completion_percentage == 0.0]
            
            for fm in future_milestones:
                # Simple prediction based on historical performance
                predicted_velocity = average_velocity * (1 + (average_effort_variance - 1) * 0.5)  # Adjust for effort variance
                predicted_completion_date = fm.planned_end + timedelta(days=int((predicted_velocity - 1) * 20))  # Assume 20-day baseline
                
                predictions[fm.milestone_id] = {
                    "milestone_name": fm.milestone_name,
                    "planned_completion": fm.planned_end.isoformat(),
                    "predicted_completion": predicted_completion_date.isoformat(),
                    "predicted_velocity_score": round(predicted_velocity, 3),
                    "confidence_level": "high" if predicted_velocity <= 1.1 else "medium" if predicted_velocity <= 1.3 else "low",
                    "risk_factors": [
                        "Team velocity trending slower than planned" if average_velocity > 1.0 else "Team velocity exceeding expectations",
                        f"Average effort variance: {average_effort_variance:.1%}" if average_effort_variance != 1.0 else "Effort tracking on target",
                        f"Dependency chain at risk" if not fm.dependencies_satisfied else "Dependencies satisfied"
                    ],
                    "success_probability": max(0.1, min(0.95, 1.0 - (predicted_velocity - 1.0) * 2))  # Simple probability model
                }
        
        # Critical path analysis
        critical_path_analysis = {
            "critical_milestones": [
                mm.milestone_id for mm in mock_milestone_metrics 
                if mm.blockers_count > 0 or not mm.dependencies_satisfied or mm.velocity_score > 1.1
            ],
            "bottleneck_milestone": max(
                [mm for mm in mock_milestone_metrics if mm.completion_percentage > 0], 
                key=lambda x: x.velocity_score, 
                default=None
            ).milestone_id if active_milestones else None,
            "fastest_milestone": min(
                [mm for mm in mock_milestone_metrics if mm.completion_percentage == 100.0], 
                key=lambda x: x.velocity_score, 
                default=None
            ).milestone_id if completed_milestones > 0 else None
        }
        
        return {
            "audit_id": audit_id,
            "analysis_timestamp": current_time.isoformat(),
            "milestone_filter": milestone_id,
            "performance_summary": {
                "total_milestones": total_milestones,
                "completed": completed_milestones,
                "in_progress": in_progress_milestones,
                "not_started": not_started_milestones,
                "completion_rate": completed_milestones / total_milestones if total_milestones > 0 else 0,
                "average_velocity_score": round(average_velocity, 3),
                "average_quality_score": round(average_quality, 1),
                "velocity_trend": "ahead_of_schedule" if average_velocity < 0.95 else "on_schedule" if average_velocity <= 1.05 else "behind_schedule"
            },
            "performance_aggregates": {
                "average_velocity_score": round(average_velocity, 3),
                "average_quality_score": round(average_quality, 1),
                "average_effort_variance": round(average_effort_variance, 3),
                "total_active_blockers": total_blockers,
                "velocity_trend": "ahead_of_schedule" if average_velocity < 0.95 else "on_schedule" if average_velocity <= 1.05 else "behind_schedule"
            },
            "risk_analysis": {
                "at_risk_milestones": len(at_risk_milestones),
                "risk_details": [
                    {
                        "milestone_id": mm.milestone_id,
                        "milestone_name": mm.milestone_name,
                        "risk_factors": [
                            f"Velocity score: {mm.velocity_score}" if mm.velocity_score > 1.05 else None,
                            f"Active blockers: {mm.blockers_count}" if mm.blockers_count > 2 else None,
                            "Dependencies not satisfied" if not mm.dependencies_satisfied else None
                        ],
                        "risk_level": "high" if mm.velocity_score > 1.2 or mm.blockers_count > 3 else "medium"
                    }
                    for mm in at_risk_milestones
                ]
            },
            "team_performance_summary": average_team_performance,
            "critical_path_analysis": critical_path_analysis,
            "milestone_data": mock_milestone_metrics,
            "predictions": predictions if include_predictions else {},
            "ai_insights": {
                "key_finding": f"Milestone performance: {completed_milestones}/{total_milestones} completed, average velocity {average_velocity:.2f}x planned",
                "performance_highlights": [
                    f"Best performing milestone: {critical_path_analysis['fastest_milestone'] or 'N/A'}" if completed_milestones > 0 else "No completed milestones yet",
                    f"Team quality score averaging {average_quality:.1f}%" if active_milestones else "Quality metrics pending milestone activity",
                    f"Effort variance {average_effort_variance:.1%} of planned" if active_milestones else "Effort tracking will begin with active milestones"
                ],
                "attention_required": [
                    f"{len(at_risk_milestones)} milestones identified as at-risk" if at_risk_milestones else "No milestones currently at risk",
                    f"Total {total_blockers} active blockers across all milestones" if total_blockers > 0 else "No active blockers reported",
                    "Dependency chain management critical for upcoming milestones" if any(not mm.dependencies_satisfied for mm in mock_milestone_metrics) else "All dependencies currently satisfied"
                ],
                "recommendations": [
                    "Focus on resolving blockers for at-risk milestones to maintain timeline",
                    "Leverage high-performing team patterns for upcoming milestone assignments",
                    "Implement proactive dependency management for future milestones"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving milestone performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve milestone performance metrics")

# Background Tasks

async def create_default_milestones(
    audit_id: str,
    framework: str,
    preparation_start: datetime,
    audit_date: datetime
):
    """Background task to create default milestones based on framework"""
    try:
        # Mock implementation for development
        # In production, this would create actual database records
        
        # Calculate timeline intervals
        total_days = (audit_date - preparation_start).days
        
        # Framework-specific milestone templates
        milestone_templates = {
            "ISO 27001:2022": [
                {"name": "ISMS Documentation Review", "offset_days": int(total_days * 0.2), "category": "documentation", "priority": "critical"},
                {"name": "Asset Inventory Verification", "offset_days": int(total_days * 0.3), "category": "preparation", "priority": "high"},
                {"name": "Risk Assessment Updates", "offset_days": int(total_days * 0.5), "category": "review", "priority": "high"},
                {"name": "Training Records Completion", "offset_days": int(total_days * 0.7), "category": "preparation", "priority": "critical"},
                {"name": "Internal Audit Completion", "offset_days": int(total_days * 0.85), "category": "review", "priority": "critical"},
                {"name": "Management Review", "offset_days": int(total_days * 0.95), "category": "review", "priority": "critical"}
            ],
            "NIST CSF 2.0": [
                {"name": "Governance Framework Review", "offset_days": int(total_days * 0.25), "category": "documentation", "priority": "high"},
                {"name": "Asset Identification Verification", "offset_days": int(total_days * 0.4), "category": "preparation", "priority": "high"},
                {"name": "Protection Controls Assessment", "offset_days": int(total_days * 0.6), "category": "review", "priority": "critical"},
                {"name": "Detection Capabilities Testing", "offset_days": int(total_days * 0.75), "category": "preparation", "priority": "high"},
                {"name": "Response Plan Validation", "offset_days": int(total_days * 0.85), "category": "review", "priority": "high"},
                {"name": "Recovery Procedures Review", "offset_days": int(total_days * 0.95), "category": "review", "priority": "medium"}
            ]
        }
        
        templates = milestone_templates.get(framework, milestone_templates["ISO 27001:2022"])
        
        # Mock milestone creation (in production, would insert into database)
        logger.info(f"Mock: Created {len(templates)} default milestones for audit {audit_id}")
        
    except Exception as e:
        logger.error(f"Error creating default milestones for audit {audit_id}: {str(e)}")