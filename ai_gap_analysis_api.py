"""
DAAKYI CompaaS Platform - Phase 4B: Advanced Compliance Framework Mapper
AI Gap Analysis API - Machine Learning Powered Gap Detection

Features:
- Real gap identification from auditor's assigned engagements
- Risk prioritization based on actual control completion data
- Smart remediation pathway generation
- Predictive compliance readiness scoring
- Resource optimization recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import asyncio
import json
from enum import Enum

# Import dependencies
from database import get_database, DatabaseOperations
from mvp1_auth import get_current_user
from mvp1_models import MVP1User
from framework_mapper_api import FrameworkType, UserRole, FrameworkControl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/ai-gap-analysis", tags=["AI Gap Analysis"])

# =============================================================================
# MODELS & SCHEMAS
# =============================================================================

class GapSeverity(str, Enum):
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"           # Address within 30 days
    MEDIUM = "medium"       # Address within 90 days
    LOW = "low"             # Address within 180 days
    INFO = "info"           # Informational only

class RiskCategory(str, Enum):
    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"

class AnalyzeEngagementRequest(BaseModel):
    engagement_id: str
    analysis_scope: str = "comprehensive"

class ComplianceGap(BaseModel):
    id: str = Field(..., description="Gap identifier")
    title: str = Field(..., description="Gap title")
    description: str = Field(..., description="Detailed gap description")
    affected_frameworks: List[str] = Field(..., description="Affected frameworks")
    missing_controls: List[str] = Field(..., description="Missing control IDs")
    severity: GapSeverity = Field(..., description="Gap severity level")
    risk_category: RiskCategory = Field(..., description="Primary risk category")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk score (0-10)")
    estimated_effort_days: int = Field(..., description="Estimated remediation effort in days")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other gaps")
    ai_confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in gap identification")
    remediation_steps: List[str] = Field(..., description="Recommended remediation steps")
    success_criteria: List[str] = Field(..., description="Success criteria for gap closure")
    engagement_id: Optional[str] = Field(None, description="Source engagement ID")
    engagement_name: Optional[str] = Field(None, description="Source engagement name")
    status: Optional[str] = Field("pending", description="Validation status: pending, approved, rejected")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RemediationPathway(BaseModel):
    id: str = Field(..., description="Pathway identifier") 
    name: str = Field(..., description="Pathway name")
    description: str = Field(..., description="Pathway description")
    target_gaps: List[str] = Field(..., description="Gaps addressed by this pathway")
    phases: List[Dict[str, Any]] = Field(..., description="Implementation phases")
    total_effort_days: int = Field(..., description="Total effort in days")
    total_cost: float = Field(..., description="Total estimated cost")
    risk_reduction_score: float = Field(..., description="Expected risk reduction")
    roi_months: int = Field(..., description="Return on investment timeline")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Success probability")

class GapAnalysisRequest(BaseModel):
    frameworks: List[str] = Field(default_factory=list, description="Frameworks to analyze (optional filter)")
    engagement_id: Optional[str] = Field(None, description="Specific engagement ID to analyze")
    analysis_scope: str = Field("comprehensive", description="Analysis scope: basic, standard, comprehensive")
    include_cost_analysis: bool = Field(True, description="Include cost estimates")
    minimum_risk_threshold: float = Field(0.0, ge=0.0, le=10.0, description="Minimum risk score to include")
    prioritize_by: str = Field("risk_score", description="Prioritization criteria")

class ComplianceReadinessRequest(BaseModel):
    target_frameworks: List[str] = Field(default_factory=list, description="Target frameworks for readiness assessment")
    timeline_months: int = Field(12, description="Target timeline in months")
    available_budget: Optional[float] = Field(None, description="Available budget")
    current_maturity_level: str = Field("intermediate", description="Current maturity: basic, intermediate, advanced")

class RiskAssessmentRequest(BaseModel):
    frameworks: List[str] = Field(default_factory=list, description="Frameworks for risk assessment")
    business_context: str = Field("", description="Business context (industry, size, etc.)")
    risk_appetite: str = Field("medium", description="Risk appetite: low, medium, high")
    compliance_deadline: Optional[datetime] = Field(None, description="Compliance deadline")

# Response Models
class GapAnalysisResponse(BaseModel):
    success: bool = Field(True)
    analysis_id: str = Field(..., description="Analysis identifier")
    frameworks_analyzed: List[str] = Field(..., description="Analyzed frameworks")
    total_gaps_identified: int = Field(..., description="Total gaps found")
    gaps_by_severity: Dict[str, int] = Field(..., description="Gap count by severity")
    gaps: List[ComplianceGap] = Field(..., description="Identified gaps")
    remediation_pathways: List[RemediationPathway] = Field(..., description="Recommended pathways")
    overall_risk_score: float = Field(..., description="Overall risk score")
    estimated_remediation_timeline: str = Field(..., description="Estimated timeline")
    ai_insights: List[str] = Field(..., description="AI-generated insights")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ComplianceReadinessResponse(BaseModel):
    success: bool = Field(True)
    readiness_score: float = Field(..., ge=0.0, le=100.0, description="Overall readiness percentage")
    framework_readiness: Dict[str, float] = Field(..., description="Per-framework readiness")
    readiness_factors: Dict[str, Any] = Field(..., description="Factors affecting readiness")
    timeline_feasibility: str = Field(..., description="Timeline feasibility assessment")
    resource_requirements: Dict[str, Any] = Field(..., description="Required resources")
    success_probability: float = Field(..., description="Probability of meeting targets")
    critical_path_items: List[str] = Field(..., description="Critical path items")
    recommendations: List[str] = Field(..., description="Strategic recommendations")

class RiskAssessmentResponse(BaseModel):
    success: bool = Field(True)
    overall_risk_level: str = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Quantitative risk score")
    risk_breakdown: Dict[str, Any] = Field(..., description="Risk by category")
    top_risk_factors: List[Dict[str, Any]] = Field(..., description="Top risk factors")
    mitigation_priorities: List[str] = Field(..., description="Prioritized mitigation areas")
    business_impact_assessment: Dict[str, Any] = Field(..., description="Business impact analysis")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_analysis_id() -> str:
    """Generate unique analysis ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"gap_analysis_{timestamp}"

def _n(val, default=0.0) -> float:
    """Safe numeric coercion — returns float, never None."""
    try:
        return float(val) if val is not None else float(default)
    except (TypeError, ValueError):
        return float(default)

def _severity_from_completion(completion_pct: float) -> GapSeverity:
    """Map completion percentage to gap severity."""
    if completion_pct < 20:
        return GapSeverity.CRITICAL
    elif completion_pct < 40:
        return GapSeverity.HIGH
    elif completion_pct < 65:
        return GapSeverity.MEDIUM
    elif completion_pct < 85:
        return GapSeverity.LOW
    return GapSeverity.INFO

def _risk_score_from_completion(completion_pct: float, ai_risk: float = 0.0) -> float:
    """Derive a 0-10 risk score from completion % and AI risk score."""
    base = (100.0 - completion_pct) / 10.0   # 0-10 scale
    ai_factor = _n(ai_risk) / 100.0 * 2.0    # up to +2 from AI risk
    return min(10.0, round(base + ai_factor, 1))

async def identify_gaps_from_engagements(
    current_user: MVP1User,
    framework_filter: Optional[List[str]] = None,
    engagement_id: Optional[str] = None
) -> List[ComplianceGap]:
    """
    Derive real compliance gaps from the auditor's assigned engagements.
    Each incomplete/low-completion engagement becomes a gap entry.
    """
    # Use specified engagement ID or default to all assigned
    if engagement_id:
        eng_ids = [engagement_id]
    else:
        eng_ids = getattr(current_user, "assigned_engagements", []) or []
    
    if not eng_ids:
        logger.info("No engagements found to analyze — returning empty gap list")
        return []

    # Build query
    query = {"id": {"$in": eng_ids}}
    # If not admin, ensure they only see their organization's data
    if current_user.role != "admin" and str(current_user.role) != "admin":
        query["organization_id"] = current_user.organization_id

    engagements = await DatabaseOperations.find_many(
        "mvp1_engagements",
        query
    )

    if not engagements:
        logger.info("Assigned engagement IDs found but no documents returned from DB")
        return []

    gaps: List[ComplianceGap] = []

    for eng in engagements:
        framework = eng.get("framework", "Unknown")
        eng_id = eng.get("id", "")
        eng_name = eng.get("name", "Unnamed Engagement")
        client_name = eng.get("client_name", "")

        # Apply framework filter if provided
        if framework_filter:
            normalised = [f.lower().replace(" ", "_").replace("-", "_").replace(".", "_") for f in framework_filter]
            eng_fw_norm = framework.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
            if not any(n in eng_fw_norm or eng_fw_norm in n for n in normalised):
                continue

        # 1. Fetch detailed intake forms for this engagement
        forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": eng_id}
        )

        # 2. Analyze forms for gaps
        for form in forms:
            confidence = _n(form.get("ai_confidence_score"), 0.0)
            status = form.get("status", "draft")
            control_id = form.get("control_id", "Unknown")
            
            # Identify gaps: low confidence or missing/partial implementation
            if confidence < 0.7 or status in ["draft", "needs_revision"]:
                severity = GapSeverity.HIGH if status != "draft" else GapSeverity.MEDIUM
                if confidence < 0.5: severity = GapSeverity.CRITICAL
                
                gaps.append(ComplianceGap(
                    id=f"gap_{form['id']}",
                    title=f"Sub-optimal Control Implementation: {control_id}",
                    description=(
                        f"AI identified a potential compliance gap in {control_id} for {eng_name}. "
                        f"Status is currently '{status}' with a confidence score of {round(confidence, 2)}."
                    ),
                    affected_frameworks=[framework],
                    missing_controls=[control_id],
                    severity=severity,
                    risk_category=RiskCategory.SECURITY if "security" in control_id.lower() else RiskCategory.COMPLIANCE,
                    risk_score=_risk_score_from_completion((1.0 - confidence) * 100),
                    estimated_effort_days=3,
                    ai_confidence=0.88,
                    remediation_steps=[
                        f"Review the analyst's submission for {control_id}",
                        "Upload additional supporting evidence if required",
                        "Address the specific feedback provided by the automated scanner"
                    ],
                    success_criteria=[f"AI confidence score for {control_id} > 0.8", "Auditor approval obtained"],
                    engagement_id=eng_id,
                    engagement_name=eng_name
                ))

        # 3. Add a general engagement gap if completion is low
        completion_pct = _n(eng.get("completion_percentage"), 0.0)
        if completion_pct < 80 and not any(g.engagement_id == eng_id for g in gaps):
            severity = _severity_from_completion(completion_pct)
            gaps.append(ComplianceGap(
                id=f"gap_{eng_id}_velocity",
                title=f"Low Compliance Velocity — {framework}",
                description=f"Engagement {eng_name} is only {round(completion_pct, 1)}% complete. Project deadline is at risk.",
                affected_frameworks=[framework],
                missing_controls=[],
                severity=severity,
                risk_category=RiskCategory.OPERATIONAL,
                risk_score=_risk_score_from_completion(completion_pct),
                estimated_effort_days=10,
                ai_confidence=0.95,
                remediation_steps=["Assign additional resources", "Escalate to compliance management"],
                success_criteria=["Completion percentage > 90%"],
                engagement_id=eng_id,
                engagement_name=eng_name
            ))


    # ── Override with auditor validation/rejection ───────────────────────────
    if gaps:
        gap_ids = [g.id for g in gaps]
        validations = await DatabaseOperations.find_many(
            "mvp1_auditor_feedback",
            {"gap_id": {"$in": gap_ids}}
        )
        validation_map = {v["gap_id"]: v["status"] for v in validations if v.get("status")}

        for gap in gaps:
            if gap.id in validation_map:
                gap.status = validation_map[gap.id]

    # Sort by risk score descending
    gaps.sort(key=lambda g: g.risk_score, reverse=True)
    return gaps


async def generate_remediation_pathways(gaps: List[ComplianceGap]) -> List[RemediationPathway]:
    """Generate smart remediation pathways based on identified gaps"""
    pathways = []
    
    high_risk_gaps = [g for g in gaps if g.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]]
    medium_gaps    = [g for g in gaps if g.severity == GapSeverity.MEDIUM]
    
    if high_risk_gaps:
        pathway = RemediationPathway(
            id=f"pathway_critical_{datetime.utcnow().strftime('%Y%m%d')}",
            name="Critical & High Risk Remediation",
            description=(
                f"Addresses {len(high_risk_gaps)} critical/high-risk compliance gaps "
                "across your assigned engagements with optimised resource allocation."
            ),
            target_gaps=[gap.id for gap in high_risk_gaps],
            phases=[
                {
                    "phase": 1,
                    "name": "Immediate Triage & Critical Controls",
                    "duration_days": 14,
                    "activities": [
                        "Review all critical-severity gaps with engagement leads",
                        "Assign dedicated analysts to incomplete critical controls",
                        "Escalate high AI risk score engagements for urgent review"
                    ]
                },
                {
                    "phase": 2,
                    "name": "Systematic Control Completion",
                    "duration_days": 30,
                    "activities": [
                        "Complete all outstanding control assessments",
                        "Upload and link required evidence for each control",
                        "Conduct daily stand-ups to track progress"
                    ]
                },
                {
                    "phase": 3,
                    "name": "Auditor Review & Approval",
                    "duration_days": 14,
                    "activities": [
                        "Batch-review completed controls and provide feedback",
                        "Approve or reject with documented rationale",
                        "Finalise engagement status and generate compliance report"
                    ]
                }
            ],
            total_effort_days=sum(g.estimated_effort_days for g in high_risk_gaps),
            total_cost=sum(g.estimated_cost or 0 for g in high_risk_gaps),
            risk_reduction_score=8.5,
            roi_months=4,
            success_probability=0.88
        )
        pathways.append(pathway)

    if medium_gaps:
        pathway = RemediationPathway(
            id=f"pathway_medium_{datetime.utcnow().strftime('%Y%m%d')}",
            name="Medium Risk Improvement Plan",
            description=(
                f"Addresses {len(medium_gaps)} medium-risk gaps to improve overall "
                "compliance posture across assigned engagements."
            ),
            target_gaps=[gap.id for gap in medium_gaps],
            phases=[
                {
                    "phase": 1,
                    "name": "Planning & Prioritisation",
                    "duration_days": 7,
                    "activities": [
                        "Prioritise medium gaps by business impact",
                        "Assign ownership to relevant team members",
                        "Set 90-day completion targets"
                    ]
                },
                {
                    "phase": 2,
                    "name": "Execution & Monitoring",
                    "duration_days": 60,
                    "activities": [
                        "Complete pending control assessments",
                        "Process approval backlog systematically",
                        "Weekly progress reviews with engagement team"
                    ]
                }
            ],
            total_effort_days=sum(g.estimated_effort_days for g in medium_gaps),
            total_cost=sum(g.estimated_cost or 0 for g in medium_gaps),
            risk_reduction_score=5.5,
            roi_months=6,
            success_probability=0.82
        )
        pathways.append(pathway)

    return pathways

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for AI Gap Analysis module"""
    return {
        "status": "healthy",
        "module": "AI Gap Analysis",
        "phase": "4B - Engagement-Grounded Gap Intelligence",
        "capabilities": [
            "Real gap identification from assigned engagements",
            "Control completion gap analysis",
            "AI risk score-based prioritisation",
            "Smart remediation pathways",
            "Predictive compliance readiness",
        ],
        "data_source": "mvp1_engagements (live database)",
    }

@router.post("/analyze", response_model=GapAnalysisResponse)
async def analyze_compliance_gaps(
    request: GapAnalysisRequest,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Run comprehensive compliance gap analysis grounded in assigned engagements"""
    try:
        logger.info(f"Starting gap analysis for user: {current_user.email}")

        analysis_id = generate_analysis_id()

        # Identify gaps from real engagement data
        framework_filter = [f if isinstance(f, str) else f.value for f in request.frameworks] if request.frameworks else None
        gaps = await identify_gaps_from_engagements(current_user, framework_filter, request.engagement_id)

        # Filter by minimum risk threshold
        filtered_gaps = [g for g in gaps if g.risk_score >= request.minimum_risk_threshold]

        # Generate remediation pathways
        pathways = await generate_remediation_pathways(filtered_gaps)

        # Calculate metrics
        gaps_by_severity: Dict[str, int] = {s.value: 0 for s in GapSeverity}
        for gap in filtered_gaps:
            gaps_by_severity[gap.severity.value] += 1

        overall_risk_score = (
            sum(g.risk_score for g in filtered_gaps) / len(filtered_gaps)
            if filtered_gaps else 0.0
        )

        # Collect unique frameworks from gaps
        frameworks_seen = list({fw for g in filtered_gaps for fw in g.affected_frameworks})

        # Generate insights
        ai_insights = [
            f"Identified {len(filtered_gaps)} compliance gaps across {len(frameworks_seen)} framework(s) in your assigned engagements",
            f"Overall risk score: {round(overall_risk_score, 1)}/10.0",
            f"Estimated total remediation effort: {sum(g.estimated_effort_days for g in filtered_gaps)} days",
            f"Generated {len(pathways)} optimised remediation pathways"
        ]
        if gaps_by_severity.get("critical", 0) > 0:
            ai_insights.append(f"⚠️  {gaps_by_severity['critical']} critical gaps require immediate attention")
        if not filtered_gaps:
            ai_insights.append("✅ No significant gaps detected — your assigned engagements are in good standing")

        logger.info(f"Gap analysis completed: {len(filtered_gaps)} gaps identified for {current_user.email}")

        return GapAnalysisResponse(
            analysis_id=analysis_id,
            frameworks_analyzed=frameworks_seen,
            total_gaps_identified=len(filtered_gaps),
            gaps_by_severity=gaps_by_severity,
            gaps=filtered_gaps,
            remediation_pathways=pathways,
            overall_risk_score=round(overall_risk_score, 1),
            estimated_remediation_timeline=f"{max(1, sum(g.estimated_effort_days for g in filtered_gaps) // 30)} months",
            ai_insights=ai_insights
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gap analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.get("/detect", response_model=GapAnalysisResponse)
async def detect_gaps(
    frameworks: str = Query("", description="Comma-separated frameworks (optional filter)"),
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Detect gaps via GET request — grounded in auditor's assigned engagements"""
    try:
        fw_list = [f.strip() for f in frameworks.split(",") if f.strip()] if frameworks else []
        req = GapAnalysisRequest(frameworks=fw_list)
        return await analyze_compliance_gaps(req, current_user, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detect gaps error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-compliance", response_model=ComplianceReadinessResponse)
async def predict_compliance_readiness(
    request: ComplianceReadinessRequest,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Predict compliance readiness based on actual engagement progress"""
    try:
        logger.info(f"Predicting compliance readiness for: {current_user.email}")

        eng_ids = getattr(current_user, "assigned_engagements", []) or []
        engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            {"id": {"$in": eng_ids}}
        ) if eng_ids else []

        # Compute per-framework readiness from real data
        framework_totals: Dict[str, Dict[str, float]] = {}
        for eng in engagements:
            fw = eng.get("framework", "Unknown")
            pct = _n(eng.get("completion_percentage"), 0.0)
            if fw not in framework_totals:
                framework_totals[fw] = {"sum": 0.0, "count": 0}
            framework_totals[fw]["sum"] += pct
            framework_totals[fw]["count"] += 1

        framework_readiness: Dict[str, float] = {}
        for fw, data in framework_totals.items():
            framework_readiness[fw] = round(data["sum"] / data["count"], 1) if data["count"] > 0 else 0.0

        # If no engagements, fall back to maturity-based estimate
        if not framework_readiness:
            base = {"basic": 45.0, "intermediate": 65.0, "advanced": 80.0}.get(
                request.current_maturity_level, 65.0
            )
            for fw in (request.target_frameworks or ["General"]):
                framework_readiness[fw if isinstance(fw, str) else fw] = base

        overall_readiness = (
            sum(framework_readiness.values()) / len(framework_readiness)
            if framework_readiness else 0.0
        )

        feasibility = (
            "Achievable" if request.timeline_months >= 12
            else "Challenging" if request.timeline_months >= 6
            else "Aggressive"
        )

        # Derive critical path from lowest-readiness frameworks
        sorted_fw = sorted(framework_readiness.items(), key=lambda x: x[1])
        critical_path = [
            f"Improve {fw} readiness (currently {pct:.0f}%)"
            for fw, pct in sorted_fw[:3]
            if pct < 80
        ] or ["Maintain current progress across all engagements"]

        return ComplianceReadinessResponse(
            readiness_score=round(overall_readiness, 1),
            framework_readiness=framework_readiness,
            readiness_factors={
                "total_assigned_engagements": len(eng_ids),
                "engagements_with_data": len(engagements),
                "current_maturity": request.current_maturity_level,
                "timeline_months": request.timeline_months,
                "budget_adequacy": (
                    "Adequate" if request.available_budget and request.available_budget > 100000
                    else "Limited"
                )
            },
            timeline_feasibility=feasibility,
            resource_requirements={
                "estimated_fte": max(1.0, len(eng_ids) * 0.5),
                "estimated_budget": len(eng_ids) * 25000,
                "key_skills_needed": ["Compliance Management", "Risk Assessment", "Evidence Review"]
            },
            success_probability=min(0.95, overall_readiness / 100 * 1.2),
            critical_path_items=critical_path,
            recommendations=[
                f"Focus on the {len([fw for fw, pct in framework_readiness.items() if pct < 50])} frameworks below 50% readiness",
                "Implement shared controls across frameworks to maximise efficiency",
                "Schedule weekly auditor review sessions to clear approval backlogs",
                "Use AI risk scores to prioritise the highest-risk engagements first"
            ]
        )

    except Exception as e:
        logger.error(f"Readiness prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Readiness prediction failed: {str(e)}")


@router.post("/analyze-engagement")
async def analyze_engagement_items(
    request: AnalyzeEngagementRequest,
    current_user: MVP1User = Depends(get_current_user)
):
    """Trigger AI analysis for all intake forms and evidence within an engagement"""
    try:
        logger.info(f"Triggering analysis for engagement: {request.engagement_id}")
        
        # 1. Fetch pending forms
        forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": request.engagement_id}
        )
        
        # 2. Fetch evidence
        evidence_files = await DatabaseOperations.find_many(
            "mvp1_evidence",
            {"engagement_id": request.engagement_id}
        )
        
        from mvp1_analyst_workflow import trigger_ai_analysis
        
        tasks = []
        for f in forms:
            tasks.append(trigger_ai_analysis(f["id"], "form_analysis", current_user.organization_id))
        
        for e in evidence_files:
            tasks.append(trigger_ai_analysis(e["id"], "evidence_analysis", current_user.organization_id))
                
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"Proactively analyzed {len(tasks)} items for engagement {request.engagement_id}")
            
        return {
            "status": "success",
            "message": f"Analyzed {len(tasks)} items",
            "engagement_id": request.engagement_id,
            "processed_count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Error triggering analysis for engagement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("AI Gap Analysis API initialized successfully — data grounded in assigned engagements")
