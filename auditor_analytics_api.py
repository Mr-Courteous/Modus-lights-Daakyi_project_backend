"""
Auditor Analytics API
Backend API endpoints for auditor-specific analytics and review insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from database import get_database
from mvp1_auth import get_current_user

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/analytics/auditor", tags=["auditor-analytics"])

# Pydantic models for request/response
class AuditProgressResponse(BaseModel):
    framework: str
    total_controls: int
    reviewed: int
    approved: int
    pending: int
    rejected: int
    completion_rate: int
    avg_review_time: float

class RiskAssessmentDataResponse(BaseModel):
    date: str
    critical: int
    high: int
    medium: int
    low: int
    total: int

class EvidenceQualityResponse(BaseModel):
    name: str
    value: int
    percentage: float
    color: str

class ComplianceGapResponse(BaseModel):
    area: str
    identified: int
    resolved: int
    remaining: int
    severity: str
    completion_percentage: float

class ReviewTimelineResponse(BaseModel):
    day: str
    reviews_completed: int
    avg_review_time: float
    quality_score: float

class ValidationMetricResponse(BaseModel):
    metric: str
    current: float
    target: float
    trend: str
    unit: Optional[str] = None

class AuditFindingResponse(BaseModel):
    month: str
    new_findings: int
    resolved_findings: int
    carryover_findings: int

class AuditPerformanceSummaryResponse(BaseModel):
    total_audits_completed: int
    average_completion_time: float
    client_satisfaction_score: float
    findings_accuracy_rate: float
    on_time_delivery_rate: float
    recommendation_implementation_rate: float

@router.get("/audit-progress", response_model=List[AuditProgressResponse])
async def get_audit_progress(
    framework_filter: Optional[str] = Query(None, description="Filter by specific framework"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get audit progress tracking by framework"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock audit progress data
        audit_progress = [
            AuditProgressResponse(
                framework="ISO 27001",
                total_controls=114,
                reviewed=89,
                approved=76,
                pending=13,
                rejected=25,
                completion_rate=78,
                avg_review_time=2.3
            ),
            AuditProgressResponse(
                framework="SOC 2 Type II",
                total_controls=64,
                reviewed=52,
                approved=48,
                pending=4,
                rejected=8,
                completion_rate=81,
                avg_review_time=1.8
            ),
            AuditProgressResponse(
                framework="NIST CSF",
                total_controls=108,
                reviewed=94,
                approved=87,
                pending=7,
                rejected=14,
                completion_rate=87,
                avg_review_time=2.1
            ),
            AuditProgressResponse(
                framework="GDPR",
                total_controls=99,
                reviewed=71,
                approved=62,
                pending=9,
                rejected=19,
                completion_rate=72,
                avg_review_time=2.7
            ),
            AuditProgressResponse(
                framework="PCI DSS",
                total_controls=78,
                reviewed=58,
                approved=51,
                pending=7,
                rejected=13,
                completion_rate=74,
                avg_review_time=2.4
            )
        ]

        # Apply framework filter if provided
        if framework_filter:
            audit_progress = [ap for ap in audit_progress if ap.framework.lower() == framework_filter.lower()]

        return audit_progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit progress")

@router.get("/risk-assessment", response_model=List[RiskAssessmentDataResponse])
async def get_risk_assessment_data(
    days: Optional[int] = Query(30, description="Number of days to include"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get risk assessment trends over time"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock risk assessment data
        risk_data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            total = max(20, int(35 + (i % 10) * 2))  # Vary risk count
            
            risk_data.append(RiskAssessmentDataResponse(
                date=current_date.strftime('%Y-%m-%d'),
                critical=int(total * 0.12),
                high=int(total * 0.28),
                medium=int(total * 0.45),
                low=int(total * 0.15),
                total=total
            ))

        return risk_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk assessment data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk assessment data")

@router.get("/evidence-quality", response_model=List[EvidenceQualityResponse])
async def get_evidence_quality(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get evidence quality distribution"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock evidence quality data
        evidence_quality = [
            EvidenceQualityResponse(
                name="Excellent (95-100%)",
                value=142,
                percentage=28.0,
                color="var(--daakyi-success)"
            ),
            EvidenceQualityResponse(
                name="Good (85-94%)",
                value=289,
                percentage=57.0,
                color="var(--daakyi-primary)"
            ),
            EvidenceQualityResponse(
                name="Fair (75-84%)",
                value=67,
                percentage=13.0,
                color="var(--daakyi-accent)"
            ),
            EvidenceQualityResponse(
                name="Poor (<75%)",
                value=12,
                percentage=2.0,
                color="var(--daakyi-error)"
            )
        ]

        return evidence_quality

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching evidence quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch evidence quality")

@router.get("/compliance-gaps", response_model=List[ComplianceGapResponse])
async def get_compliance_gaps(
    severity_filter: Optional[str] = Query(None, description="Filter by severity level"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get compliance gap analysis by control area"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock compliance gaps data
        compliance_gaps = [
            ComplianceGapResponse(
                area="Access Management",
                identified=23,
                resolved=18,
                remaining=5,
                severity="Medium",
                completion_percentage=78.3
            ),
            ComplianceGapResponse(
                area="Data Protection",
                identified=31,
                resolved=22,
                remaining=9,
                severity="High",
                completion_percentage=71.0
            ),
            ComplianceGapResponse(
                area="Network Security",
                identified=18,
                resolved=15,
                remaining=3,
                severity="Low",
                completion_percentage=83.3
            ),
            ComplianceGapResponse(
                area="Incident Response",
                identified=27,
                resolved=19,
                remaining=8,
                severity="High",
                completion_percentage=70.4
            ),
            ComplianceGapResponse(
                area="Risk Assessment",
                identified=15,
                resolved=14,
                remaining=1,
                severity="Low",
                completion_percentage=93.3
            ),
            ComplianceGapResponse(
                area="Business Continuity",
                identified=22,
                resolved=16,
                remaining=6,
                severity="Medium",
                completion_percentage=72.7
            ),
            ComplianceGapResponse(
                area="Vendor Management",
                identified=19,
                resolved=11,
                remaining=8,
                severity="Critical",
                completion_percentage=57.9
            )
        ]

        # Apply severity filter if provided
        if severity_filter:
            compliance_gaps = [cg for cg in compliance_gaps if cg.severity.lower() == severity_filter.lower()]

        return compliance_gaps

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching compliance gaps: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch compliance gaps")

@router.get("/review-timeline", response_model=List[ReviewTimelineResponse])
async def get_review_timeline(
    days: Optional[int] = Query(7, description="Number of days to include"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get review timeline and workflow efficiency"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock review timeline data
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        review_timeline = []
        for i in range(days):
            day_name = days_of_week[i % 7]
            reviews = max(15, int(28 + (i % 5) * 3))
            
            review_timeline.append(ReviewTimelineResponse(
                day=day_name,
                reviews_completed=reviews,
                avg_review_time=1.5 + (i % 3) * 0.3,
                quality_score=85.0 + (i % 4) * 2.5
            ))

        return review_timeline[:days]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch review timeline")

@router.get("/validation-metrics", response_model=List[ValidationMetricResponse])
async def get_validation_metrics(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get validation and accuracy metrics"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock validation metrics
        validation_metrics = [
            ValidationMetricResponse(
                metric="Review Accuracy",
                current=94.0,
                target=95.0,
                trend="stable",
                unit="%"
            ),
            ValidationMetricResponse(
                metric="False Positive Rate",
                current=3.2,
                target=2.0,
                trend="down",
                unit="%"
            ),
            ValidationMetricResponse(
                metric="Evidence Validation Speed",
                current=2.1,
                target=1.8,
                trend="up",
                unit="days"
            ),
            ValidationMetricResponse(
                metric="Control Coverage",
                current=89.0,
                target=92.0,
                trend="up",
                unit="%"
            ),
            ValidationMetricResponse(
                metric="Risk Identification Rate",
                current=96.0,
                target=98.0,
                trend="up",
                unit="%"
            ),
            ValidationMetricResponse(
                metric="Audit Efficiency Score",
                current=87.0,
                target=90.0,
                trend="stable",
                unit="%"
            )
        ]

        return validation_metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching validation metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch validation metrics")

@router.get("/audit-findings", response_model=List[AuditFindingResponse])
async def get_audit_findings(
    months: Optional[int] = Query(12, description="Number of months to include"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get audit findings breakdown over time"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock audit findings data
        months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        audit_findings = []
        
        for i in range(months):
            month_name = months_names[i % 12]
            new_findings = max(25, int(45 + (i % 6) * 5))
            
            audit_findings.append(AuditFindingResponse(
                month=month_name,
                new_findings=new_findings,
                resolved_findings=int(new_findings * 0.75),
                carryover_findings=int(new_findings * 0.25)
            ))

        return audit_findings[:months]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit findings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit findings")

@router.get("/performance-summary", response_model=AuditPerformanceSummaryResponse)
async def get_performance_summary(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get overall auditor performance summary"""
    try:
        # Validate auditor access
        if not current_user or current_user.get('role') not in ['admin', 'auditor']:
            raise HTTPException(status_code=403, detail="Auditor access required")

        # Mock performance summary
        performance_summary = AuditPerformanceSummaryResponse(
            total_audits_completed=127,
            average_completion_time=4.2,
            client_satisfaction_score=4.7,
            findings_accuracy_rate=94.2,
            on_time_delivery_rate=96.8,
            recommendation_implementation_rate=87.3
        )

        return performance_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance summary")

@router.get("/health")
async def health_check():
    """Health check endpoint for auditor analytics API"""
    return {
        "status": "healthy",
        "service": "Auditor Analytics API",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "audit_progress_tracking",
            "risk_assessment_analytics",
            "evidence_quality_analysis", 
            "compliance_gap_monitoring",
            "review_timeline_insights",
            "validation_metrics_reporting",
            "audit_findings_trends",
            "performance_summary_analytics",
            "auditor_role_access_control"
        ]
    }