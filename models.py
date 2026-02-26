# ==================== EVIDENCE/ASSESSMENT LINK MODEL ====================


from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional, Dict, Any



class AssessmentEvidence(BaseModel):
    id: str
    assessment_id: str
    evidence_id: str
    evidence_name: Optional[str] = None
    evidence_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    status: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    control_mappings: Optional[List[str]] = None
    notes: Optional[str] = None
class EvidenceLifecycleState(BaseModel):
    id: str
    evidence_id: str
    current_state: str
    previous_state: Optional[str] = None
    state_changed_at: datetime
    state_changed_by: str
    reviewer_id: Optional[str] = None
    review_deadline: Optional[datetime] = None
    review_priority: Optional[str] = None
    state_comments: Optional[str] = None
    quality_score: Optional[float] = None
    quality_indicators: Optional[Dict[str, Any]] = None
    completeness_score: Optional[float] = None
    relevance_score: Optional[float] = None
    workflow_step: Optional[int] = None
    total_workflow_steps: Optional[int] = None
    can_auto_approve: Optional[bool] = None
    requires_expert_review: Optional[bool] = None
    organization_id: Optional[str] = None

class EvidenceReview(BaseModel):
    id: str
    evidence_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    review_type: Optional[str] = None
    review_status: Optional[str] = None
    review_outcome: Optional[str] = None
    quality_rating: Optional[int] = None
    completeness_rating: Optional[int] = None
    relevance_rating: Optional[int] = None
    clarity_rating: Optional[int] = None
    review_comments: Optional[str] = None
    strengths_identified: Optional[List[str]] = None
    improvements_needed: Optional[List[str]] = None
    additional_evidence_needed: Optional[List[str]] = None
    review_requested_at: Optional[datetime] = None
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    organization_id: Optional[str] = None

class EvidenceReviewRequest(BaseModel):
    review_outcome: str
    quality_rating: int
    completeness_rating: int
    relevance_rating: int
    clarity_rating: int
    review_comments: Optional[str] = None
    improvements_needed: Optional[List[str]] = None
    additional_evidence_needed: Optional[List[str]] = None

class EvidenceQualityMetrics(BaseModel):
    id: str
    evidence_id: str
    overall_quality_score: float
    confidence_level: float
    relevance_score: float
    completeness_score: float
    clarity_score: float
    currency_score: float
    authenticity_score: float
    document_type_detected: Optional[str] = None
    key_topics_identified: Optional[List[str]] = None
    control_mappings_suggested: Optional[List[Dict[str, Any]]] = None
    missing_elements: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    ai_model_used: Optional[str] = None
    analysis_timestamp: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    peer_comparison_percentile: Optional[float] = None
    organization_baseline_score: Optional[float] = None
    industry_benchmark_score: Optional[float] = None
    organization_id: Optional[str] = None

class EvidenceQualityAnalysisResponse(BaseModel):
    evidence_id: str
    quality_metrics: EvidenceQualityMetrics
    recommended_actions: List[str]
    auto_approval_eligible: bool = False
    requires_expert_review: bool = False

class BulkEvidenceOperationRequest(BaseModel):
    operation_type: str
    evidence_ids: List[str]
    operation_parameters: Optional[Dict[str, Any]] = None

class BulkEvidenceOperation(BaseModel):
    id: str
    operation_type: str
    evidence_ids: List[str]
    operation_parameters: Optional[Dict[str, Any]] = None
    batch_size: Optional[int] = None
    status: str
    total_items: int
    processed_items: Optional[int] = None
    successful_items: Optional[int] = None
    failed_items: Optional[int] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_details: Optional[List[Dict[str, Any]]] = None
    failure_details: Optional[List[Dict[str, Any]]] = None
    operation_log: Optional[List[Dict[str, Any]]] = None
    initiated_by: Optional[str] = None
    organization_id: Optional[str] = None
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    LEADERSHIP = "leadership"
    ASSESSMENT_MANAGER = "assessment manager"

class AssessmentStatus(str, Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"

class EvidenceStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ControlStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    NEEDS_REVIEW = "Needs Review"

# ==================== PHASE 4A: REPORT GENERATION MODELS ====================

class ReportType(str, Enum):
    """Report type enumeration for different report formats"""
    ASSESSMENT_SUMMARY = "assessment_summary"
    EXECUTIVE_SUMMARY = "executive_summary"
    COMPLIANCE_REPORT = "compliance_report"
    FRAMEWORK_ANALYSIS = "framework_analysis"
    TOKURO_AI_INSIGHTS = "tokuro_ai_insights"
    BOARD_PRESENTATION = "board_presentation"
    REMEDIATION_PLAN = "remediation_plan"

class ReportFormat(str, Enum):
    """Export format enumeration"""
    PDF = "pdf"
    PPTX = "pptx"
    DOCX = "docx"
    XLSX = "xlsx"
    HTML = "html"
    JSON = "json"

class ReportStatus(str, Enum):
    """Report generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADED = "downloaded"

class TokuroAIReportData(BaseModel):
    """Tokuro AI-specific data for report generation"""
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    framework_mappings: Dict[str, List[str]] = Field(default_factory=dict)
    gap_analysis: Dict[str, Any] = Field(default_factory=dict)
    remediation_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    maturity_scores: Dict[str, float] = Field(default_factory=dict)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    executive_insights: List[str] = Field(default_factory=list)

class ReportTemplate(BaseModel):
    """Report template configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    report_type: ReportType
    supported_formats: List[ReportFormat]
    template_path: str
    is_active: bool = True
    organization_id: Optional[str] = None  # None for system templates
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Template configuration
    sections: List[str] = Field(default_factory=list)
    dynamic_fields: Dict[str, str] = Field(default_factory=dict)
    branding_config: Dict[str, Any] = Field(default_factory=dict)
    tokuro_ai_enabled: bool = True

class ReportGeneration(BaseModel):
    """Report generation request and tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    
    # Source data
    assessment_id: Optional[str] = None
    organization_id: str
    created_by: str
    
    # Report configuration
    report_type: ReportType
    report_format: ReportFormat
    template_id: str
    
    # Generation settings
    include_tokuro_ai: bool = True
    include_executive_summary: bool = False
    include_remediation_plan: bool = False
    custom_branding: Dict[str, Any] = Field(default_factory=dict)
    
    # Status tracking
    status: ReportStatus = ReportStatus.PENDING
    progress_percentage: float = 0.0
    error_message: Optional[str] = None
    
    # File information
    output_filename: Optional[str] = None
    output_file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    
    # Tokuro AI data
    tokuro_ai_data: Optional[TokuroAIReportData] = None
    
    # Metadata
    generation_started_at: Optional[datetime] = None
    generation_completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None

class ReportGenerationRequest(BaseModel):
    """Request model for report generation"""
    name: str
    description: Optional[str] = None
    assessment_id: Optional[str] = None
    report_type: ReportType
    report_format: ReportFormat
    template_id: Optional[str] = None  # Use default if not provided
    include_tokuro_ai: bool = True
    include_executive_summary: bool = False
    include_remediation_plan: bool = False
    custom_branding: Dict[str, Any] = Field(default_factory=dict)

class ReportDownloadResponse(BaseModel):
    """Response model for report download"""
    report_id: str
    download_url: str
    filename: str
    file_size_bytes: int
    expires_at: datetime
    content_type: str

class ReportAnalytics(BaseModel):
    """Report generation analytics"""
    total_reports: int = 0
    reports_by_type: Dict[str, int] = Field(default_factory=dict)
    reports_by_format: Dict[str, int] = Field(default_factory=dict)
    reports_by_status: Dict[str, int] = Field(default_factory=dict)
    average_generation_time_seconds: float = 0.0
    tokuro_ai_usage_percentage: float = 0.0
    most_used_templates: List[Dict[str, Any]] = Field(default_factory=list)
    organization_report_count: Dict[str, int] = Field(default_factory=dict)

# ==================== EXISTING MODELS (Enhanced for Phase 4A) ====================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emergent_id: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    name: Optional[str] = None  # Legacy field support
    organization_id: str
    role: UserRole
    session_token: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Legacy fields for backward compatibility
    permissions: Optional[List[str]] = Field(default_factory=list)
    status: Optional[str] = "active"
    avatar: Optional[str] = None
    
    # Phase 4A: Report preferences
    report_preferences: Dict[str, Any] = Field(default_factory=dict)
    default_report_format: Optional[ReportFormat] = None
    
    def get_display_name(self) -> str:
        """Get the display name, preferring full_name over name"""
        return self.full_name or self.name or "Unknown User"

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Phase 4A: Organization branding for reports
    branding_config: Dict[str, Any] = Field(default_factory=dict)
    report_templates: List[str] = Field(default_factory=list)

class Assessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    organization_id: str
    created_by: str
    assigned_team: List[str] = []
    status: AssessmentStatus = AssessmentStatus.PLANNING
    framework: str = "NIST CSF 2.0"
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Phase 4A: Report generation tracking
    generated_reports: List[str] = Field(default_factory=list)  # Report IDs
    last_report_generated: Optional[datetime] = None

class RemediationTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: str
    status: str = "open"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    assigned_to: str
    assigned_by: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

class EscalationRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    user_id: str
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskMetrics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    metrics_data: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

class WorkflowState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    transitions: List[str] = Field(default_factory=list)

class ExecutiveSummaryReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    organization_id: str
    created_by: str
    summary_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ComplianceScorecard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    framework: str
    overall_score: float
    scores_by_category: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditTrailEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReportExportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str
    export_format: str
    status: str = "pending"
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReportSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    report_type: str
    schedule_pattern: str
    recipients: List[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StakeholderView(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExportRequest(BaseModel):
    report_id: str
    format: str
    include_attachments: bool = False

class ScheduleReportRequest(BaseModel):
    name: str
    report_type: str
    schedule_pattern: str
    recipients: List[str]

class ComplianceScorecardRequest(BaseModel):
    framework: str
    date_range: Optional[str] = None

class NISTFunction(BaseModel):
    id: str
    name: str
    description: str
    categories: List[str] = Field(default_factory=list)

class NISTCategory(BaseModel):
    id: str
    function_id: str
    name: str
    description: str
    subcategories: List[str] = Field(default_factory=list)

class NISTSubcategory(BaseModel):
    id: str
    category_id: str
    name: str
    description: str
    implementation_guidance: Optional[str] = None

class AIAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_file_id: str
    analysis_type: str
    confidence_score: float
    findings: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    framework_mappings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EvidenceFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str
    assessment_id: str
    uploaded_by: str
    processing_status: EvidenceStatus = EvidenceStatus.UPLOADED
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Tokuro AI analysis results (enhanced for Phase 4A reporting)
    tokuro_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    framework_mappings: List[str] = Field(default_factory=list)

class ControlAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str
    control_id: str
    status: ControlStatus = ControlStatus.NOT_STARTED
    implementation_score: int = 0  # 0-100
    effectiveness_score: int = 0   # 0-100
    maturity_score: int = 0        # 0-5
    overall_score: float = 0.0     # Calculated weighted score
    evidence_files: List[str] = []  # Evidence file IDs
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # AI analysis
    ai_confidence: Optional[float] = None
    ai_recommendations: List[str] = []

class DashboardMetrics(BaseModel):
    total_assessments: int
    active_assessments: int
    completed_assessments: int
    average_compliance_score: float
    critical_findings: int
    ai_analyses_performed: int
    framework_coverage: Dict[str, Any] = {}
    recent_activity: List[Dict[str, Any]] = []
    
    # Phase 4A: Report metrics
    total_reports_generated: int = 0
    reports_generated_this_month: int = 0

# ==================== REQUEST/RESPONSE MODELS ====================

class CreateAssessmentRequest(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_team: List[str] = []
    due_date: Optional[datetime] = None
    framework: str = "NIST CSF 2.0"

class AssessmentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: AssessmentStatus
    framework: str
    progress_percentage: float = 0.0
    created_at: datetime
    due_date: Optional[datetime] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class SessionValidationRequest(BaseModel):
    session_id: str

class EmergentAuthResponse(BaseModel):
    user: Dict[str, Any]
    organization: Dict[str, Any]

# ==================== PHASE 4A VALIDATORS ====================

def validate_report_format(cls, v):
    """Validate report format"""
    if v not in ReportFormat.__members__.values():
        raise ValueError(f'Invalid report format: {v}')
    return v

def validate_report_type(cls, v):
    """Validate report type"""
    if v not in ReportType.__members__.values():
        raise ValueError(f'Invalid report type: {v}')
    return v

# Validators are now defined inline with field_validator decorator in Pydantic v2
# The validation logic is handled by the enum types directly

# ==================== FRAMEWORK MANAGEMENT MODELS ====================

class ComplianceFramework(BaseModel):
    """Compliance framework model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    framework_type: str = "compliance"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FrameworkControl(BaseModel):
    """Framework control model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str
    title: str
    description: Optional[str] = None
    framework_id: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    implementation_guidance: Optional[str] = None
    assessment_procedures: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ControlMapping(BaseModel):
    """Control mapping between frameworks"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_framework_id: str
    source_control_id: str
    target_framework_id: str
    target_control_id: str
    mapping_type: str = "equivalent"  # equivalent, related, partial
    confidence_score: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AssessmentTemplate(BaseModel):
    """Assessment template model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    framework_id: str
    template_type: str = "standard"
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FrameworkUpload(BaseModel):
    """Framework upload model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_size: int
    upload_status: str = "pending"
    framework_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FrameworkUploadRequest(BaseModel):
    """Framework upload request"""
    name: str
    description: Optional[str] = None
    framework_type: str = "compliance"

class FrameworkListResponse(BaseModel):
    """Framework list response"""
    frameworks: List[ComplianceFramework]
    total_count: int

class ControlListResponse(BaseModel):
    """Control list response"""
    controls: List[FrameworkControl]
    total_count: int

class MappingRequest(BaseModel):
    """Control mapping request"""
    source_framework_id: str
    source_control_id: str
    target_framework_id: str
    target_control_id: str
    mapping_type: str = "equivalent"
    confidence_score: float = 1.0

class AssessmentTemplateRequest(BaseModel):
    """Assessment template request"""
    name: str
    description: Optional[str] = None
    framework_id: str
    template_type: str = "standard"

class FrameworkStatistics(BaseModel):
    """Framework statistics"""
    total_frameworks: int = 0
    active_frameworks: int = 0
    total_controls: int = 0
    total_mappings: int = 0
    recent_uploads: int = 0

class SystemOverview(BaseModel):
    """System overview"""
    frameworks: FrameworkStatistics
    assessments: Dict[str, int] = Field(default_factory=dict)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== PHASE 2C-A: RISK INTELLIGENCE MODELS ====================

class RiskScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str
    entity_id: str
    entity_name: str
    framework_id: Optional[str] = None
    overall_risk_score: float
    likelihood_score: float
    impact_score: float
    maturity_score: float
    evidence_quality_score: float
    framework_weight: float = 1.0
    risk_level: str
    risk_category: str = "operational"
    threat_vectors: List[str] = Field(default_factory=list)
    confidence_level: float = 0.85
    data_quality_score: float = 0.80
    calculation_method: str = "ai_weighted"
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    risk_indicators: List[Dict[str, Any]] = Field(default_factory=list)
    mitigation_factors: List[Dict[str, Any]] = Field(default_factory=list)
    calculated_by: str = "ai_engine"
    organization_id: str
    last_updated_trigger: str = "manual_calculation"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RiskFactor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    category: str
    impact: float
    likelihood: float
    trend: str = "stable"
    framework_relevance: Dict[str, float] = Field(default_factory=dict)

class RiskScoreHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str
    entity_type: str
    risk_score: float
    risk_level: str
    calculation_date: datetime = Field(default_factory=datetime.utcnow)
    calculation_method: str

class RiskThreshold(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    threshold_name: str
    description: Optional[str] = None
    threshold_type: str = "score_based"
    applies_to_entity_types: List[str] = Field(default_factory=list)
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: float = 95.0
    notification_recipients: List[str] = Field(default_factory=list)
    enable_notifications: bool = True
    is_active: bool = True
    created_by: str
    organization_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RiskAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str
    severity: str
    title: str
    description: str
    entity_type: str
    entity_id: str
    risk_score: float
    threshold_id: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

class RiskIntelligenceConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    default_thresholds: Dict[str, float] = Field(default_factory=dict)
    ai_analysis_enabled: bool = True
    update_frequency_hours: int = 24

class RiskAnalyticsSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    average_risk_score: float
    risk_score_distribution: Dict[str, int] = Field(default_factory=dict)
    top_risks: List[Dict[str, Any]] = Field(default_factory=list)
    trends: Dict[str, Any] = Field(default_factory=dict)

class RiskScoreCalculationRequest(BaseModel):
    entity_type: str
    entity_ids: Optional[List[str]] = None
    framework_id: Optional[str] = None
    calculation_mode: str = "comprehensive"

class RiskScoreResponse(BaseModel):
    risk_scores: List[RiskScore]
    calculation_metadata: Dict[str, Any]
    data_quality_assessment: Dict[str, Any]
    recommendations: List[str]

class RiskThresholdConfigRequest(BaseModel):
    threshold_name: str
    applies_to_entity_types: List[str]
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: Optional[float] = None
    notification_recipients: List[str]
    enable_notifications: bool = True

class RiskAlertSummaryResponse(BaseModel):
    alerts: List[RiskAlert]
    total_count: int
    severity_breakdown: Dict[str, int]
    last_updated: datetime

class RiskTrendAnalysisResponse(BaseModel):
    entity_type: str
    entity_id: str
    trend_period_days: int
    trend_direction: str
    trend_velocity: float
    historical_scores: List[Dict[str, Any]]
    trend_factors: List[Dict[str, Any]]
    predictions: Dict[str, Any]

class RiskIntelligenceDashboardResponse(BaseModel):
    overall_risk_index: float
    risk_trend: str
    critical_alerts_count: int
    risk_distribution: Dict[str, int]
    top_risk_entities: List[RiskScore]
    framework_risk_comparison: Dict[str, float]
    ai_insights: List[str]
