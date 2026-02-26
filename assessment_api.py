"""
Phase 2A: Control Assessment Engine Core API
Implements comprehensive assessment lifecycle management with dynamic form generation,
conditional logic, flexible scoring, and multi-level review workflows.
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import math
from models import (
    # Phase 2A Models
    AssessmentConfiguration, AssessmentEngine, AssessmentQuestion,
    AssessmentResponse, AssessmentEvidence, AssessmentReview, AssessmentNotification,
    CreateAssessmentRequest, AssessmentListResponse, AssessmentDetailResponse,
    SubmitResponseRequest, AssessmentProgressResponse,
    
    # Existing Models
    User, ComplianceFramework, FrameworkControl
)
from auth import get_current_user

# Initialize router
assessment_router = APIRouter()

# =====================================
# ASSESSMENT CONFIGURATION ENDPOINTS
# =====================================

@assessment_router.get("/configurations", response_model=List[AssessmentConfiguration])
async def list_assessment_configurations(
    current_user: User = Depends(get_current_user)
):
    """List all assessment configurations for the organization"""
    try:
        # Mock configurations for development
        configurations = [
            AssessmentConfiguration(
                id=str(uuid.uuid4()),
                name="Standard Risk Assessment",
                description="Default configuration for self-assessments with balanced scoring",
                scoring_weights={
                    "high_priority": 1.5,
                    "medium_priority": 1.0,
                    "low_priority": 0.7
                },
                scoring_formula="weighted_average",
                risk_thresholds={
                    "high_risk": 60.0,
                    "medium_risk": 80.0,
                    "low_risk": 100.0
                },
                conditional_logic_enabled=True,
                logic_rules=[
                    {
                        "if": {"==": [{"var": "implementation_status"}, "Partially Implemented"]},
                        "then": {"show": ["evidence_upload", "justification_text"]},
                        "else": {"show": ["evidence_upload"]}
                    }
                ],
                created_by=current_user.id,
                organization_id=current_user.organization_id,
                is_default=True
            ),
            AssessmentConfiguration(
                id=str(uuid.uuid4()),
                name="External Audit Preparation",
                description="Stricter configuration for external audit readiness",
                scoring_weights={
                    "critical": 2.0,
                    "high_priority": 1.8,
                    "medium_priority": 1.2,
                    "low_priority": 0.8
                },
                scoring_formula="weighted_average",
                risk_thresholds={
                    "high_risk": 70.0,
                    "medium_risk": 85.0,
                    "low_risk": 100.0
                },
                conditional_logic_enabled=True,
                logic_rules=[
                    {
                        "if": {"and": [
                            {"==": [{"var": "implementation_status"}, "Not Implemented"]},
                            {"==": [{"var": "priority_level"}, "High"]}
                        ]},
                        "then": {"require": ["remediation_plan", "timeline", "evidence"]},
                        "else": {"show": ["evidence_upload"]}
                    }
                ],
                created_by=current_user.id,
                organization_id=current_user.organization_id,
                is_default=False
            )
        ]
        
        return configurations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment configurations: {str(e)}"
        )

# =====================================
# ASSESSMENT CRUD ENDPOINTS
# =====================================

@assessment_router.post("/assessments", response_model=AssessmentEngine)
async def create_assessment(
    request: CreateAssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new assessment"""
    try:
        # Get framework information (mock for development)
        framework_name = "NIST CSF 2.0"  # Default for now
        
        # Create assessment
        assessment = AssessmentEngine(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            framework_id=request.framework_id,
            framework_name=framework_name,
            configuration_id=str(uuid.uuid4()),  # Use default configuration
            assessment_type=request.assessment_type,
            status="draft",
            business_units=request.business_units,
            owner_id=current_user.id,
            participants=request.participants,
            reviewers=request.reviewers,
            due_date=request.due_date,
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Generate dynamic questions for the assessment
        questions = await generate_assessment_questions(assessment.id, request.framework_id)
        assessment.total_questions = len(questions)
        
        return assessment
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assessment: {str(e)}"
        )

@assessment_router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List assessments with pagination and filtering"""
    try:
        # Mock assessments for development
        all_assessments = [
            AssessmentEngine(
                id=str(uuid.uuid4()),
                name="Q1 2025 NIST CSF Self-Assessment",
                description="Quarterly self-assessment for NIST Cybersecurity Framework compliance",
                framework_id="nist-csf-v2",
                framework_name="NIST CSF 2.0",
                configuration_id=str(uuid.uuid4()),
                assessment_type="self_assessment",
                status="in_progress",
                business_units=["IT", "Security", "Compliance"],
                owner_id=current_user.id,
                participants=[current_user.id],
                reviewers=[current_user.id],
                start_date=datetime.utcnow() - timedelta(days=5),
                due_date=datetime.utcnow() + timedelta(days=25),
                total_questions=45,
                answered_questions=22,
                completion_percentage=48.9,
                overall_score=67.5,
                risk_level="medium",
                compliance_status="partially_compliant",
                created_by=current_user.id,
                organization_id=current_user.organization_id
            ),
            AssessmentEngine(
                id=str(uuid.uuid4()),
                name="ISO 27001 Annual Assessment",
                description="Annual comprehensive assessment for ISO 27001:2022 certification",
                framework_id="iso-27001-2022",
                framework_name="ISO 27001:2022",
                configuration_id=str(uuid.uuid4()),
                assessment_type="external_audit",
                status="draft",
                business_units=["IT", "HR", "Finance"],
                owner_id=current_user.id,
                participants=[current_user.id],
                reviewers=[current_user.id],
                due_date=datetime.utcnow() + timedelta(days=60),
                total_questions=39,
                answered_questions=0,
                completion_percentage=0.0,
                compliance_status="unknown",
                created_by=current_user.id,
                organization_id=current_user.organization_id
            ),
            AssessmentEngine(
                id=str(uuid.uuid4()),
                name="SOC 2 Type II Readiness",
                description="Preparation assessment for SOC 2 Type II audit",
                framework_id="soc2-tsc",
                framework_name="SOC 2",
                configuration_id=str(uuid.uuid4()),
                assessment_type="compliance_check",
                status="completed",
                business_units=["IT", "Operations"],
                owner_id=current_user.id,
                participants=[current_user.id],
                reviewers=[current_user.id],
                start_date=datetime.utcnow() - timedelta(days=30),
                due_date=datetime.utcnow() - timedelta(days=5),
                completion_date=datetime.utcnow() - timedelta(days=3),
                total_questions=25,
                answered_questions=25,
                completion_percentage=100.0,
                overall_score=85.2,
                risk_level="low",
                compliance_status="compliant",
                created_by=current_user.id,
                organization_id=current_user.organization_id
            )
        ]
        
        # Apply status filter if provided
        if status_filter:
            all_assessments = [a for a in all_assessments if a.status == status_filter]
        
        # Apply pagination
        total_count = len(all_assessments)
        total_pages = math.ceil(total_count / page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        assessments = all_assessments[start_idx:end_idx]
        
        return AssessmentListResponse(
            assessments=assessments,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessments: {str(e)}"
        )

@assessment_router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment_details(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed assessment information including questions and responses"""
    try:
        # Mock assessment details
        assessment = AssessmentEngine(
            id=assessment_id,
            name="Q1 2025 NIST CSF Self-Assessment",
            description="Quarterly self-assessment for NIST Cybersecurity Framework compliance",
            framework_id="nist-csf-v2",
            framework_name="NIST CSF 2.0",
            configuration_id=str(uuid.uuid4()),
            assessment_type="self_assessment",
            status="in_progress",
            business_units=["IT", "Security", "Compliance"],
            owner_id=current_user.id,
            participants=[current_user.id],
            reviewers=[current_user.id],
            start_date=datetime.utcnow() - timedelta(days=5),
            due_date=datetime.utcnow() + timedelta(days=25),
            total_questions=45,
            answered_questions=22,
            completion_percentage=48.9,
            overall_score=67.5,
            risk_level="medium",
            compliance_status="partially_compliant",
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Generate questions and responses
        questions = await generate_assessment_questions(assessment_id, assessment.framework_id)
        responses = await get_assessment_responses(assessment_id)
        
        progress_summary = {
            "sections": {
                "Identity & Access Management": {"completed": 8, "total": 12, "percentage": 66.7},
                "Data Protection": {"completed": 6, "total": 10, "percentage": 60.0},
                "Incident Response": {"completed": 4, "total": 8, "percentage": 50.0},
                "Risk Management": {"completed": 4, "total": 15, "percentage": 26.7}
            },
            "recent_activity": [
                {"timestamp": datetime.utcnow() - timedelta(hours=2), "activity": "Response submitted for PR.AC-1"},
                {"timestamp": datetime.utcnow() - timedelta(hours=4), "activity": "Evidence uploaded for ID.AM-1"},
                {"timestamp": datetime.utcnow() - timedelta(days=1), "activity": "Assessment started"}
            ]
        }
        
        return AssessmentDetailResponse(
            assessment=assessment,
            questions=questions[:10],  # Limit for demo
            responses=responses[:10],   # Limit for demo
            progress_summary=progress_summary,
            review_status=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment details: {str(e)}"
        )

@assessment_router.put("/assessments/{assessment_id}")
async def update_assessment(
    assessment_id: str,
    request: CreateAssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing assessment"""
    try:
        # Mock update - in real implementation, would update database
        updated_assessment = AssessmentEngine(
            id=assessment_id,
            name=request.name,
            description=request.description,
            framework_id=request.framework_id,
            framework_name="NIST CSF 2.0",  # Would be fetched from DB
            configuration_id=str(uuid.uuid4()),
            assessment_type=request.assessment_type,
            status="draft",  # Would preserve existing status
            business_units=request.business_units,
            owner_id=current_user.id,
            participants=request.participants,
            reviewers=request.reviewers,
            due_date=request.due_date,
            created_by=current_user.id,
            updated_by=current_user.id,
            updated_at=datetime.utcnow(),
            organization_id=current_user.organization_id
        )
        
        return {"message": "Assessment updated successfully", "assessment": updated_assessment}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating assessment: {str(e)}"
        )

@assessment_router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an assessment"""
    try:
        # In real implementation, would delete from database
        return {"message": f"Assessment {assessment_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting assessment: {str(e)}"
        )

# =====================================
# DYNAMIC FORM AND QUESTION ENDPOINTS
# =====================================

@assessment_router.get("/assessments/{assessment_id}/questions", response_model=List[AssessmentQuestion])
async def get_assessment_questions(
    assessment_id: str,
    section: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get questions for an assessment, optionally filtered by section"""
    try:
        questions = await generate_assessment_questions(assessment_id, "nist-csf-v2")
        
        if section:
            questions = [q for q in questions if q.section == section]
        
        return questions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment questions: {str(e)}"
        )

@assessment_router.post("/assessments/{assessment_id}/responses")
async def submit_assessment_response(
    assessment_id: str,
    request: SubmitResponseRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit a response to an assessment question"""
    try:
        # Create response
        response = AssessmentResponse(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            question_id=request.question_id,
            control_id="PR.AC-1",  # Would be determined from question
            response_value=request.response_value,
            response_data=request.response_data,
            response_type="multiple_choice",  # Would match question type
            is_complete=True,
            confidence_level=request.confidence_level,
            comments=request.comments,
            status="submitted",
            respondent_id=current_user.id,
            respondent_name=current_user.name,
            respondent_role=current_user.role,
            submitted_at=datetime.utcnow()
        )
        
        # Calculate response score (mock scoring logic)
        response.response_score = calculate_response_score(response)
        
        return {"message": "Response submitted successfully", "response": response}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting response: {str(e)}"
        )

@assessment_router.get("/assessments/{assessment_id}/progress", response_model=AssessmentProgressResponse)
async def get_assessment_progress(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed progress information for an assessment"""
    try:
        progress = AssessmentProgressResponse(
            assessment_id=assessment_id,
            total_questions=45,
            answered_questions=22,
            completion_percentage=48.9,
            sections_progress={
                "Identity & Access Management": {
                    "completed": 8,
                    "total": 12,
                    "percentage": 66.7,
                    "status": "in_progress"
                },
                "Data Protection": {
                    "completed": 6,
                    "total": 10,
                    "percentage": 60.0,
                    "status": "in_progress"
                },
                "Incident Response": {
                    "completed": 4,
                    "total": 8,
                    "percentage": 50.0,
                    "status": "in_progress"
                },
                "Risk Management": {
                    "completed": 4,
                    "total": 15,
                    "percentage": 26.7,
                    "status": "not_started"
                }
            },
            recent_activity=[
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=2),
                    "activity": "Response submitted for PR.AC-1",
                    "user": current_user.name,
                    "type": "response"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=4),
                    "activity": "Evidence uploaded for ID.AM-1",
                    "user": current_user.name,
                    "type": "evidence"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(days=1),
                    "activity": "Assessment started",
                    "user": current_user.name,
                    "type": "status_change"
                }
            ]
        )
        
        return progress
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment progress: {str(e)}"
        )

# =====================================
# EVIDENCE MANAGEMENT ENDPOINTS
# =====================================

@assessment_router.post("/assessments/{assessment_id}/evidence")
async def upload_assessment_evidence(
    assessment_id: str,
    response_id: str,
    file: UploadFile = File(...),
    evidence_type: str = "other",
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Upload evidence for an assessment response"""
    try:
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        # Create evidence record
        evidence = AssessmentEvidence(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            response_id=response_id,
            control_id="PR.AC-1",  # Would be determined from response
            filename=f"{uuid.uuid4()}_{file.filename}",
            original_filename=file.filename,
            file_path=f"/evidence/{assessment_id}/{uuid.uuid4()}_{file.filename}",
            file_size=file.size,
            file_type=file.filename.split('.')[-1].lower(),
            mime_type=file.content_type,
            evidence_type=evidence_type,
            description=description,
            validation_status="valid",
            processing_status="processed",
            uploaded_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # In real implementation, would save file to S3/local storage
        
        return {"message": "Evidence uploaded successfully", "evidence": evidence}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading evidence: {str(e)}"
        )

# =====================================
# REVIEW WORKFLOW ENDPOINTS
# =====================================

@assessment_router.post("/assessments/{assessment_id}/reviews")
async def request_assessment_review(
    assessment_id: str,
    reviewers: List[str],
    review_type: str = "standard",
    due_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Request review for an assessment"""
    try:
        review = AssessmentReview(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            review_type=review_type,
            status="pending",
            assigned_reviewers=reviewers,
            review_due_date=due_date or datetime.utcnow() + timedelta(days=7),
            requested_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # In real implementation, would send notifications to reviewers
        
        return {"message": "Review requested successfully", "review": review}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error requesting review: {str(e)}"
        )

# =====================================
# UTILITY FUNCTIONS
# =====================================

async def generate_assessment_questions(assessment_id: str, framework_id: str) -> List[AssessmentQuestion]:
    """Generate dynamic questions based on framework and conditional logic"""
    
    # Mock questions for development
    questions = [
        AssessmentQuestion(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            control_id="PR.AC-1",
            question_text="How is access to your organization's systems and data managed?",
            question_type="multiple_choice",
            help_text="Select the option that best describes your current access management practices.",
            is_required=True,
            display_order=1,
            section="Identity & Access Management",
            options=[
                {"value": "fully_implemented", "label": "Fully Implemented", "score": 4},
                {"value": "largely_implemented", "label": "Largely Implemented", "score": 3},
                {"value": "partially_implemented", "label": "Partially Implemented", "score": 2},
                {"value": "not_implemented", "label": "Not Implemented", "score": 0}
            ],
            visibility_conditions={"always": True},
            validation_rules={"required": True}
        ),
        AssessmentQuestion(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            control_id="PR.AC-1",
            question_text="Please provide evidence of your access management procedures.",
            question_type="file_upload",
            help_text="Upload policies, procedures, or documentation that demonstrates access management.",
            is_required=False,
            display_order=2,
            section="Identity & Access Management",
            allowed_file_types=["pdf", "docx", "xlsx"],
            max_file_size_mb=10,
            max_files=3,
            visibility_conditions={
                "if": {"in": [{"var": "PR.AC-1"}, ["partially_implemented", "largely_implemented", "fully_implemented"]]}
            }
        ),
        AssessmentQuestion(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            control_id="PR.DS-1",
            question_text="Rate the effectiveness of your data protection measures.",
            question_type="scale",
            help_text="Rate from 1 (Ineffective) to 5 (Highly Effective)",
            is_required=True,
            display_order=3,
            section="Data Protection",
            scale_min=1,
            scale_max=5,
            scale_labels={"1": "Ineffective", "2": "Poor", "3": "Fair", "4": "Good", "5": "Excellent"}
        )
    ]
    
    return questions

async def get_assessment_responses(assessment_id: str) -> List[AssessmentResponse]:
    """Get existing responses for an assessment"""
    
    # Mock responses for development
    responses = [
        AssessmentResponse(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            question_id=str(uuid.uuid4()),
            control_id="PR.AC-1",
            response_value="largely_implemented",
            response_type="multiple_choice",
            is_complete=True,
            confidence_level=4,
            comments="We have documented procedures but some legacy systems need updates.",
            status="submitted",
            response_score=3.0,
            respondent_id="user123",
            respondent_name="John Doe",
            respondent_role="System Administrator",
            submitted_at=datetime.utcnow() - timedelta(hours=2)
        )
    ]
    
    return responses

def calculate_response_score(response: AssessmentResponse) -> float:
    """Calculate score for an individual response"""
    
    # Mock scoring logic - in real implementation would be more sophisticated
    if response.response_type == "multiple_choice":
        if response.response_value == "fully_implemented":
            return 4.0
        elif response.response_value == "largely_implemented":
            return 3.0
        elif response.response_value == "partially_implemented":
            return 2.0
        else:
            return 0.0
    elif response.response_type == "scale":
        try:
            return float(response.response_value)
        except:
            return 0.0
    
    return 0.0

def apply_conditional_logic(questions: List[AssessmentQuestion], responses: Dict[str, Any]) -> List[AssessmentQuestion]:
    """Apply conditional logic to show/hide questions based on responses"""
    
    # Mock conditional logic - in real implementation would use JSON Logic
    visible_questions = []
    
    for question in questions:
        if question.visibility_conditions.get("always"):
            visible_questions.append(question)
        elif "if" in question.visibility_conditions:
            # Simplified logic evaluation
            condition = question.visibility_conditions["if"]
            # In real implementation, would use proper JSON Logic library
            visible_questions.append(question)
    
    return visible_questions

# =====================================
# HEALTH CHECK ENDPOINT
# =====================================

@assessment_router.get("/health")
async def assessment_engine_health():
    """Health check endpoint for assessment engine"""
    return {
        "status": "healthy",
        "module": "Assessment Engine",
        "phase": "2A - Control Assessment Engine Core",
        "capabilities": [
            "Assessment Creation & Management",
            "Dynamic Form Generation", 
            "Conditional Logic Processing",
            "Flexible Scoring Configuration",
            "Evidence Management",
            "Multi-level Review Workflows",
            "Progress Tracking",
            "Notification System"
        ],
        "supported_question_types": [
            "text", "multiple_choice", "yes_no", "scale", 
            "file_upload", "date", "checkbox"
        ],
        "supported_evidence_types": [
            "policy", "procedure", "screenshot", "log", 
            "certificate", "other"
        ],
        "timestamp": datetime.utcnow()
    }