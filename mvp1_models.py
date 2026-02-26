"""
MVP 1 - Multi-tenant Compliance Collaboration Platform Models
Database schema for role-based workflow synchronization across user personas

Architecture:
- Multi-tenant organization segregation  
- 4 distinct roles: Admin, Analyst, Auditor, Leadership
- Framework-based engagements with real-time collaboration
- Immediate AI processing with feedback loops
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from enum import Enum

# =====================================
# CORE ENUMS AND CONSTANTS
# =====================================

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    LEADERSHIP = "leadership"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class EngagementStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class EvidenceStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"

class AIProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

# =====================================
# MULTI-TENANT ORGANIZATION MODELS
# =====================================

class MVP1Organization(BaseModel):
    """Enhanced organization model for multi-tenancy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    
    # Organization Details
    industry: Optional[str] = None
    size: Optional[str] = None  # "Small (1-50)", "Medium (51-500)", "Large (500+)"
    headquarters_location: Optional[str] = None
    established_date: Optional[datetime] = None
    
    # Subscription and Limits
    subscription_tier: str = "standard"  # "trial", "standard", "premium", "enterprise"
    max_users: int = 50
    max_engagements: int = 10
    storage_limit_gb: int = 10
    
    # Configuration
    supported_frameworks: List[str] = ["ISO 27001", "NIST CSF", "SOC 2 Type I", "Ghana CII Directives"]
    enabled_features: List[str] = ["ai_processing", "real_time_collaboration", "advanced_analytics"]
    custom_settings: Dict[str, Any] = {}
    
    # Status and Metadata
    status: str = "active"  # "active", "suspended", "trial", "expired"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Admin Information
    primary_admin_id: Optional[str] = None
    billing_contact_id: Optional[str] = None
    
    # Authentication Bridge
    daakyi_org_id: Optional[str] = None  # For tracking original DAAKYI organization

# =====================================
# ENHANCED USER MANAGEMENT MODELS
# =====================================

class MVP1User(BaseModel):
    """Enhanced user model with role-based permissions and multi-tenant support"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    name: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    
    # Organization and Role
    organization_id: str
    role: UserRole
    department: Optional[str] = None
    job_title: Optional[str] = None
    
    # Authentication and Session
    password_hash: Optional[str] = None  # For internal credential management
    session_token: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    
    # Permissions and Access
    permissions: List[str] = []  # Role-based permissions
    assigned_engagements: List[str] = []  # Engagement IDs user has access to
    managed_frameworks: List[str] = []  # Frameworks user can work with
    business_units_access: List[str] = []  # Business units user can access
    
    # User Preferences
    notification_preferences: Dict[str, bool] = {
        "email_notifications": True,
        "task_reminders": True,
        "escalation_alerts": True,
        "weekly_summaries": True
    }
    dashboard_layout: Dict[str, Any] = {}
    timezone: str = "UTC"
    language: str = "en"
    
    # Status and Metadata
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Admin who created this user
    last_activity: Optional[datetime] = None
    
    # Performance Tracking (for analytics)
    completed_tasks: int = 0
    avg_task_completion_time: Optional[float] = None  # in hours
    quality_score: Optional[float] = None  # 0-100

class UserPermissions:
    """Static class defining role-based permission matrices"""
    
    ADMIN_PERMISSIONS = [
        "manage_users", "create_users", "delete_users", "manage_engagements",
        "create_engagements", "archive_engagements", "view_all_data", 
        "manage_organization", "access_audit_logs", "configure_system",
        "bulk_operations", "export_data", "manage_permissions"
    ]
    
    ANALYST_PERMISSIONS = [
        "view_assigned_engagements", "submit_responses", "upload_evidence",
        "view_ai_insights", "receive_tasks", "request_clarification",
        "view_own_progress", "collaborate_realtime"
    ]
    
    AUDITOR_PERMISSIONS = [
        "view_analyst_submissions", "provide_feedback", "approve_responses",
        "reject_responses", "annotate_evidence", "flag_issues", 
        "recommend_actions", "update_status", "view_ai_analysis",
        "collaborate_realtime", "export_reviews"
    ]
    
    LEADERSHIP_PERMISSIONS = [
        "view_summaries", "view_dashboards", "view_analytics", 
        "download_reports", "track_progress", "view_risk_scores",
        "view_predictive_metrics", "export_executive_reports"
    ]

# =====================================
# ENGAGEMENT MANAGEMENT MODELS
# =====================================

class ComplianceEngagement(BaseModel):
    """Framework-based compliance engagements with organizational context"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    name: str  # e.g., "ISO 27001 Readiness – AlphaTech Q3 2025"
    description: Optional[str] = None
    engagement_code: str = Field(default_factory=lambda: f"ENG-{str(uuid.uuid4())[:8].upper()}")
    
    # Framework and Scope
    framework: str  # "ISO 27001", "NIST CSF", "SOC 2 Type I", "Ghana CII Directives"
    framework_version: Optional[str] = None
    framework_focus: Optional[str] = None  # e.g., "Cloud Focus" for specialized assessments
    
    # Organizational Context
    organization_id: str
    client_name: str  # e.g., "AlphaTech Solutions"
    business_unit: Optional[str] = None
    
    # Timeline and Status
    status: EngagementStatus = EngagementStatus.DRAFT
    target_quarter: str  # e.g., "Q3 2025"
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    
    # Team Assignments
    engagement_lead: str  # Admin user ID
    assigned_analysts: List[str] = []  # Analyst user IDs
    assigned_auditors: List[str] = []  # Auditor user IDs
    leadership_stakeholders: List[str] = []  # Leadership user IDs
    
    # Progress Tracking
    total_controls: int = 0
    completed_controls: int = 0
    approved_controls: int = 0
    flagged_controls: int = 0
    completion_percentage: float = 0.0
    
    # AI and Analytics
    ai_risk_score: Optional[float] = None  # 0-100
    predictive_completion_date: Optional[datetime] = None
    ai_confidence_level: Optional[float] = None
    
    # Configuration
    evidence_requirements: Dict[str, List[str]] = {}  # Control -> Evidence types
    approval_workflow: Dict[str, Any] = {}  # Workflow configuration
    notification_settings: Dict[str, bool] = {}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # Admin user ID
    
class EngagementControl(BaseModel):
    """Individual controls within engagements with status tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Control Identity
    engagement_id: str
    control_id: str  # Framework-specific control ID
    control_name: str
    control_description: str
    control_category: Optional[str] = None
    
    # Assignment and Status
    assigned_analyst: Optional[str] = None  # Analyst user ID
    assigned_auditor: Optional[str] = None  # Auditor user ID
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: str = "medium"  # "low", "medium", "high", "critical"
    
    # Progress Tracking
    analyst_response_submitted: bool = False
    auditor_review_completed: bool = False
    final_approval: bool = False
    completion_percentage: float = 0.0
    
    # Evidence and Documentation
    evidence_count: int = 0
    evidence_approved_count: int = 0
    current_state_notes: Optional[str] = None  # Analyst's current state description
    
    # AI Analysis
    ai_analysis_status: AIProcessingStatus = AIProcessingStatus.PENDING
    ai_analysis_results: Optional[Dict[str, Any]] = None
    ai_recommendations: List[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    analyst_submission_date: Optional[datetime] = None
    auditor_review_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    organization_id: str  # For multi-tenant isolation

# =====================================
# CURRENT STATE INTAKE FORM MODELS
# =====================================

class CurrentStateIntakeForm(BaseModel):
    """Analyst's current state intake form for engagements"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Form Context
    engagement_id: str
    control_id: str
    analyst_id: str
    
    # Current State Assessment
    implementation_status: str  # "not_implemented", "partially_implemented", "fully_implemented"
    implementation_description: str  # Required detailed description
    current_controls_in_place: List[str] = []  # List of existing controls
    
    # Gap Analysis
    identified_gaps: List[str] = []  # Gaps identified by analyst
    risk_assessment: str = "medium"  # "low", "medium", "high", "critical"
    business_impact_if_failed: str  # Impact description
    
    # Resources and Timeline
    required_resources: List[str] = []  # Resources needed for compliance
    estimated_implementation_time: Optional[int] = None  # Hours
    target_completion_date: Optional[datetime] = None
    
    # Evidence and Documentation
    current_documentation: List[str] = []  # Existing documentation
    evidence_gaps: List[str] = []  # Missing evidence identified
    
    # Form Status
    status: str = "draft"  # "draft", "submitted", "under_review", "approved", "needs_revision"
    completion_percentage: float = 0.0
    responses: Optional[Dict[str, Any]] = None  # Flexible container for extra assessment context
    
    # AI Processing
    ai_processed: bool = False
    ai_analysis_results: Optional[Dict[str, Any]] = None
    ai_generated_tasks: List[str] = []  # Task suggestions from AI
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)
    
    organization_id: str  # For multi-tenant isolation

# =====================================
# EVIDENCE MANAGEMENT MODELS
# =====================================

class ComplianceEvidence(BaseModel):
    """Enhanced evidence model with AI processing and auditor feedback"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # File Information
    filename: str
    original_filename: str
    file_path: str  # Storage path
    file_size: int  # bytes
    file_type: str  # "pdf", "docx", "xlsx", "jpg", "png"
    mime_type: str
    file_hash: str  # For integrity verification
    
    # Context and Association
    engagement_id: str
    control_id: str
    intake_form_id: Optional[str] = None  # Link to intake form
    evidence_type: str  # "policy", "procedure", "screenshot", "log", "certificate", "other"
    evidence_description: Optional[str] = None
    
    # Status and Processing
    status: EvidenceStatus = EvidenceStatus.UPLOADED
    processing_status: AIProcessingStatus = AIProcessingStatus.PENDING
    
    # AI Analysis
    ai_analysis_completed: bool = False
    ai_analysis_results: Optional[Dict[str, Any]] = None
    ai_confidence_score: Optional[float] = None  # 0-1
    ai_extracted_metadata: Dict[str, Any] = {}
    ai_compliance_assessment: Optional[str] = None
    
    # Auditor Review
    auditor_reviewed: bool = False
    auditor_approval: Optional[bool] = None
    auditor_comments: Optional[str] = None
    auditor_annotations: List[Dict[str, Any]] = []  # Annotations on the evidence
    quality_score: Optional[int] = None  # 1-5 rating from auditor
    
    # User Attribution
    uploaded_by: str  # Analyst user ID
    reviewed_by: Optional[str] = None  # Auditor user ID
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    ai_processed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    
    organization_id: str  # For multi-tenant isolation
    
class EvidenceAnnotation(BaseModel):
    """Auditor annotations on evidence files"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    evidence_id: str
    auditor_id: str
    annotation_type: str  # "highlight", "comment", "flag", "recommendation"
    
    # Annotation Content
    page_number: Optional[int] = None  # For multi-page documents
    position: Optional[Dict[str, float]] = None  # X, Y coordinates if applicable
    text_content: Optional[str] = None  # Highlighted text
    comment: str  # Auditor's comment
    
    # Classification
    severity: str = "info"  # "info", "warning", "critical"
    category: str  # "missing_info", "incomplete", "excellent", "needs_clarification"
    
    # Status
    resolved: bool = False
    analyst_response: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    organization_id: str

# =====================================
# REAL-TIME COLLABORATION MODELS
# =====================================

class CollaborationActivity(BaseModel):
    """Real-time activity tracking for collaboration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Activity Context
    engagement_id: str
    control_id: Optional[str] = None
    evidence_id: Optional[str] = None
    
    # Activity Details
    activity_type: str  # "form_updated", "evidence_uploaded", "feedback_provided", "status_changed"
    actor_id: str  # User who performed the action
    actor_name: str
    actor_role: UserRole
    
    # Activity Content
    activity_description: str
    changes_made: Dict[str, Any] = {}  # What changed
    previous_values: Dict[str, Any] = {}  # Previous state
    new_values: Dict[str, Any] = {}  # New state
    
    # Visibility and Notifications
    visible_to_roles: List[UserRole] = []  # Which roles can see this activity
    notification_sent: bool = False
    real_time_broadcast: bool = True  # Whether to broadcast via WebSocket
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: str

class RealTimeFeedback(BaseModel):
    """Real-time feedback between analysts and auditors"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Feedback Context
    engagement_id: str
    control_id: str
    target_type: str  # "intake_form", "evidence", "response"
    target_id: str  # ID of the item being reviewed
    
    # Feedback Details
    feedback_type: str  # "approval", "rejection", "clarification_request", "recommendation"
    feedback_text: str
    severity: str = "normal"  # "low", "normal", "high", "urgent"
    
    # Status and Resolution
    status: str = "open"  # "open", "addressed", "resolved", "dismissed"
    requires_action: bool = True
    action_taken: Optional[str] = None
    
    # User Attribution
    provided_by: str  # Auditor user ID
    provided_by_name: str
    addressed_by: Optional[str] = None  # Analyst user ID
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    addressed_at: Optional[datetime] = None
    
    organization_id: str

# =====================================
# AI PROCESSING AND RECOMMENDATIONS
# =====================================

class AIProcessingJob(BaseModel):
    """AI processing jobs for evidence and forms"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Job Context
    job_type: str  # "evidence_analysis", "form_analysis", "risk_assessment", "recommendation_generation"
    target_type: str  # "evidence", "intake_form", "engagement"
    target_id: str
    engagement_id: str
    
    # Processing Details
    status: AIProcessingStatus = AIProcessingStatus.PENDING
    processing_model: str = "gpt-4o"  # AI model used
    processing_parameters: Dict[str, Any] = {}
    
    # Results
    processing_results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    generated_recommendations: List[str] = []
    identified_risks: List[Dict[str, Any]] = []
    
    # Performance Metrics
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    processing_duration_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Error Handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    organization_id: str

class SystemRecommendation(BaseModel):
    """AI-generated task and action recommendations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Recommendation Context
    engagement_id: str
    control_id: Optional[str] = None
    target_user_id: str  # User the recommendation is for
    target_user_role: UserRole
    
    # Recommendation Details
    recommendation_type: str  # "task", "evidence_request", "process_improvement", "training", "escalation"
    title: str
    description: str
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    
    # Implementation
    estimated_effort_hours: Optional[float] = None
    suggested_due_date: Optional[datetime] = None
    prerequisite_actions: List[str] = []
    success_criteria: List[str] = []
    
    # AI Metadata
    ai_confidence: float  # 0-1
    generated_by_model: str = "gpt-4o"
    generation_context: Dict[str, Any] = {}  # Context used for generation
    
    # Status and Feedback
    status: str = "pending"  # "pending", "accepted", "rejected", "completed"
    user_feedback: Optional[str] = None
    implementation_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    organization_id: str

# =====================================
# LEADERSHIP DASHBOARD MODELS
# =====================================

class ExecutiveSummary(BaseModel):
    """Executive-level summaries for leadership dashboard"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Summary Context
    organization_id: str
    engagement_id: Optional[str] = None  # If None, organization-wide summary
    summary_type: str  # "weekly", "monthly", "quarterly", "engagement_specific"
    
    # Key Metrics
    total_engagements: int = 0
    active_engagements: int = 0
    completed_engagements: int = 0
    overall_compliance_percentage: float = 0.0
    
    # Risk and Status
    high_risk_areas: List[str] = []
    critical_issues_count: int = 0
    overdue_items_count: int = 0
    avg_engagement_health_score: float = 0.0
    
    # Progress and Performance
    month_over_month_improvement: float = 0.0
    projected_completion_dates: Dict[str, datetime] = {}  # Engagement -> Date
    resource_utilization: Dict[str, float] = {}  # Team utilization metrics
    
    # AI Insights
    ai_generated_insights: List[str] = []
    predicted_risks: List[Dict[str, Any]] = []
    optimization_recommendations: List[str] = []
    
    # Financial Impact (if available)
    estimated_compliance_cost: Optional[float] = None
    risk_mitigation_value: Optional[float] = None
    efficiency_gains: Optional[float] = None
    
    # Timestamps
    summary_period_start: datetime
    summary_period_end: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    next_update_scheduled: Optional[datetime] = None

class ComplianceHeatmap(BaseModel):
    """Heatmap data for visual compliance status representation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Heatmap Context
    organization_id: str
    engagement_id: Optional[str] = None
    framework: Optional[str] = None
    
    # Heatmap Data
    heatmap_type: str  # "framework_controls", "business_units", "risk_areas", "timeline"
    data_points: List[Dict[str, Any]] = []  # Individual heatmap cells
    risk_scores: Dict[str, float] = {}  # Item -> Risk Score
    status_distribution: Dict[str, int] = {}  # Status -> Count
    
    # Visualization Configuration
    color_scheme: str = "risk_based"  # "risk_based", "progress_based", "custom"
    scale_min: float = 0.0
    scale_max: float = 100.0
    threshold_values: Dict[str, float] = {}
    
    # AI Analysis
    ai_generated_patterns: List[str] = []
    anomaly_detection_results: List[Dict[str, Any]] = []
    trend_predictions: Dict[str, Any] = {}
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: datetime = Field(default_factory=datetime.utcnow)
    auto_refresh_enabled: bool = True
    refresh_frequency_minutes: int = 30

# =====================================
# AUDIT TRAIL AND LOGGING MODELS
# =====================================

class AuditLogEntry(BaseModel):
    """Comprehensive audit trail for compliance and accountability"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Log Context
    organization_id: str
    engagement_id: Optional[str] = None
    
    # Action Details
    action_type: str  # "user_login", "form_submission", "evidence_upload", "status_change", "approval", "rejection"
    action_description: str
    actor_id: str  # User who performed the action
    actor_name: str
    actor_role: UserRole
    actor_ip_address: Optional[str] = None
    
    # Target Information
    target_type: Optional[str] = None  # "user", "engagement", "evidence", "form"
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    
    # Change Tracking
    changes_made: Dict[str, Any] = {}
    previous_state: Dict[str, Any] = {}
    new_state: Dict[str, Any] = {}
    
    # Classification
    log_level: str = "info"  # "debug", "info", "warning", "error", "critical"
    category: str  # "authentication", "data_change", "system_operation", "security"
    sensitive_data: bool = False  # Whether this log contains sensitive information
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_metadata: Dict[str, Any] = {}

# =====================================
# API REQUEST/RESPONSE MODELS
# =====================================

class CreateEngagementRequest(BaseModel):
    """Request to create a new compliance engagement"""
    name: str
    description: Optional[str] = None
    framework: str
    framework_version: Optional[str] = None
    client_name: str
    target_quarter: str
    target_completion_date: Optional[datetime] = None
    assigned_analysts: List[str] = []
    assigned_auditors: List[str] = []
    leadership_stakeholders: List[str] = []

class CurrentStateSubmissionRequest(BaseModel):
    """Request to submit current state intake form"""
    engagement_id: str
    control_id: str
    implementation_status: str
    implementation_description: str
    current_controls_in_place: List[str] = []
    identified_gaps: List[str] = []
    risk_assessment: str
    business_impact_if_failed: str
    required_resources: List[str] = []
    estimated_implementation_time: Optional[int] = None

class EvidenceUploadRequest(BaseModel):
    """Request to upload compliance evidence"""
    engagement_id: str
    control_id: str
    evidence_type: str
    evidence_description: Optional[str] = None
    filename: str
    file_size: int
    file_type: str

class AuditorFeedbackRequest(BaseModel):
    """Request to provide auditor feedback"""
    target_type: str  # "intake_form", "evidence", "response"
    target_id: str
    feedback_type: str
    feedback_text: str
    approval: Optional[bool] = None
    requires_action: bool = True

class UserCreationRequest(BaseModel):
    """Admin request to create new users"""
    name: str
    email: str
    role: UserRole
    department: Optional[str] = None
    job_title: Optional[str] = None
    assigned_engagements: List[str] = []
    permissions: Optional[List[str]] = None  # If None, use role defaults
    send_onboarding_email: bool = False  # Send email notification to new user

class EngagementAssignmentRequest(BaseModel):
    """Request to assign users to engagements"""
    engagement_id: str
    analyst_ids: List[str] = []
    auditor_ids: List[str] = []
    leadership_ids: List[str] = []

class DashboardDataResponse(BaseModel):
    """Response for dashboard data requests"""
    user_role: UserRole
    organization_summary: Dict[str, Any]
    engagement_summaries: List[Dict[str, Any]]
    pending_tasks: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]
    ai_recommendations: List[SystemRecommendation]
    alerts_and_notifications: List[Dict[str, Any]]

# =====================================
# WEBSOCKET AND REAL-TIME MODELS
# =====================================

class WebSocketMessage(BaseModel):
    """WebSocket message format for real-time updates"""
    message_type: str  # "activity_update", "feedback_received", "status_change", "notification"
    engagement_id: str
    target_user_roles: List[UserRole]
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: str
    sender_name: str

class NotificationPreferences(BaseModel):
    """User notification preferences"""
    user_id: str
    email_notifications: bool = True
    browser_notifications: bool = True
    task_reminders: bool = True
    feedback_alerts: bool = True
    escalation_notices: bool = True
    weekly_summaries: bool = True
    real_time_updates: bool = True
    notification_frequency: str = "immediate"  # "immediate", "hourly", "daily"