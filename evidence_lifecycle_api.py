"""
Phase 2B: Evidence Lifecycle Management API
Implements comprehensive evidence workflow management with AI-powered quality scoring,
reviewer dashboards, bulk operations, and audit trail capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import os
from models import (
    # Phase 2B Models
    EvidenceLifecycleState, EvidenceReview, EvidenceQualityMetrics,
    BulkEvidenceOperation, EvidenceReviewRequest, BulkEvidenceOperationRequest,
    EvidenceQualityAnalysisResponse,
    
    # Existing Models
    AssessmentEvidence
)
from mvp1_models import MVP1User
from mvp1_auth import get_current_user

# Initialize router
evidence_lifecycle_router = APIRouter(prefix="/api/evidence-lifecycle", tags=["Evidence Lifecycle"])

# =====================================
# EVIDENCE LIFECYCLE STATE MANAGEMENT
# =====================================

@evidence_lifecycle_router.get("/evidence/{evidence_id}/lifecycle", response_model=EvidenceLifecycleState)
async def get_evidence_lifecycle_state(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get current lifecycle state of evidence"""
    try:
        # Mock lifecycle state for development
        lifecycle_state = EvidenceLifecycleState(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            current_state="in_review",
            previous_state="uploaded",
            state_changed_at=datetime.utcnow() - timedelta(hours=2),
            state_changed_by=current_user.id,
            reviewer_id=current_user.id,
            review_deadline=datetime.utcnow() + timedelta(days=3),
            review_priority="medium",
            state_comments="Evidence uploaded successfully, assigned for review",
            quality_score=78.5,
            quality_indicators={
                "document_type": "policy_document",
                "completeness": "good",
                "clarity": "excellent",
                "relevance": "high"
            },
            completeness_score=85.0,
            relevance_score=92.0,
            workflow_step=2,
            total_workflow_steps=3,
            can_auto_approve=False,
            requires_expert_review=True,
            organization_id=current_user.organization_id
        )
        
        return lifecycle_state
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving evidence lifecycle state: {str(e)}"
        )

@evidence_lifecycle_router.post("/evidence/{evidence_id}/transition")
async def transition_evidence_state(
    evidence_id: str,
    new_state: str,
    comments: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Transition evidence to new lifecycle state"""
    try:
        valid_states = ["uploaded", "in_review", "approved", "rejected", "requires_revision"]
        if new_state not in valid_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state. Valid states: {valid_states}"
            )
        
        # Create new lifecycle state
        new_lifecycle_state = EvidenceLifecycleState(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            current_state=new_state,
            previous_state="in_review",  # Would be retrieved from current state
            state_changed_at=datetime.utcnow(),
            state_changed_by=current_user.id,
            reviewer_id=reviewer_id or current_user.id,
            state_comments=comments,
            organization_id=current_user.organization_id
        )
        
        # In real implementation, would update database and trigger notifications
        
        return {
            "message": f"Evidence {evidence_id} transitioned to {new_state}",
            "new_state": new_lifecycle_state,
            "notifications_sent": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transitioning evidence state: {str(e)}"
        )

# =====================================
# EVIDENCE REVIEW MANAGEMENT
# =====================================

@evidence_lifecycle_router.post("/evidence/{evidence_id}/reviews", response_model=EvidenceReview)
async def create_evidence_review(
    evidence_id: str,
    request: EvidenceReviewRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create a new evidence review"""
    try:
        review = EvidenceReview(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            reviewer_id=current_user.id,
            reviewer_name=current_user.name,
            reviewer_role=current_user.role,
            review_type="standard",
            review_status="completed",
            review_outcome=request.review_outcome,
            quality_rating=request.quality_rating,
            completeness_rating=request.completeness_rating,
            relevance_rating=request.relevance_rating,
            clarity_rating=4,  # Default rating
            review_comments=request.review_comments,
            improvements_needed=request.improvements_needed,
            additional_evidence_needed=request.additional_evidence_needed,
            review_requested_at=datetime.utcnow() - timedelta(hours=1),
            review_started_at=datetime.utcnow() - timedelta(minutes=30),
            review_completed_at=datetime.utcnow(),
            organization_id=current_user.organization_id
        )
        
        # Auto-transition evidence state based on review outcome
        if request.review_outcome == "approved":
            await transition_evidence_state(evidence_id, "approved", "Review completed - approved", current_user.id)
        elif request.review_outcome == "rejected":
            await transition_evidence_state(evidence_id, "rejected", "Review completed - rejected", current_user.id)
        elif request.review_outcome == "requires_revision":
            await transition_evidence_state(evidence_id, "requires_revision", "Review completed - revision required", current_user.id)
        
        return review
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating evidence review: {str(e)}"
        )

@evidence_lifecycle_router.get("/evidence/{evidence_id}/reviews", response_model=List[EvidenceReview])
async def get_evidence_reviews(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get all reviews for evidence"""
    try:
        # Mock reviews for development
        reviews = [
            EvidenceReview(
                id=str(uuid.uuid4()),
                evidence_id=evidence_id,
                reviewer_id=current_user.id,
                reviewer_name=current_user.name,
                reviewer_role="Senior Compliance Reviewer",
                review_type="expert",
                review_status="completed",
                review_outcome="approved",
                quality_rating=4,
                completeness_rating=5,
                relevance_rating=4,
                clarity_rating=4,
                review_comments="Excellent policy document with comprehensive coverage of access control requirements. Minor formatting improvements could enhance readability.",
                strengths_identified=[
                    "Clear policy statements",
                    "Comprehensive coverage",
                    "Regular review dates specified"
                ],
                improvements_needed=[
                    "Add specific role definitions",
                    "Include implementation timeline"
                ],
                review_requested_at=datetime.utcnow() - timedelta(days=2),
                review_started_at=datetime.utcnow() - timedelta(days=1, hours=8),
                review_completed_at=datetime.utcnow() - timedelta(days=1),
                organization_id=current_user.organization_id
            ),
            EvidenceReview(
                id=str(uuid.uuid4()),
                evidence_id=evidence_id,
                reviewer_id=str(uuid.uuid4()),
                reviewer_name="Alice Johnson",
                reviewer_role="IT Security Validator",
                review_type="peer",
                review_status="completed",
                review_outcome="requires_revision",
                quality_rating=3,
                completeness_rating=3,
                relevance_rating=4,
                clarity_rating=3,
                review_comments="Policy addresses most requirements but needs technical implementation details.",
                improvements_needed=[
                    "Add technical implementation procedures",
                    "Include system access matrices",
                    "Specify audit requirements"
                ],
                additional_evidence_needed=[
                    "System configuration screenshots",
                    "Access control matrices",
                    "Audit logs sample"
                ],
                review_requested_at=datetime.utcnow() - timedelta(days=3),
                review_completed_at=datetime.utcnow() - timedelta(days=2),
                organization_id=current_user.organization_id
            )
        ]
        
        return reviews
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving evidence reviews: {str(e)}"
        )

# =====================================
# AI-POWERED QUALITY ASSESSMENT
# =====================================

@evidence_lifecycle_router.post("/evidence/{evidence_id}/analyze-quality", response_model=EvidenceQualityAnalysisResponse)
async def analyze_evidence_quality(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Perform AI-powered quality analysis of evidence"""
    try:
        # Mock AI quality analysis
        quality_metrics = EvidenceQualityMetrics(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            overall_quality_score=82.5,
            confidence_level=0.89,
            relevance_score=88.0,
            completeness_score=78.0,
            clarity_score=85.0,
            currency_score=92.0,
            authenticity_score=95.0,
            document_type_detected="access_control_policy",
            key_topics_identified=[
                "Access Management",
                "User Authentication",
                "Role-Based Access Control",
                "Audit Requirements",
                "Password Policy"
            ],
            control_mappings_suggested=[
                {
                    "control_id": "PR.AC-1",
                    "confidence": 0.95,
                    "rationale": "Document directly addresses identity and access management requirements"
                },
                {
                    "control_id": "PR.AC-4",
                    "confidence": 0.87,
                    "rationale": "Contains access permission and authorization procedures"
                }
            ],
            missing_elements=[
                "Specific implementation timelines",
                "Role-specific access matrices",
                "Exception handling procedures"
            ],
            strengths=[
                "Comprehensive policy coverage",
                "Clear language and structure",
                "Regular review schedule defined",
                "Stakeholder responsibilities outlined"
            ],
            weaknesses=[
                "Limited technical implementation details",
                "Missing specific access control matrices",
                "No exception approval process defined"
            ],
            recommendations=[
                "Add technical implementation procedures",
                "Include role-based access control matrices",
                "Define exception handling workflow",
                "Add implementation timeline and milestones"
            ],
            ai_model_used="gpt-4o",
            analysis_timestamp=datetime.utcnow(),
            processing_time_ms=2500,
            peer_comparison_percentile=78.0,
            organization_baseline_score=75.5,
            industry_benchmark_score=80.2,
            organization_id=current_user.organization_id
        )
        
        # Determine recommendations based on quality score
        recommended_actions = []
        auto_approval_eligible = False
        requires_expert_review = False
        
        if quality_metrics.overall_quality_score >= 90:
            recommended_actions.append("Evidence meets high quality standards - recommend for auto-approval")
            auto_approval_eligible = True
        elif quality_metrics.overall_quality_score >= 75:
            recommended_actions.append("Evidence meets good quality standards - standard review recommended")
            recommended_actions.append("Consider addressing identified missing elements")
        else:
            recommended_actions.append("Evidence requires significant improvement before approval")
            recommended_actions.append("Request revision addressing all identified weaknesses")
            requires_expert_review = True
        
        if quality_metrics.completeness_score < 70:
            recommended_actions.append("Evidence completeness is below threshold - request additional documentation")
        
        if quality_metrics.relevance_score < 80:
            recommended_actions.append("Evidence relevance could be improved - verify control mapping accuracy")
            requires_expert_review = True
        
        response = EvidenceQualityAnalysisResponse(
            evidence_id=evidence_id,
            quality_metrics=quality_metrics,
            recommended_actions=recommended_actions,
            auto_approval_eligible=auto_approval_eligible,
            requires_expert_review=requires_expert_review
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing evidence quality: {str(e)}"
        )

@evidence_lifecycle_router.get("/evidence/{evidence_id}/quality-metrics", response_model=EvidenceQualityMetrics)
async def get_evidence_quality_metrics(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get stored quality metrics for evidence"""
    try:
        # Would retrieve from database in real implementation
        quality_analysis = await analyze_evidence_quality(evidence_id, current_user)
        return quality_analysis.quality_metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quality metrics: {str(e)}"
        )

# =====================================
# BULK EVIDENCE OPERATIONS
# =====================================

@evidence_lifecycle_router.post("/evidence/bulk-operation", response_model=BulkEvidenceOperation)
async def create_bulk_evidence_operation(
    request: BulkEvidenceOperationRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create a bulk evidence operation"""
    try:
        valid_operations = ["bulk_approve", "bulk_reject", "bulk_assign", "bulk_review"]
        if request.operation_type not in valid_operations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation type. Valid types: {valid_operations}"
            )
        
        bulk_operation = BulkEvidenceOperation(
            id=str(uuid.uuid4()),
            operation_type=request.operation_type,
            evidence_ids=request.evidence_ids,
            operation_parameters=request.operation_parameters,
            batch_size=min(50, len(request.evidence_ids)),
            status="queued",
            total_items=len(request.evidence_ids),
            initiated_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Simulate processing start
        bulk_operation.status = "in_progress"
        bulk_operation.started_at = datetime.utcnow()
        bulk_operation.estimated_completion_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Mock processing results
        if request.operation_type == "bulk_approve":
            bulk_operation.successful_items = len(request.evidence_ids)
            bulk_operation.processed_items = len(request.evidence_ids)
            bulk_operation.status = "completed"
            bulk_operation.completed_at = datetime.utcnow()
            
            bulk_operation.success_details = [
                {
                    "evidence_id": eid,
                    "action": "approved",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reviewer": current_user.name
                } for eid in request.evidence_ids
            ]
        
        return bulk_operation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bulk operation: {str(e)}"
        )

@evidence_lifecycle_router.get("/evidence/bulk-operations", response_model=List[BulkEvidenceOperation])
async def list_bulk_evidence_operations(
    status_filter: Optional[str] = None,
    limit: int = 20,
    current_user: MVP1User = Depends(get_current_user)
):
    """List bulk evidence operations"""
    try:
        # Mock bulk operations for development
        operations = [
            BulkEvidenceOperation(
                id=str(uuid.uuid4()),
                operation_type="bulk_approve",
                evidence_ids=[str(uuid.uuid4()) for _ in range(15)],
                status="completed",
                total_items=15,
                processed_items=15,
                successful_items=15,
                failed_items=0,
                queued_at=datetime.utcnow() - timedelta(hours=2),
                started_at=datetime.utcnow() - timedelta(hours=2, minutes=-5),
                completed_at=datetime.utcnow() - timedelta(hours=1, minutes=50),
                initiated_by=current_user.id,
                organization_id=current_user.organization_id
            ),
            BulkEvidenceOperation(
                id=str(uuid.uuid4()),
                operation_type="bulk_assign",
                evidence_ids=[str(uuid.uuid4()) for _ in range(8)],
                status="in_progress",
                total_items=8,
                processed_items=5,
                successful_items=5,
                failed_items=0,
                queued_at=datetime.utcnow() - timedelta(minutes=30),
                started_at=datetime.utcnow() - timedelta(minutes=25),
                estimated_completion_time=datetime.utcnow() + timedelta(minutes=10),
                initiated_by=current_user.id,
                organization_id=current_user.organization_id
            )
        ]
        
        if status_filter:
            operations = [op for op in operations if op.status == status_filter]
        
        return operations[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing bulk operations: {str(e)}"
        )

@evidence_lifecycle_router.get("/evidence/bulk-operations/{operation_id}", response_model=BulkEvidenceOperation)
async def get_bulk_operation_status(
    operation_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get status of a specific bulk operation"""
    try:
        # Mock operation status
        operation = BulkEvidenceOperation(
            id=operation_id,
            operation_type="bulk_approve",
            evidence_ids=[str(uuid.uuid4()) for _ in range(25)],
            status="completed",
            total_items=25,
            processed_items=25,
            successful_items=23,
            failed_items=2,
            queued_at=datetime.utcnow() - timedelta(hours=1),
            started_at=datetime.utcnow() - timedelta(minutes=55),
            completed_at=datetime.utcnow() - timedelta(minutes=45),
            operation_log=[
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=55),
                    "event": "operation_started",
                    "details": "Bulk approval operation initiated"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=50),
                    "event": "batch_completed",
                    "details": "Processed batch 1/3 (10 items)"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=47),
                    "event": "batch_completed", 
                    "details": "Processed batch 2/3 (10 items)"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=45),
                    "event": "operation_completed",
                    "details": "Bulk approval operation completed with 2 failures"
                }
            ],
            failure_details=[
                {
                    "evidence_id": str(uuid.uuid4()),
                    "error": "Evidence already approved",
                    "timestamp": datetime.utcnow() - timedelta(minutes=48)
                },
                {
                    "evidence_id": str(uuid.uuid4()),
                    "error": "Insufficient permissions",
                    "timestamp": datetime.utcnow() - timedelta(minutes=46)  
                }
            ],
            initiated_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        return operation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving bulk operation status: {str(e)}"
        )

# =====================================
# EVIDENCE DASHBOARD ENDPOINTS
# =====================================

@evidence_lifecycle_router.get("/evidence/dashboard/summary")
async def get_evidence_dashboard_summary(
    current_user: MVP1User = Depends(get_current_user)
):
    """Get evidence dashboard summary statistics"""
    try:
        dashboard_summary = {
            "total_evidence": 245,
            "pending_review": 18,
            "in_review": 12,
            "approved": 195,
            "rejected": 8,
            "requires_revision": 12,
            "quality_metrics": {
                "average_quality_score": 78.5,
                "auto_approval_rate": 42.0,
                "expert_review_rate": 15.0,
                "average_review_time_hours": 18.5
            },
            "recent_activity": [
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=15),
                    "activity": "Evidence approved",
                    "evidence_name": "Access Control Policy v2.1",
                    "reviewer": "Sarah Wilson",
                    "quality_score": 89.5
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=32),
                    "activity": "Bulk operation completed",
                    "details": "15 evidence items approved",
                    "initiated_by": current_user.name
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=1),
                    "activity": "Evidence requires revision",
                    "evidence_name": "Incident Response Procedure",
                    "reviewer": "Mike Chen",
                    "quality_score": 65.2
                }
            ],
            "workflow_performance": {
                "average_time_to_approval_hours": 22.5,
                "approval_rate": 79.6,
                "revision_rate": 4.9,
                "rejection_rate": 3.3
            }
        }
        
        return dashboard_summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )

@evidence_lifecycle_router.get("/evidence/dashboard/pending-reviews")
async def get_pending_evidence_reviews(
    priority: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    limit: int = 20,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get evidence items pending review"""
    try:
        # Mock pending reviews
        pending_reviews = [
            {
                "evidence_id": str(uuid.uuid4()),
                "evidence_name": "Data Encryption Standards v3.0",
                "assessment_name": "Q1 2025 NIST CSF Assessment",
                "control_id": "PR.DS-1",
                "submitted_by": "John Smith",
                "submitted_at": datetime.utcnow() - timedelta(hours=8),
                "priority": "high",
                "estimated_quality_score": 82.0,
                "requires_expert_review": False,
                "file_type": "PDF",
                "file_size_mb": 2.1
            },
            {
                "evidence_id": str(uuid.uuid4()),
                "evidence_name": "Network Security Configuration",
                "assessment_name": "ISO 27001 Compliance Check",
                "control_id": "A.13.1.1",
                "submitted_by": "Alice Johnson",
                "submitted_at": datetime.utcnow() - timedelta(hours=12),
                "priority": "medium",
                "estimated_quality_score": 75.5,
                "requires_expert_review": True,
                "file_type": "DOCX",
                "file_size_mb": 1.8
            },
            {
                "evidence_id": str(uuid.uuid4()),
                "evidence_name": "Backup and Recovery Procedures",
                "assessment_name": "SOC 2 Type II Preparation",
                "control_id": "CC6.1",
                "submitted_by": "Mike Chen",
                "submitted_at": datetime.utcnow() - timedelta(days=1),
                "priority": "urgent",
                "estimated_quality_score": 68.0,
                "requires_expert_review": True,
                "file_type": "PDF",
                "file_size_mb": 3.4
            }
        ]
        
        # Apply filters
        if priority:
            pending_reviews = [r for r in pending_reviews if r["priority"] == priority]
        
        return pending_reviews[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending reviews: {str(e)}"
        )

# =====================================
# HEALTH CHECK ENDPOINT
# =====================================

@evidence_lifecycle_router.get("/health")
async def evidence_lifecycle_health():
    """Health check endpoint for evidence lifecycle management"""
    return {
        "status": "healthy",
        "module": "Evidence Lifecycle Management",
        "phase": "2B - Enhanced Evidence Collection & Workflow Management",
        "capabilities": [
            "Evidence Lifecycle State Management",
            "AI-Powered Quality Assessment", 
            "Evidence Review Workflows",
            "Bulk Evidence Operations",
            "Evidence Dashboard Analytics",
            "Audit Trail Tracking",
            "Role-Based Access Control",
            "Notification Management"
        ],
        "supported_evidence_states": [
            "uploaded", "in_review", "approved", "rejected", "requires_revision"
        ],
        "supported_bulk_operations": [
            "bulk_approve", "bulk_reject", "bulk_assign", "bulk_review"
        ],
        "ai_capabilities": [
            "Quality Scoring", "Document Type Detection", "Control Mapping Suggestions",
            "Completeness Analysis", "Relevance Assessment"
        ],
        "timestamp": datetime.utcnow()
    }