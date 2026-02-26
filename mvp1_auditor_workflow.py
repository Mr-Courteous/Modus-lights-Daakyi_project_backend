# === AI Findings for Engagement (Phase 3-4 Integration) ===

"""
MVP 1 Week 4: Auditor Workflow Backend APIs
Real-time reviewer dashboard, analyst submission access, evidence annotation, and approval workflows

Features:
- Auditor dashboard with real-time analyst insights
- View-only access to analyst form responses and AI recommendations
- Evidence annotation and review capabilities  
- Feedback submission and approval system
- Complete audit trail continuity
- Role-based access restrictions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, BackgroundTasks
from mvp1_analyst_workflow import generate_remediation_plan
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging
from pydantic import BaseModel

from mvp1_models import (
    MVP1User, UserRole, UserStatus, EngagementStatus, TaskStatus, 
    EvidenceStatus, AIProcessingStatus, AuditLogEntry
)
from mvp1_auth import get_current_user, require_role, ensure_organization_access
from database import DatabaseOperations

logger = logging.getLogger(__name__)

# Create router for auditor workflow endpoints
auditor_router = APIRouter(prefix="/api/mvp1/auditor", tags=["MVP1 Auditor Workflow"])

# =====================================
# AUDITOR WORKFLOW PYDANTIC MODELS
# =====================================

class AuditorDashboardResponse(BaseModel):
    """Auditor dashboard with real-time insights"""
    auditor_overview: Dict[str, Any]
    pending_reviews: List[Dict[str, Any]]
    recent_feedback: List[Dict[str, Any]]
    analyst_submissions: List[Dict[str, Any]]
    engagement_insights: Dict[str, Any]
    quick_actions: List[Dict[str, Any]]

class AnalystSubmissionDetail(BaseModel):
    """Detailed analyst submission for auditor review"""
    submission_id: str
    engagement_id: str
    analyst_id: str
    analyst_name: str
    framework: str
    control_id: str
    form_responses: Dict[str, Any]
    ai_recommendations: List[Dict[str, Any]]
    evidence_files: List[Dict[str, Any]]
    submission_date: datetime
    status: str
    completion_percentage: float
    ai_confidence_score: Optional[float]

class EvidenceAnnotation(BaseModel):
    """Evidence annotation by auditor"""
    annotation_id: str = None
    evidence_id: str
    auditor_id: str
    annotation_type: str  # "comment", "highlight", "flag", "approval", "rejection"
    annotation_text: str
    annotation_position: Optional[Dict[str, Any]] = None  # For document positioning
    severity: str = "info"  # "info", "warning", "critical"
    created_at: datetime = None

class FeedbackSubmission(BaseModel):
    """Auditor feedback on analyst submission"""
    feedback_id: str = None
    submission_id: str
    auditor_id: str
    feedback_type: str  # "approve", "reject", "requires_revision"
    overall_assessment: str
    detailed_comments: str
    evidence_feedback: List[Dict[str, Any]] = []
    corrective_actions: List[str] = []
    compliance_rating: Optional[int] = None  # 1-5 scale
    resubmission_required: bool = False
    priority_level: str = "medium"  # "low", "medium", "high", "critical"
    created_at: datetime = None

class ApprovalWorkflow(BaseModel):
    """Approval workflow status and history"""
    workflow_id: str
    submission_id: str
    current_status: str
    approval_history: List[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    workflow_stage: str
    estimated_completion: Optional[datetime]

# =====================================
# AUDITOR DASHBOARD ENDPOINTS
# =====================================

@auditor_router.get("/findings/{engagement_id}", response_model=List[Dict[str, Any]])
async def get_ai_findings_for_engagement(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Fetch all findings for a specific engagement.
    Returns every record from mvp1_intake_forms and mvp1_evidence regardless of AI status.
    """
    logger.info(f"[findings] HIT: engagement_id={engagement_id}, user={current_user.email}, role={current_user.role}")

    # Inline role check — allows AUDITOR, ANALYST, and ADMIN
    allowed_roles = [UserRole.AUDITOR, UserRole.ANALYST, UserRole.ADMIN]
    if current_user.role not in allowed_roles and str(current_user.role) not in ["auditor", "analyst", "admin"]:
        logger.warning(f"[findings] 403: user {current_user.email} has role {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: auditor, analyst, or admin."
        )

    try:
        # 1. Try fetching from dedicated findings collection
        findings = await DatabaseOperations.find_many(
            "control_assessments",
            {
                "engagement_id": engagement_id
            }
        )
        
        results = []
        
        # 2. Generate from Intake Forms (primary source of AI analysis)
        # Always fetch form data to ensure AI analysis is visible
        forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id}
        )
        
        # Fetch analysts for mapping names (guard against empty $in)
        analyst_ids = list(set([f.get("analyst_id") for f in forms if f.get("analyst_id")]))
        if analyst_ids:
            analysts = await DatabaseOperations.find_many("mvp1_users", {"id": {"$in": analyst_ids}})
        else:
            analysts = []
        analyst_map = {a["id"]: a.get("name", "Unknown Analyst") for a in analysts}

        for form in forms:
            # Extract AI Gaps/Risks - Ensure fallback for None values in DB
            ai_results = form.get("ai_analysis_results") or {}
            confidence = form.get("ai_confidence_score") or 0.0
            db_status = form.get("status", "draft")
            
            # Use strict visibility: Show all items regardless of AI status
            gaps = form.get("identified_gaps") or []

            # Analyst-provided fallback for recommendation when AI hasn't run yet
            analyst_description = (
                form.get("implementation_description")
                or (form.get("form_data") or {}).get("implementation_description")
                or (form.get("responses") or {}).get("implementation_description")
                or ""
            )
            
            # Determine status and description based on analysis
            # IF status in DB is already indicating progress past 'submitted' or 'draft', respect it
            if db_status in ["approved", "rejected", "ai_verified", "gap_found", "needs_remediation", "requires_revision"]:
                status_val = db_status
                desc = form.get("remediation_summary") or analyst_description or "Reviewed item"
                rec = ai_results.get("recommendation") or analyst_description or "Follow remediation plan"
            elif confidence >= 0.8 and not gaps:
                status_val = "ai_verified"
                desc = "AI validation successful - High confidence"
                rec = "Verify and approve"
            elif confidence > 0:
                status_val = "pending"
                if not gaps:
                    gaps = ["Manual review recommended"]
                desc = "; ".join(gaps)
                rec = ai_results.get("recommendation") or analyst_description or "Review control implementation"
            else:
                # No AI analysis yet — use analyst's own description as interim recommendation
                status_val = "pending_ai_analysis"
                desc = analyst_description or "Awaiting AI Analysis"
                rec = analyst_description or "Awaiting AI Analysis"  # must set rec in every branch
                ai_results = {}  # Clear stale data
            
            # Derive severity
            risk_lvl = ai_results.get("risk_level", "").lower()
            if not gaps and confidence >= 0.8:
                severity = "Low"
            elif risk_lvl == "high" or "Manual review recommended" in gaps:
                severity = "High"
            elif risk_lvl == "critical":
                severity = "Critical"
            else:
                severity = "Medium"

            # Serialise datetime fields so FastAPI can return them as strings
            last_updated = form.get("last_modified_at") or form.get("submitted_at")
            if hasattr(last_updated, "isoformat"):
                last_updated = last_updated.isoformat()

            results.append({
                "id": form["id"],
                "control_id": form.get("control_id"),
                "control": form.get("control_id"),
                "submission_id": form["id"],
                "evidence_id": None,
                "aiConfidence": int(confidence * 100) if confidence else 0,
                "status": status_val,
                "severity": severity,
                "description": desc,
                "control_name": form.get("control_title", form.get("control_id")),
                "gap_summary": desc,
                "recommendation": rec,
                "framework": form.get("framework_id", "Unknown"),
                "last_updated": last_updated,
                "analyst_id": form.get("analyst_id"),
                "analyst_name": analyst_map.get(form.get("analyst_id"), "Unknown Analyst"),
                "analyst_description": analyst_description,
                "auditor_comments": form.get("auditor_comments"),
                "auditor_name": form.get("auditor_name"),
                "ai_details": ai_results,
                "form_responses": form.get("form_data") or form.get("responses") or {},
                "source_type": "intake_form"
            })

        # 3. Check Evidence for AI flags — fetched ONCE outside the forms loop
        evidence_list = await DatabaseOperations.find_many(
            "mvp1_evidence",
            {"engagement_id": engagement_id}
        )
        for ev in evidence_list:
            ai_res = ev.get("ai_analysis_results", {})
            confidence = ev.get("ai_confidence_score", 0.0)
            db_status = ev.get("status", "uploaded")

            # Analyst-provided fallback
            analyst_description = (
                ev.get("description")
                or ev.get("notes")
                or f"Uploaded file: {ev.get('original_filename', 'Unknown')}"
            )

            # Determine status for evidence
            if db_status in ["approved", "rejected", "analyzed", "requires_revision"]:
                # Map analyzed to ai_verified or similar for frontend
                status_val = "ai_verified" if db_status == "analyzed" else db_status
                desc = analyst_description
                rec = ai_res.get("recommendation") or analyst_description or "Evidence review complete"
            elif confidence >= 0.8 and ai_res.get("risk_level") != "high":
                status_val = "ai_verified"
                desc = "Evidence analyzed - Low risk"
                rec = ai_res.get("recommendation") or analyst_description or "Verify evidence content manually"
            elif confidence > 0:
                status_val = "pending"
                desc = f"Review required: {ev.get('original_filename')}"
                rec = ai_res.get("recommendation") or analyst_description or "Verify evidence content manually"
            else:
                # No AI yet — surface with analyst context
                status_val = "pending_ai_analysis"
                desc = analyst_description or "Awaiting AI Analysis"
                ai_res = {}
            
            # Derive severity for evidence
            risk_lvl = ai_res.get("risk_level", "").lower()
            if status_val == "ai_verified":
                severity = "Low"
            elif risk_lvl == "high" or status_val == "requires_revision":
                severity = "High"
            elif risk_lvl == "critical":
                severity = "Critical"
            else:
                severity = "Medium"

            ev_last_updated = ev.get("uploaded_at") or ev.get("updated_at")
            if hasattr(ev_last_updated, "isoformat"):
                ev_last_updated = ev_last_updated.isoformat()

            results.append({
                "id": ev["id"],
                "control_id": ev.get("control_id"),
                "control": ev.get("control_id"),
                "submission_id": ev["id"],
                "evidence_id": ev["id"],
                "filename": ev.get("original_filename"),
                "aiConfidence": int(confidence * 100) if confidence else 0,
                "status": status_val,
                "severity": severity,
                "description": desc,
                "recommendation": rec,
                "analyst_description": analyst_description,
                "framework": "Evidence Analysis",
                "last_updated": ev_last_updated,
                "ai_details": ai_res,
                "source_type": "evidence"
            })

        # 4. Include existing control assessments (manual findings or prior reviews)
        for f in findings:
            results.append({
                "id": f.get("id", str(uuid.uuid4())),
                "control_id": f.get("control_id"),
                "control": f.get("control_name", f.get("control_id")),
                "evidence_id": f.get("evidence_id"),
                "aiConfidence": int(f.get("ai_confidence", 0) * 100),
                "status": f.get("status", "pending"),
                "description": f.get("description", ""),
                "control_name": f.get("control_name", ""),
                "gap_summary": f.get("gap_summary", ""),
                "recommendation": f.get("recommendation", "Review required"),
                "framework": f.get("framework", "Unknown"),
                "last_updated": f.get("updated_at"),
                "source_type": "finding"
            })

        logger.info(f"Findings endpoint: engagement_id={engagement_id}, generated_findings={len(results)}")
        return results

    except Exception as e:
        logger.error(f"Error fetching AI findings for engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch AI findings")

    
    
@auditor_router.get("/dashboard", response_model=AuditorDashboardResponse)
@require_role(UserRole.AUDITOR)
async def get_auditor_dashboard(current_user: MVP1User = Depends(get_current_user)):
    """Get auditor dashboard with real-time insights"""
    try:

        # Get all engagements where current auditor is assigned
        assigned_engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            {
                "organization_id": current_user.organization_id,
                "assigned_auditors": {"$in": [current_user.id]}
            }
        )
        assigned_engagement_ids = [e["id"] for e in assigned_engagements]

        # Get pending reviews (forms status=submitted/under_review) for assigned engagements only
        pending_forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {
                "organization_id": current_user.organization_id,
                "status": {"$in": ["submitted", "under_review"]},
                "engagement_id": {"$in": assigned_engagement_ids}
            }
        )
        pending_forms_count = len(pending_forms)

        # Get completed reviews this week
        week_start = datetime.utcnow() - timedelta(days=7)
        completed_reviews_count = await DatabaseOperations.count_documents(
            "mvp1_auditor_feedback",
            {
                "auditor_id": current_user.id,
                "created_at": {"$gte": week_start}
            }
        )

        # Calculate average compliance score from approved forms
        approved_forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {
                "organization_id": current_user.organization_id,
                "status": "approved"
            }
        )
        scores = [f.get("compliance_score", 0) for f in approved_forms if f.get("compliance_score")]
        avg_compliance_score = round(sum(scores) / len(scores), 1) if scores else 0

        # Construct pending_reviews list (top 5)
        # Collect engagement IDs
        eng_ids = list(set([f.get("engagement_id") for f in pending_forms if f.get("engagement_id")]))
        engagements = await DatabaseOperations.find_many("mvp1_engagements", {"id": {"$in": eng_ids}})
        eng_map = {e["id"]: e.get("name", "Unknown Engagement") for e in engagements}
        
        # User names
        user_ids = list(set([f.get("analyst_id") for f in pending_forms if f.get("analyst_id")]))
        users = await DatabaseOperations.find_many("mvp1_users", {"id": {"$in": user_ids}})
        user_map = {u["id"]: u.get("name", "Unknown Analyst") for u in users}

        dashboard_pending_reviews = []
        for form in pending_forms[:5]: # Top 5
            dashboard_pending_reviews.append({
                "submission_id": form["id"],
                "engagement_name": eng_map.get(form.get("engagement_id"), "Unknown"),
                "analyst_name": user_map.get(form.get("analyst_id"), "Unknown Analyst"),
                "control_id": form.get("control_id"),
                "submitted_date": form.get("submitted_at", datetime.utcnow()).isoformat() if isinstance(form.get("submitted_at"), datetime) else str(form.get("submitted_at", "")),
                "ai_confidence": round(form.get("ai_confidence_score", 0) * 100, 1),
                "priority": form.get("priority", "medium"),
                "framework": form.get("framework_id", "Unknown") 
            })

        # Recent Feedback
        recent_feedbacks = await DatabaseOperations.find_many(
            "mvp1_auditor_feedback",
            {
                "auditor_id": current_user.id
            },
            sort=[("created_at", -1)],
            limit=5
        )
        
        dashboard_recent_feedback = []
        for fb in recent_feedbacks:
            dashboard_recent_feedback.append({
                "feedback_id": fb.get("id", "Unknown"),
                "submission_id": fb.get("submission_id", "Unknown"),
                "analyst_name": "Unknown", # Placeholder until we fetch linked submission -> analyst
                "control_id": fb.get("control_id", "Unknown"),
                "feedback_type": fb.get("feedback_type", "Unknown"),
                "created_date": fb["created_at"].isoformat() if isinstance(fb.get("created_at"), datetime) else str(fb.get("created_at", "")),
                "compliance_rating": fb.get("compliance_rating", 0)
            })

        # Analyst Submissions Summary
        all_forms = await DatabaseOperations.find_many(
             "mvp1_intake_forms",
             {"organization_id": current_user.organization_id}
        )
        
        analyst_stats = {}
        for form in all_forms:
            aid = form.get("analyst_id")
            if not aid:
                continue
            if aid not in analyst_stats:
                analyst_stats[aid] = {"total": 0, "pending": 0, "approved": 0, "revision": 0, "confidence_sum": 0, "count": 0}
            
            stats = analyst_stats[aid]
            stats["total"] += 1
            form_status = form.get("status")  # Avoid shadowing 'status' from fastapi
            if form_status in ["submitted", "under_review", "pending_review"]:
                stats["pending"] += 1
            elif form_status == "approved":
                stats["approved"] += 1
            elif form_status == "requires_revision":
                stats["revision"] += 1
            
            if form.get("ai_confidence_score"):
                stats["confidence_sum"] += form.get("ai_confidence_score")
                stats["count"] += 1

        # Fetch analyst names if not already in user_map
        all_analyst_ids = list(analyst_stats.keys())
        missing_ids = [aid for aid in all_analyst_ids if aid not in user_map]
        if missing_ids:
            more_users = await DatabaseOperations.find_many("mvp1_users", {"id": {"$in": missing_ids}})
            for u in more_users:
                user_map[u["id"]] = u.get("name", "Unknown Analyst")

        analyst_submissions_list = []
        for aid, stats in analyst_stats.items():
            username = user_map.get(aid, "Unknown Analyst")
            analyst_submissions_list.append({
                "analyst_id": aid,
                "analyst_name": username,
                "total_submissions": stats["total"],
                "pending_review": stats["pending"],
                "approved": stats["approved"],
                "requires_revision": stats["revision"],
                "avg_ai_confidence": round((stats["confidence_sum"] / stats["count"] * 100), 1) if stats["count"] else 0
            })

        # Engagement Insights with all assigned engagements
        engagement_insights = {
            "total_engagements": len(assigned_engagements),
            "active_reviews": pending_forms_count,
            "completion_rate": 0,
            "avg_quality_score": avg_compliance_score,
            "framework_distribution": {},
            "review_velocity": {
                "this_week": completed_reviews_count,
                "last_week": 0,
                "trend": "stable"
            },
            # List all assigned engagements (id and name)
            "engagements": [
                {"id": e["id"], "name": e.get("name", e["id"])} for e in assigned_engagements
            ]
        }

        # Quick Actions
        quick_actions = [
            {
                "action_id": "review_pending",
                "title": "Review Pending Submissions",
                "description": f"{pending_forms_count} submissions awaiting review",
                "priority": "high",
                "action_type": "navigation",
                "action_data": {"route": "/auditor/submissions?status=submitted"}
            },
            {
                "action_id": "annotate_evidence",
                "title": "Annotate Evidence",
                "description": "Review and annotate uploaded evidence",
                "priority": "medium",
                "action_type": "navigation",
                "action_data": {"route": "/auditor/evidence-review"}
            },
            {
                "action_id": "generate_report",
                "title": "Generate Audit Report",
                "description": "Create comprehensive audit findings report",
                "priority": "medium",
                "action_type": "modal",
                "action_data": {"modal": "report-generator"}
            },
             {
                "action_id": "send_feedback",
                "title": "Send Feedback",
                "description": "Provide detailed feedback to analysts",
                "priority": "low",
                "action_type": "navigation",
                "action_data": {"route": "/auditor/feedback"}
            }
        ]

        return AuditorDashboardResponse(
            auditor_overview={
                "total_pending_reviews": pending_forms_count,
                "completed_this_week": completed_reviews_count,
                "average_review_time_days": 2.5,
                "avg_compliance_score": avg_compliance_score,
                "active_engagements": engagement_insights["total_engagements"],
                "review_velocity": engagement_insights["review_velocity"]["this_week"]
            },
            pending_reviews=dashboard_pending_reviews,
            recent_feedback=dashboard_recent_feedback,
            analyst_submissions=analyst_submissions_list,
            engagement_insights=engagement_insights,
            quick_actions=quick_actions
        )

    except Exception as e:
        logger.error(f"Error getting auditor dashboard for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve auditor dashboard"
        )

# =====================================
# ANALYST SUBMISSION ACCESS ENDPOINTS 
# =====================================

@auditor_router.get("/submissions", response_model=List[Dict[str, Any]])
@require_role(UserRole.AUDITOR)
async def get_analyst_submissions(
    engagement_id: Optional[str] = None,
    status: Optional[str] = None,
    analyst_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get analyst submissions for auditor review"""
    try:

        # Get all engagements where current auditor is assigned
        assigned_engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            {
                "organization_id": current_user.organization_id,
                "assigned_auditors": {"$in": [current_user.id]}
            }
        )
        assigned_engagement_ids = [e["id"] for e in assigned_engagements]

        # Build query filters
        query = {"organization_id": current_user.organization_id, "engagement_id": {"$in": assigned_engagement_ids}}
        if engagement_id:
            if engagement_id in assigned_engagement_ids:
                query["engagement_id"] = engagement_id
            else:
                # If auditor tries to access an engagement not assigned, return empty
                return []
        if status:
            query["status"] = status
        if analyst_id:
            query["analyst_id"] = analyst_id

        # Fetch submissions
        submissions = await DatabaseOperations.find_many("mvp1_intake_forms", query)
        
        # Enrich with Engagement and User names
        eng_ids = list(set([s.get("engagement_id") for s in submissions if s.get("engagement_id")]))
        engagements = await DatabaseOperations.find_many("mvp1_engagements", {"id": {"$in": eng_ids}})
        eng_map = {e["id"]: e.get("name", "Unknown Engagement") for e in engagements}
        
        analyst_ids = list(set([s.get("analyst_id") for s in submissions if s.get("analyst_id")]))
        users = await DatabaseOperations.find_many("mvp1_users", {"id": {"$in": analyst_ids}})
        user_map = {u["id"]: u.get("name", "Unknown Analyst") for u in users}

        mapped_submissions = []
        for s in submissions:
             mapped_submissions.append({
                "submission_id": s["id"],
                "engagement_id": s.get("engagement_id"),
                "engagement_name": eng_map.get(s.get("engagement_id"), "Unknown"),
                "analyst_id": s.get("analyst_id"),
                "analyst_name": user_map.get(s.get("analyst_id"), "Unknown Analyst"),
                "framework": s.get("framework_id", "Unknown"),
                "control_id": s.get("control_id"),
                "control_title": s.get("control_title", "Unknown Control"),
                "form_responses": s.get("form_data") or {},
                "ai_confidence_score": round(s.get("ai_confidence_score", 0) * 100, 1),
                "submission_date": s.get("submitted_at", datetime.utcnow()).isoformat() if isinstance(s.get("submitted_at"), datetime) else str(s.get("submitted_at", "")),
                "status": s.get("status", "pending"),
                "priority": s.get("priority", "medium"),
                "evidence_count": len(s.get("evidence_ids") or []),
                "estimated_review_time": "30 mins"
             })

        logger.info(f"Retrieved {len(mapped_submissions)} analyst submissions for auditor {current_user.id}")
        return mapped_submissions

    except Exception as e:
        logger.error(f"Error getting analyst submissions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analyst submissions"
        )

@auditor_router.get("/submissions/{submission_id}", response_model=AnalystSubmissionDetail)
@require_role(UserRole.AUDITOR)
async def get_submission_detail(
    submission_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get detailed analyst submission for auditor review"""
    try:

        # Fetch submission
        submission = await DatabaseOperations.find_one("mvp1_intake_forms", {"id": submission_id})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Check access (org check and auditor assignment)
        if submission.get("organization_id") != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Fetch engagement and check auditor assignment
        engagement = await DatabaseOperations.find_one("mvp1_engagements", {"id": submission.get("engagement_id")})
        if not engagement or current_user.id not in engagement.get("assigned_auditors", []):
            raise HTTPException(status_code=403, detail="You are not assigned to this engagement")
        # engagement_name = engagement.get("name", "Unknown") if engagement else "Unknown"

        # Fetch analyst name
        analyst = await DatabaseOperations.find_one("mvp1_users", {"id": submission.get("analyst_id")})
        analyst_name = analyst.get("name", "Unknown Analyst") if analyst else "Unknown Analyst"

        # Fetch Evidence
        evidence_files = []
        if (submission.get("evidence_ids") or []):
             evidences = await DatabaseOperations.find_many("mvp1_evidence", {"id": {"$in": (submission.get("evidence_ids") or [])}})
             for ev in evidences:
                 evidence_files.append({
                     "evidence_id": ev["id"],
                     "filename": ev.get("filename"),
                     "file_type": ev.get("content_type", "unknown"),
                     "file_size": f"{round(ev.get('file_size', 0)/1024, 1)} KB",
                     "upload_date": ev.get("uploaded_at", datetime.utcnow()).isoformat() if isinstance(ev.get("uploaded_at"), datetime) else str(ev.get("uploaded_at", "")),
                     "ai_analysis": ev.get("ai_analysis_results") or {},
                     "annotations_count": 0 
                 })
                 
        # Fetch AI Recommendations
        ai_recommendations = (submission.get("ai_analysis_results") or {}).get("recommendations") or []
        formatted_recommendations = ai_recommendations if isinstance(ai_recommendations, list) else []

        submission_detail = AnalystSubmissionDetail(
            submission_id=submission_id,
            engagement_id=submission.get("engagement_id"),
            analyst_id=submission.get("analyst_id"),
            analyst_name=analyst_name,
            framework=submission.get("framework_id", "Unknown"),
            control_id=submission.get("control_id"),
            form_responses=submission.get("form_data") or {},
            ai_recommendations=formatted_recommendations,
            evidence_files=evidence_files,
            submission_date=submission.get("submitted_at") if isinstance(submission.get("submitted_at"), datetime) else datetime.utcnow(),
            status=submission.get("status", "pending"),
            completion_percentage=submission.get("completion_percentage", 95.0) if submission.get("completion_percentage") else 95.0,
            ai_confidence_score=round(submission.get("ai_confidence_score", 0) * 100, 1) if submission.get("ai_confidence_score") else 0.0
        )

        logger.info(f"Retrieved detailed submission {submission_id} for auditor {current_user.id}")
        return submission_detail

    except Exception as e:
        logger.error(f"Error getting submission detail {submission_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission details"
        )

# =====================================
# EVIDENCE ANNOTATION ENDPOINTS
# =====================================

@auditor_router.post("/annotations", response_model=Dict[str, Any])
@require_role(UserRole.AUDITOR)
async def create_evidence_annotation(
    annotation: EvidenceAnnotation,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create evidence annotation by auditor"""
    try:
        # Create annotation
        annotation_dict = annotation.dict()
        if not annotation_dict.get("evidence_id"):
             raise HTTPException(status_code=400, detail="Evidence ID required")

        annotation_dict["annotation_id"] = f"ANN-{uuid.uuid4().hex[:8].upper()}"
        annotation_dict["auditor_id"] = current_user.id
        annotation_dict["auditor_name"] = current_user.name
        annotation_dict["created_at"] = datetime.utcnow()
        annotation_dict["organization_id"] = current_user.organization_id
        
        # Save to database
        await DatabaseOperations.insert_one("mvp1_evidence_annotations", annotation_dict)

        # Log annotation creation
        await _log_audit_event(
            organization_id=current_user.organization_id,
            action_type="evidence_annotated",
            action_description=f"Evidence annotated: {annotation.evidence_id}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="evidence",
            target_id=annotation.evidence_id
        )

        logger.info(f"Created evidence annotation {annotation_dict['annotation_id']} by auditor {current_user.id}")
        
        return {
            "annotation": annotation_dict,
            "message": "Evidence annotation created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating evidence annotation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create evidence annotation"
        )

@auditor_router.get("/evidence/{evidence_id}/annotations", response_model=List[Dict[str, Any]])
@require_role(UserRole.AUDITOR)
async def get_evidence_annotations(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get all annotations for specific evidence"""
    try:
        # Fetch annotations from database
        annotations = await DatabaseOperations.find_many(
            "mvp1_evidence_annotations",
            {"evidence_id": evidence_id},
            sort=[("created_at", -1)]
        )

        logger.info(f"Retrieved {len(annotations)} annotations for evidence {evidence_id}")
        return annotations

    except Exception as e:
        logger.error(f"Error getting evidence annotations for {evidence_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evidence annotations"
        )

# =====================================
# FEEDBACK AND APPROVAL ENDPOINTS
# =====================================

@auditor_router.post("/feedback", response_model=Dict[str, Any])
@require_role(UserRole.AUDITOR)
async def submit_feedback(
    feedback: FeedbackSubmission,
    current_user: MVP1User = Depends(get_current_user)
):
    """Submit auditor feedback on analyst submission"""
    try:
        # Check if submission exists
        submission = await DatabaseOperations.find_one("mvp1_intake_forms", {"id": feedback.submission_id})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Create feedback object
        feedback_dict = feedback.dict(exclude={"created_at", "auditor_id"}) 
        feedback_dict["id"] = f"FB-{uuid.uuid4().hex[:8].upper()}"
        feedback_dict["auditor_id"] = current_user.id
        feedback_dict["auditor_name"] = current_user.name
        feedback_dict["organization_id"] = current_user.organization_id
        feedback_dict["created_at"] = datetime.utcnow()
        
        if "feedback_id" not in feedback_dict or not feedback_dict["feedback_id"]:
             feedback_dict["feedback_id"] = feedback_dict["id"]

        # Save to database
        await DatabaseOperations.insert_one("mvp1_auditor_feedback", feedback_dict)

        # Update submission status based on feedback type
        ftype = feedback.feedback_type.lower()
        new_status = "under_review"
        if "approve" in ftype:
            new_status = "approved"
        elif "reject" in ftype:
            new_status = "rejected"
        elif "revision" in ftype:
            new_status = "requires_revision"

        # Update submission status
        await DatabaseOperations.update_one(
            "mvp1_intake_forms",
            {"id": feedback.submission_id},
            {
                "status": new_status, 
                "workflow_stage": "auditor_review_complete" if new_status in ["approved", "rejected"] else "revision_required",
                "reviewed_at": datetime.utcnow(), 
                "reviewed_by": current_user.id
            }
        )

        # Log feedback submission
        await _log_audit_event(
            organization_id=current_user.organization_id,
            action_type="feedback_submitted", 
            action_description=f"Auditor feedback submitted: {feedback.feedback_type}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="submission",
            target_id=feedback.submission_id
        )

        logger.info(f"Submitted feedback {feedback_dict['id']} by auditor {current_user.id}")
        
        return {
            "feedback": feedback_dict,
            "submission_status": new_status,
            "message": f"Feedback submitted successfully - Submission {new_status}"
        }

    except Exception as e:
        logger.error(f"Error submitting feedback for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@auditor_router.get("/feedback/{submission_id}", response_model=List[Dict[str, Any]])
@require_role(UserRole.AUDITOR)
async def get_submission_feedback(
    submission_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get all feedback for specific submission"""
    try:
        # Fetch feedback from database
        feedback_history = await DatabaseOperations.find_many(
            "mvp1_auditor_feedback",
            {"submission_id": submission_id},
            sort=[("created_at", -1)]
        )
        
        logger.info(f"Retrieved {len(feedback_history)} feedback records for submission {submission_id}")
        return feedback_history

    except Exception as e:
        logger.error(f"Error getting submission feedback for {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission feedback"
        )

@auditor_router.get("/workflow/{submission_id}", response_model=ApprovalWorkflow)
@require_role(UserRole.AUDITOR)
async def get_approval_workflow(
    submission_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get approval workflow status and history"""
    try:
        # Get submission
        submission = await DatabaseOperations.find_one("mvp1_intake_forms", {"id": submission_id})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Get feedback history (for timeline)
        feedbacks = await DatabaseOperations.find_many(
            "mvp1_auditor_feedback", 
            {"submission_id": submission_id},
            sort=[("created_at", 1)]
        )

        timeline_events = []
        
        # Add submission event (approx from submitted_at)
        if submission.get("submitted_at"):
             sub_date = submission.get("submitted_at")
             if isinstance(sub_date, str):
                 try:
                     sub_date = datetime.fromisoformat(sub_date.replace('Z', '+00:00'))
                 except:
                     sub_date = datetime.utcnow() # Fallback

             timeline_events.append({
                 "stage": "submission",
                 "actor": "Analyst", # Ideally fetch name
                 "action": "submitted",
                 "timestamp": sub_date,
                 "comments": "Initial submission"
             })

        # Add feedback events
        for fb in feedbacks:
             fb_date = fb.get("created_at")
             if isinstance(fb_date, str):
                 try:
                     fb_date = datetime.fromisoformat(fb_date.replace('Z', '+00:00'))
                 except:
                     fb_date = datetime.utcnow()

             timeline_events.append({
                 "stage": "auditor_review",
                 "actor": fb.get("auditor_name", "Auditor"),
                 "action": fb.get("feedback_type", "reviewed"),
                 "timestamp": fb_date,
                 "comments": fb.get("overall_assessment", "")
             })
             
        # Current status logic
        current_status = submission.get("status", "pending")
        
        # Pending actions
        pending_actions = []
        if current_status in ["submitted", "under_review"]:
             pending_actions.append({
                 "action_required": "auditor_review",
                 "assigned_to": current_user.name,
                 "due_date": datetime.utcnow() + timedelta(days=2),
                 "priority": "medium"
             })
        elif current_status == "requires_revision":
             pending_actions.append({
                 "action_required": "analyst_revision",
                 "assigned_to": "Analyst",
                 "due_date": datetime.utcnow() + timedelta(days=2),
                 "priority": "high"
             })

        workflow = ApprovalWorkflow(
            workflow_id=f"WF-{uuid.uuid4().hex[:8].upper()}",
            submission_id=submission_id,
            current_status=current_status,
            approval_history=timeline_events,
            pending_actions=pending_actions,
            workflow_stage=submission.get("workflow_stage", "review"),
            estimated_completion=datetime.utcnow() + timedelta(days=5)
        )
        
        logger.info(f"Retrieved approval workflow for submission {submission_id}")
        return workflow

    except Exception as e:
        logger.error(f"Error getting approval workflow for {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval workflow"
        )

# =====================================
# HELPER FUNCTIONS
# =====================================

async def _log_audit_event(
    organization_id: str,
    action_type: str,
    action_description: str,
    actor_id: str,
    actor_name: str,
    actor_role: UserRole,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    changes_made: Optional[Dict[str, Any]] = None
):
    """Log audit events for auditor actions"""
    audit_entry = AuditLogEntry(
        organization_id=organization_id,
        engagement_id=engagement_id,
        action_type=action_type,
        action_description=action_description,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        target_type=target_type,
        target_id=target_id,
        changes_made=changes_made or {},
        category="auditor_workflow"
    )
    
    await DatabaseOperations.insert_one("mvp1_audit_logs", audit_entry.dict())
    logger.info(f"Audit event logged: {action_type} by {actor_name} ({actor_role})")

# Health check endpoint for auditor workflow
@auditor_router.get("/health")
async def auditor_workflow_health():
    """Health check for auditor workflow module"""
    return {
        "module": "MVP 1 Week 4 - Auditor Workflow",
        "version": "1.0.0",
        "status": "healthy",
        "capabilities": [
            "real_time_dashboard",
            "analyst_submission_access", 
            "evidence_annotation",
            "feedback_submission",
            "approval_workflows",
            "audit_trail_continuity",
            "role_based_restrictions"
        ],
        "endpoints": 11,
        "integration_points": [
            "Analyst Workflow (Week 3)",
            "Admin Portal (Week 2)", 
            "Authentication Bridge",
            "AI Analysis Engine"
        ],
        "last_health_check": datetime.utcnow().isoformat()
    }

class GapValidationRequest(BaseModel):
    gap_id: str
    status: str
    comments: Optional[str] = None

@auditor_router.post("/gap-reviews")
async def validate_gap(
    request: GapValidationRequest,
    background_tasks: BackgroundTasks,
    current_user: MVP1User = Depends(get_current_user)
):
    """Validate a gap analysis finding"""


    try:
        review_id = f"GAP-REV-{uuid.uuid4().hex[:8].upper()}"
        review_doc = {
            "id": review_id,
            "gap_id": request.gap_id,
            "status": request.status,
            "comments": request.comments,
            "auditor_id": current_user.id,
            "auditor_name": current_user.name,
            "organization_id": current_user.organization_id,
            "created_at": datetime.utcnow()
        }

        await DatabaseOperations.insert_one("mvp1_auditor_feedback", review_doc)

        # Map frontend review status to DB form status
        status_map = {
            "approved": "approved",
            "ai_verified": "approved",
            "rejected": "rejected",
            "gap_found": "needs_remediation",
            "requires_revision": "requires_revision"
        }
        
        new_db_status = status_map.get(request.status.strip().lower(), "under_review")

        # Update intake form status — also write auditor_comments so analyst can see feedback
        update_fields = {
            "status": new_db_status,
            "last_modified_at": datetime.utcnow(),
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": current_user.id,
            "auditor_name": current_user.name,
            "auditor_comments": request.comments or ""
        }
        await DatabaseOperations.update_one(
            "mvp1_intake_forms",
            {"id": request.gap_id},
            update_fields
        )

        # If rejected or gap_found, update intake form status to needs_remediation and trigger remediation plan
        if request.status and request.status.strip().lower() in ["rejected", "gap_found"]:
            # Fetch ai_details for the gap
            form = await DatabaseOperations.find_one("mvp1_intake_forms", {"id": request.gap_id})
            ai_details = form.get("ai_details", {}) or (form.get("ai_analysis_results") or {}) if form else {}
            background_tasks.add_task(generate_remediation_plan, request.gap_id, ai_details, request.comments)

        # Log validation
        await _log_audit_event(
            organization_id=current_user.organization_id,
            action_type="gap_validation",
            action_description=f"Gap {request.gap_id} validated: {request.status}",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            target_type="gap",
            target_id=request.gap_id
        )

        return {
            "message": "Gap validation submitted successfully",
            "review_id": review_id,
            "status": request.status
        }
    except Exception as e:
        logger.error(f"Gap validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Engagement Review Endpoint (by engagement_id) ===
@auditor_router.get("/engagement-review/{engagement_id}", response_model=Dict[str, Any])
@require_role(UserRole.AUDITOR)
async def get_engagement_review_details(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get all analyst submissions, AI recommendations, and evidence files for a given engagement_id"""
    try:
        # Check auditor assignment
        engagement = await DatabaseOperations.find_one("mvp1_engagements", {"id": engagement_id})
        if not engagement or current_user.id not in engagement.get("assigned_auditors", []):
            raise HTTPException(status_code=403, detail="You are not assigned to this engagement")

        # Fetch all submissions for this engagement
        submissions = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id}
        )

        # Fetch all analysts for mapping
        analyst_ids = list(set([s.get("analyst_id") for s in submissions if s.get("analyst_id")]))
        analysts = await DatabaseOperations.find_many("mvp1_users", {"id": {"$in": analyst_ids}})
        analyst_map = {a["id"]: a.get("name", "Unknown Analyst") for a in analysts}

        # Fetch all evidence for this engagement
        evidence_list = await DatabaseOperations.find_many(
            "mvp1_evidence",
            {"engagement_id": engagement_id}
        )
        evidence_map = {}
        for ev in evidence_list:
            evidence_map[ev["id"]] = {
                "evidence_id": ev["id"],
                "filename": ev.get("filename", ev.get("original_filename")),
                "file_type": ev.get("content_type", "unknown"),
                "file_size": f"{round(ev.get('file_size', 0)/1024, 1)} KB",
                "upload_date": ev.get("uploaded_at", datetime.utcnow()).isoformat() if isinstance(ev.get("uploaded_at"), datetime) else str(ev.get("uploaded_at", "")),
                "ai_analysis": ev.get("ai_analysis_results") or {},
                "annotations_count": 0
            }

        # Build comprehensive submission details
        submission_details = []
        for s in submissions:
            # Evidence files for this submission
            evidence_files = []
            for eid in (s.get("evidence_ids") or []):
                if eid in evidence_map:
                    evidence_files.append(evidence_map[eid])

            ai_recommendations = (s.get("ai_analysis_results") or {}).get("recommendations") or []
            formatted_recommendations = ai_recommendations if isinstance(ai_recommendations, list) else []

            submission_details.append({
                "submission_id": s["id"],
                "engagement_id": s.get("engagement_id"),
                "analyst_id": s.get("analyst_id"),
                "analyst_name": analyst_map.get(s.get("analyst_id"), "Unknown Analyst"),
                "framework": s.get("framework_id", "Unknown"),
                "control_id": s.get("control_id"),
                "form_responses": s.get("form_data") or {},
                "ai_recommendations": formatted_recommendations,
                "evidence_files": evidence_files,
                "submission_date": s.get("submitted_at", datetime.utcnow()).isoformat() if isinstance(s.get("submitted_at"), datetime) else str(s.get("submitted_at", "")),
                "status": s.get("status", "pending"),
                "completion_percentage": s.get("completion_percentage", 95.0) if s.get("completion_percentage") else 95.0,
                "ai_confidence_score": round(s.get("ai_confidence_score", 0) * 100, 1) if s.get("ai_confidence_score") else 0.0
            })

        return {
            "engagement_id": engagement_id,
            "engagement_name": engagement.get("name", engagement_id),
            "submissions": submission_details,
            "evidence": list(evidence_map.values())
        }
    except Exception as e:
        logger.error(f"Error getting engagement review details for {engagement_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement review details"
        )


# === Engagement Status Endpoint (for frontend stage tracking) ===
@auditor_router.get("/engagements/{engagement_id}/status")
@require_role(UserRole.AUDITOR)
async def get_engagement_status(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get engagement stage status: forms filled, documents uploaded, AI run, in auditor review"""
    try:
        # Check auditor assignment
        engagement = await DatabaseOperations.find_one("mvp1_engagements", {"id": engagement_id})
        if not engagement or current_user.id not in engagement.get("assigned_auditors", []):
            raise HTTPException(status_code=403, detail="You are not assigned to this engagement")

        # Check for forms submitted
        submitted_forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id, "status": {"$ne": "draft"}},
            limit=1
        )
        forms_found = len(submitted_forms) > 0
        
        # Check for evidence uploaded
        uploaded_evidence = await DatabaseOperations.find_many(
            "mvp1_evidence",
            {"engagement_id": engagement_id},
            limit=1
        )
        documents_found = len(uploaded_evidence) > 0
        
        # Check for AI analysis — look for any auditor feedback/findings which indicates AI has analyzed
        auditor_feedback = await DatabaseOperations.find_many(
            "mvp1_auditor_feedback",
            {"engagement_id": engagement_id},
            limit=1
        )
        ai_run = len(auditor_feedback) > 0  # If there's auditor feedback, AI analysis has been run
        
        # Check if in auditor review stage
        current_state = engagement.get("current_review_state", "").lower()
        is_in_review_state = current_state in ["auditor_review", "under_review", "in_review"]
        
        # Also check form statuses for under_review or approved
        review_submissions = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id, "status": {"$in": ["under_review", "requires_revision", "approved"]}},
            limit=1
        )
        has_reviewed_forms = len(review_submissions) > 0
        
        in_auditor_stage = is_in_review_state or has_reviewed_forms or len(auditor_feedback) > 0
        
        # Get completion percentage
        completion_percentage = engagement.get("completion_percentage", 0)
        
        return {
            "engagement_id": engagement_id,
            "forms_found": forms_found,
            "documents_found": documents_found,
            "ai_run": ai_run,
            "in_auditor_stage": in_auditor_stage,
            "completion_percentage": completion_percentage,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get engagement status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement status"
        )