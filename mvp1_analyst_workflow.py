# === Remediation Plan Background Task ===
import asyncio

async def generate_remediation_plan(gap_id: str, ai_details: dict, auditor_comments: str):
    """Background task to generate a remediation summary for a flagged gap."""
    # Compose remediation summary using AI details and auditor comments
    summary = "Remediation Plan: "
    if ai_details:
        summary += f"AI Recommendations: {ai_details.get('recommendations', [])}. "
        summary += f"Key Findings: {ai_details.get('key_findings', [])}. "
    if auditor_comments:
        summary += f"Auditor Notes: {auditor_comments}. "
    summary = summary.strip()
    # Update the intake form with remediation_summary
    await DatabaseOperations.update_one(
        "mvp1_intake_forms",
        {"id": gap_id},
        {"remediation_summary": summary, "remediation_generated_at": datetime.utcnow()}
    )
"""
MVP 1 Week 3 - Analyst Workflow API
Comprehensive analyst workflow with current state forms, evidence upload, and AI analysis

Features:
- Framework-specific dynamic intake forms
- Evidence upload system with smart metadata
- AI-powered analysis and recommendations
- Progress tracking and notification management
- Real-time collaboration with auditors
"""

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import uuid
import os
import hashlib
import aiofiles
from pathlib import Path

from mvp1_models import (
    MVP1User, UserRole, ComplianceEngagement, EngagementControl,
    CurrentStateIntakeForm, ComplianceEvidence, EvidenceStatus,
    AIProcessingJob, AIProcessingStatus, SystemRecommendation,
    CollaborationActivity
)
from mvp1_auth import get_current_user, require_role, ensure_organization_access
from database import DatabaseOperations
from multi_framework import get_multi_framework_engine, FrameworkType
import json

logger = logging.getLogger(__name__)

# Create analyst workflow router
analyst_router = APIRouter(prefix="/api/mvp1/analyst", tags=["Analyst Workflow"])

# File upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"}

# =====================================
# ANALYST DASHBOARD ENDPOINTS
# =====================================

@analyst_router.get("/dashboard")
@require_role(UserRole.ANALYST)
async def get_analyst_dashboard(current_user: MVP1User = Depends(get_current_user)):
    """Get analyst dashboard with assigned engagements and progress"""
    try:
        # Get assigned engagements
        engagements = await DatabaseOperations.find_many(
            "mvp1_engagements",
            {
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        # Calculate progress for each engagement
        engagement_progress = []
        total_forms_submitted = 0
        total_evidence_uploaded = 0
        
        for engagement in engagements:
            # Get controls for this engagement
            controls = await DatabaseOperations.find_many(
                "mvp1_engagement_controls",
                {"engagement_id": engagement["id"]}
            )

            # Get all forms for this engagement/analyst
            all_forms = await DatabaseOperations.find_many(
                "mvp1_intake_forms",
                {
                    "engagement_id": engagement["id"],
                    "analyst_id": current_user.id
                }
            )
            # Count forms with status in [submitted, under_review, approved, ai_verified]
            completed_forms = len([f for f in all_forms if f.get("status") in ["submitted", "under_review", "approved", "ai_verified"]])

            # Get uploaded evidence
            uploaded_evidence = await DatabaseOperations.find_many(
                "mvp1_evidence",
                {
                    "engagement_id": engagement["id"],
                    "uploaded_by": current_user.id
                }
            )

            # Calculate completion percentage
            total_controls = len(controls)
            evidence_count = len(uploaded_evidence)
            completion_percentage = (completed_forms / max(total_controls, 1)) * 100

            engagement_info = {
                "id": engagement["id"],
                "name": engagement["name"],
                "engagement_code": engagement["engagement_code"],
                "framework": engagement["framework"],
                "client_name": engagement["client_name"],
                "status": engagement["status"],
                "target_quarter": engagement["target_quarter"],
                "completion_percentage": round(completion_percentage, 1),
                "total_controls": total_controls,
                "completed_forms": completed_forms,
                "evidence_count": evidence_count,
                "pending_reviews": 0,  # Will be calculated from auditor feedback
                "last_activity": engagement.get("updated_at", engagement["created_at"])
            }

            engagement_progress.append(engagement_info)
            total_forms_submitted += completed_forms
            total_evidence_uploaded += evidence_count
        
        # Get recent notifications/activities
        recent_activities = await DatabaseOperations.find_many(
            "mvp1_collaboration_activities",
            {
                "organization_id": current_user.organization_id,
                "visible_to_roles": {"$in": [UserRole.ANALYST]}
            },
            limit=10,
            sort=[("timestamp", -1)]
        )
        
        # Get pending tasks/recommendations
        pending_recommendations = await DatabaseOperations.find_many(
            "mvp1_system_recommendations",
            {
                "organization_id": current_user.organization_id,
                "target_user_id": current_user.id,
                "status": "pending"
            },
            limit=5
        )
        
        return {
            "analyst_overview": {
                "assigned_engagements": len(engagements),
                "total_forms_submitted": total_forms_submitted,
                "total_evidence_uploaded": total_evidence_uploaded,
                "avg_completion_rate": round(sum(e["completion_percentage"] for e in engagement_progress) / max(len(engagement_progress), 1), 1)
            },
            "assigned_engagements": engagement_progress,
            "recent_activities": recent_activities,
            "pending_recommendations": pending_recommendations,
            "quick_actions": [
                {"action": "complete_intake_form", "label": "Complete Current State Form", "priority": "high"},
                {"action": "upload_evidence", "label": "Upload Evidence", "priority": "medium"},
                {"action": "view_feedback", "label": "View Auditor Feedback", "priority": "medium"},
                {"action": "check_progress", "label": "Check Progress", "priority": "low"}
            ]
        }
    except Exception as e:
        logger.error(f"Analyst dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analyst dashboard"
        )

@analyst_router.get("/engagements/{engagement_id}/controls")
@require_role(UserRole.ANALYST)
async def get_engagement_controls(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get all controls for an engagement"""
    try:
        # Verify engagement access
        query = {"id": engagement_id, "organization_id": current_user.organization_id}
        if current_user.role != UserRole.ADMIN and current_user.role != "admin":
            query["assigned_analysts"] = {"$in": [current_user.id]}
            
        engagement = await DatabaseOperations.find_one("mvp1_engagements", query)
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
            
        # Get controls
        controls = await DatabaseOperations.find_many(
            "mvp1_engagement_controls",
            {"engagement_id": engagement_id}
        )
        
        # Auto-populate controls if none found
        if not controls:
            logger.info(f"No controls found for engagement {engagement_id}. Attempting to populate from framework template.")
            
            # Map engagement framework to multi-framework engine types
            framework_mapping = {
                "NIST CSF": FrameworkType.NIST_CSF_20,
                "NIST CSF 2.0": FrameworkType.NIST_CSF_20,
                "ISO 27001": FrameworkType.ISO_27001_2022,
                "ISO/IEC 27001:2022": FrameworkType.ISO_27001_2022,
                "SOC 2": FrameworkType.SOC_2,
                "SOC 2 Type I": FrameworkType.SOC_2,
                "GDPR": FrameworkType.GDPR,
                "Ghana CII Directives": FrameworkType.NIST_CSF_20 # Fallback to NIST for now
            }
            
            engagement_framework = engagement.get("framework")
            fw_type = framework_mapping.get(engagement_framework)
            
            if fw_type:
                engine = get_multi_framework_engine()
                # Ensure framework is active for this operation
                engine.activate_framework(fw_type)
                fw_controls = engine.get_framework_controls(fw_type)
                
                if fw_controls:
                    new_controls = []
                    for fw_c in fw_controls:
                        ec = EngagementControl(
                            engagement_id=engagement_id,
                            control_id=fw_c.id,
                            control_name=fw_c.id, # Use ID as name if name not available, but usually we have title
                            control_description=fw_c.description,
                            control_category=fw_c.category,
                            organization_id=current_user.organization_id
                        )
                        # We might want to use title for control_name if available
                        if hasattr(fw_c, 'title') and fw_c.title:
                            ec.control_name = fw_c.title
                            
                        new_controls.append(ec.dict())
                    
                    if new_controls:
                        await DatabaseOperations.insert_many("mvp1_engagement_controls", new_controls)
                        logger.info(f"Populated {len(new_controls)} controls for engagement {engagement_id} from {engagement_framework}")
                        controls = new_controls
        
        return {
            "controls": controls,
            "count": len(controls)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get engagement controls error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement controls"
        )
# =====================================
# CURRENT STATE INTAKE FORM ENDPOINTS
# =====================================

@analyst_router.get("/engagements/{engagement_id}/intake-forms")
@require_role(UserRole.ANALYST)
async def list_intake_forms(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """List all submitted intake forms for an engagement"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )

        forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id}
        )

        return {
            "intake_forms": [
                {
                    "id": f.get("id"),
                    "control_id": f.get("control_id"),
                    "control_title": f.get("control_title"),
                    "status": f.get("status", "draft"),
                    "completion_percentage": f.get("completion_percentage", 0),
                    "ai_confidence_score": f.get("ai_confidence_score"),
                    "last_modified_at": f.get("last_modified_at"),
                    "submitted_at": f.get("submitted_at"),
                    "framework_id": f.get("framework_id"),
                    "implementation_description": f.get("form_data", {}).get("implementation_description", "")
                        if isinstance(f.get("form_data"), dict) else "",
                }
                for f in (forms or [])
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List intake forms error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intake forms"
        )

@analyst_router.get("/engagements/{engagement_id}/intake-form")
@require_role(UserRole.ANALYST)
async def get_intake_form(
    engagement_id: str,
    control_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get current state intake form for engagement/control"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
        # Get framework-specific questions
        framework_questions = await get_framework_questions(engagement["framework"], control_id)
        
        # Get existing form if available
        existing_form = None
        if control_id:
            existing_form = await DatabaseOperations.find_one(
                "mvp1_intake_forms",
                {
                    "engagement_id": engagement_id,
                    "control_id": control_id,
                    "analyst_id": current_user.id
                }
            )
        
        # Get assigned analyst name
        assigned_analyst_name = None
        if engagement.get("assigned_analysts"):
            assigned_analysts = engagement["assigned_analysts"]
            if assigned_analysts:
                # Fetch the first assigned analyst's name
                analyst = await DatabaseOperations.find_one("mvp1_users", {"id": assigned_analysts[0]})
                assigned_analyst_name = analyst["name"] if analyst else None
        return {
            "engagement": {
                "id": engagement["id"],
                "name": engagement["name"],
                "framework": engagement["framework"],
                "client_name": engagement["client_name"],
                "assigned_analyst_name": assigned_analyst_name
            },
            "framework_questions": framework_questions,
            "existing_form": existing_form,
            "autosave_enabled": True,
            "validation_rules": get_validation_rules(engagement["framework"]),
            "allow_engagement_change": True,
            # Expose auditor feedback so analyst can see revision requests
            "auditor_review": {
                "status": existing_form.get("status") if existing_form else None,
                "auditor_comments": existing_form.get("auditor_comments") if existing_form else None,
                "auditor_name": existing_form.get("auditor_name") if existing_form else None,
                "reviewed_at": existing_form.get("reviewed_at").isoformat()
                    if existing_form and isinstance(existing_form.get("reviewed_at"), datetime)
                    else (str(existing_form.get("reviewed_at")) if existing_form and existing_form.get("reviewed_at") else None)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get intake form error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intake form"
        )

@analyst_router.post("/engagements/{engagement_id}/intake-form")
@require_role(UserRole.ANALYST)
async def submit_intake_form(
    engagement_id: str,
    form_data: Dict[str, Any],
    current_user: MVP1User = Depends(get_current_user)
):
    """Submit or save current state intake form"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
        # Check if wrapped in form_data key (common axios pattern)
        if "form_data" in form_data and len(form_data) == 1:
            form_data = form_data["form_data"]

        control_id = form_data.get("control_id")
        if not control_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Control ID is required"
            )
        
        # Extract nested responses if present (from updated MapAssess frontend)
        responses = form_data.get("responses", {})
        org_data = responses.get("organization") or responses.get("org_details") or {}
        assess_data = responses.get("assessment") or responses.get("control_assessment") or {}
        risk_data = responses.get("risk_analysis") or responses.get("risk_intelligence") or {}
        goals_data = responses.get("target_goals") or responses.get("compliance_goals") or {}

        # Create or update intake form
        form_id = str(uuid.uuid4())
        intake_form = CurrentStateIntakeForm(
            id=form_id,
            engagement_id=engagement_id,
            control_id=control_id,
            analyst_id=current_user.id,
            # Prefer nested structure if available, otherwise fallback to flat form_data
            implementation_status=assess_data.get("status") or form_data.get("implementation_status", "not_implemented"),
            implementation_description=assess_data.get("description") or form_data.get("implementation_description", f"Assessment for {org_data.get('name', '')}"),
            current_controls_in_place=assess_data.get("current_controls_in_place") or form_data.get("current_controls_in_place", []),
            identified_gaps=assess_data.get("identified_gaps") or form_data.get("identified_gaps", []),
            risk_assessment=risk_data.get("risk_assessment") or form_data.get("risk_assessment", "medium"),
            business_impact_if_failed=risk_data.get("business_impact_if_failed") or form_data.get("business_impact_if_failed", ""),
            required_resources=form_data.get("required_resources", []),
            estimated_implementation_time=form_data.get("estimated_implementation_time"),
            target_completion_date=form_data.get("target_completion_date"),
            current_documentation=form_data.get("current_documentation", []),
            evidence_gaps=form_data.get("evidence_gaps", []),
            status=form_data.get("status", "draft"),
            completion_percentage=calculate_form_completion(form_data),
            responses=responses if responses else None,
            organization_id=current_user.organization_id
        )
        
        # Check if form already exists
        existing_form = await DatabaseOperations.find_one(
            "mvp1_intake_forms",
            {
                "engagement_id": engagement_id,
                "control_id": control_id,
                "analyst_id": current_user.id
            }
        )
        
        if existing_form:
            # Update existing form
            await DatabaseOperations.update_one(
                "mvp1_intake_forms",
                {"id": existing_form["id"]},
                intake_form.dict()
            )
            form_id = existing_form["id"]
        else:
            # Create new form
            await DatabaseOperations.insert_one("mvp1_intake_forms", intake_form.dict())
        
        # Trigger AI analysis if form is submitted
        if intake_form.status == "submitted":
            await trigger_ai_analysis(form_id, "form_analysis", current_user.organization_id)
            
            # Log activity
            await log_collaboration_activity(
                organization_id=current_user.organization_id,
                engagement_id=engagement_id,
                activity_type="form_submitted",
                actor_id=current_user.id,
                actor_name=current_user.name,
                actor_role=current_user.role,
                activity_description=f"Current state form submitted for control {control_id}",
                visible_to_roles=[UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
            )
        
        return {
            "status": "success",
            "message": f"Form {'submitted' if intake_form.status == 'submitted' else 'saved'} successfully",
            "form_id": form_id,
            "completion_percentage": intake_form.completion_percentage,
            "ai_analysis_triggered": intake_form.status == "submitted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit intake form error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit intake form"
        )

@analyst_router.post("/engagements/{engagement_id}/bulk-auto-map")
@require_role(UserRole.ANALYST)
async def bulk_auto_map_forms(
    engagement_id: str,
    request: Optional[Dict[str, Any]] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Automatically create intake forms for selected controls in an engagement using AI baselines"""
    try:
        # Extract control_ids from request if present
        target_control_ids = None
        if request and "control_ids" in request:
            target_control_ids = request["control_ids"]

        # 1. Get engagement
        engagement = await DatabaseOperations.find_one("mvp1_engagements", {"id": engagement_id})
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # 2. Get all controls for this engagement
        controls = await DatabaseOperations.find_many("mvp1_engagement_controls", {"engagement_id": engagement_id})
        
        # 3. Get existing forms
        existing_forms = await DatabaseOperations.find_many("mvp1_intake_forms", {"engagement_id": engagement_id})
        existing_control_ids = {f["control_id"] for f in (existing_forms or [])}

        # 4. Filter controls that need mapping
        pending_controls = [c for c in (controls or []) if c.get("control_id") not in existing_control_ids]
        
        # 5. Further filter if specific IDs were provided
        if target_control_ids is not None:
            pending_controls = [c for c in pending_controls if c.get("control_id") in target_control_ids]

        if not pending_controls:
            return {
                "status": "success",
                "mapped_count": 0,
                "message": "No pending controls to map for the given selection."
            }

        results = []
        for ctrl in pending_controls:
            control_id = ctrl["control_id"]
            
            # Create a basic form with "submitted" status
            form_id = str(uuid.uuid4())
            intake_form = CurrentStateIntakeForm(
                id=form_id,
                engagement_id=engagement_id,
                control_id=control_id,
                analyst_id=current_user.id,
                implementation_status="partially_implemented",
                implementation_description=f"Auto-mapped: AI baseline assessment for {ctrl.get('control_name', control_id)}.",
                risk_assessment="medium",
                status="submitted",
                completion_percentage=85.0,
                organization_id=current_user.organization_id
            )
            
            await DatabaseOperations.insert_one("mvp1_intake_forms", intake_form.dict())
            
            # Trigger AI analysis for each
            await trigger_ai_analysis(form_id, "form_analysis", current_user.organization_id)
            
            results.append(control_id)

        # Log activity
        if results:
            await log_collaboration_activity(
                organization_id=current_user.organization_id,
                engagement_id=engagement_id,
                activity_type="bulk_form_submitted",
                actor_id=current_user.id,
                actor_name=current_user.name,
                actor_role=current_user.role,
                activity_description=f"Bulk auto-mapped {len(results)} intake forms using AI baselines.",
                visible_to_roles=[UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
            )

        return {
            "status": "success",
            "mapped_count": len(results),
            "mapped_control_ids": results
        }
    except Exception as e:
        logger.error(f"Bulk map error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk mapping failed: {str(e)}")

# =====================================
# EVIDENCE UPLOAD ENDPOINTS
# =====================================

@analyst_router.post("/engagements/{engagement_id}/evidence/upload")
@require_role(UserRole.ANALYST)
async def upload_evidence(
    engagement_id: str,
    control_id: str = Form(...),
    evidence_type: str = Form(...),
    evidence_description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    current_user: MVP1User = Depends(get_current_user)
):
    """Upload evidence files for engagement/control"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
        uploaded_files = []
        
        for file in files:
            # Validate file
            if file.size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds maximum size of 25MB"
                )
            
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file_extension} not allowed. Allowed types: {ALLOWED_EXTENSIONS}"
                )
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_id}{file_extension}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Generate file hash for integrity
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Create evidence record
            evidence = ComplianceEvidence(
                id=file_id,
                filename=safe_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file.size,
                file_type=file_extension[1:],  # Remove the dot
                mime_type=file.content_type or "application/octet-stream",
                file_hash=file_hash,
                engagement_id=engagement_id,
                control_id=control_id,
                evidence_type=evidence_type,
                evidence_description=evidence_description,
                status=EvidenceStatus.UPLOADED,
                processing_status=AIProcessingStatus.PENDING,
                uploaded_by=current_user.id,
                organization_id=current_user.organization_id
            )
            
            # Save evidence to database
            await DatabaseOperations.insert_one("mvp1_evidence", evidence.dict())
            
            # Trigger AI analysis
            await trigger_ai_analysis(file_id, "evidence_analysis", current_user.organization_id)
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "size": file.size,
                "type": evidence_type,
                "status": "uploaded"
            })
        
        # Log collaboration activity
        await log_collaboration_activity(
            organization_id=current_user.organization_id,
            engagement_id=engagement_id,
            activity_type="evidence_uploaded",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            activity_description=f"Uploaded {len(files)} evidence file(s) for control {control_id}",
            visible_to_roles=[UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
        )
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(files)} file(s)",
            "uploaded_files": uploaded_files,
            "ai_analysis_initiated": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload evidence error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload evidence"
        )

@analyst_router.get("/engagements/{engagement_id}/evidence")
@require_role(UserRole.ANALYST)
async def get_evidence_list(
    engagement_id: str,
    control_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get list of uploaded evidence for engagement/control"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
        # Build query
        query = {
            "engagement_id": engagement_id,
            "organization_id": current_user.organization_id
        }
        
        if control_id:
            query["control_id"] = control_id
        
        # Get evidence files
        evidence_files = await DatabaseOperations.find_many(
            "mvp1_evidence",
            query,
            sort=[("uploaded_at", -1)]
        )
        
        # Format response
        formatted_evidence = []
        for evidence in evidence_files:
            formatted_evidence.append({
                "id": evidence["id"],
                "filename": evidence["original_filename"],
                "size": evidence["file_size"],
                "type": evidence["evidence_type"],
                "description": evidence.get("evidence_description"),
                "status": evidence["status"],
                "ai_analysis_status": evidence.get("processing_status", "pending"),
                "ai_confidence_score": evidence.get("ai_confidence_score"),
                "uploaded_at": evidence["uploaded_at"],
                "auditor_reviewed": evidence.get("auditor_reviewed", False),
                "auditor_approval": evidence.get("auditor_approval"),
                "control_id": evidence["control_id"]
            })
        
        return {
            "evidence_files": formatted_evidence,
            "total_count": len(formatted_evidence),
            "filter_applied": {"control_id": control_id} if control_id else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get evidence list error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evidence list"
        )


# =====================================
# AI ANALYSIS ENDPOINTS
# =====================================

@analyst_router.get("/ai-analysis/{analysis_id}")
@require_role(UserRole.ANALYST)
async def get_ai_analysis_results(
    analysis_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get AI analysis results for form or evidence"""
    try:
        # Get AI processing job
        ai_job = await DatabaseOperations.find_one(
            "mvp1_ai_jobs",
            {
                "target_id": analysis_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not ai_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI analysis not found"
            )
        
        # Get associated recommendations
        recommendations = await DatabaseOperations.find_many(
            "mvp1_system_recommendations",
            {
                "target_user_id": current_user.id,
                "organization_id": current_user.organization_id
            }
        )
        
        return {
            "analysis_id": analysis_id,
            "status": ai_job["status"],
            "processing_model": ai_job.get("processing_model", "gpt-4o"),
            "confidence_score": ai_job.get("confidence_score"),
            "processing_results": ai_job.get("processing_results", {}),
            "generated_recommendations": ai_job.get("generated_recommendations", []),
            "identified_risks": ai_job.get("identified_risks", []),
            "processing_duration": ai_job.get("processing_duration_seconds"),
            "system_recommendations": recommendations,
            "created_at": ai_job["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get AI analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI analysis"
        )

@analyst_router.post("/evidence/{evidence_id}/analyze")
@require_role(UserRole.ANALYST)
async def trigger_evidence_analysis(
    evidence_id: str,
    request_data: Dict[str, Any],
    current_user: MVP1User = Depends(get_current_user)
):
    """Trigger AI analysis for an uploaded evidence file"""
    try:
        # Get the evidence record
        evidence = await DatabaseOperations.find_one(
            "mvp1_evidence",
            {
                "id": evidence_id,
                "organization_id": current_user.organization_id,
                "uploaded_by": current_user.id
            }
        )
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found or access denied"
            )
        
        # Check if already being processed
        existing_job = await DatabaseOperations.find_one(
            "mvp1_ai_jobs",
            {
                "target_id": evidence_id,
                "status": {"$in": ["pending", "processing"]}
            }
        )
        
        if existing_job:
            return {
                "status": "already_processing",
                "message": "Analysis already in progress for this evidence",
                "job_id": existing_job["id"]
            }
        
        # Update evidence status
        await DatabaseOperations.update_one(
            "mvp1_evidence",
            {"id": evidence_id},
            {"processing_status": AIProcessingStatus.PROCESSING}
        )
        
        # Trigger AI analysis
        await trigger_ai_analysis(evidence_id, "evidence_analysis", current_user.organization_id)
        
        # Log activity
        await log_collaboration_activity(
            organization_id=current_user.organization_id,
            engagement_id=evidence.get("engagement_id", ""),
            activity_type="evidence_analysis_started",
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            activity_description=f"AI analysis started for evidence: {evidence['original_filename']}",
            visible_to_roles=[UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
        )
        
        return {
            "status": "success",
            "message": "AI analysis initiated",
            "evidence_id": evidence_id,
            "processing_status": "processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trigger evidence analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger evidence analysis"
        )

@analyst_router.get("/evidence/{evidence_id}/status")
@require_role(UserRole.ANALYST)
async def get_evidence_status(
    evidence_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get processing status for an evidence file"""
    try:
        # Get the evidence record
        evidence = await DatabaseOperations.find_one(
            "mvp1_evidence",
            {
                "id": evidence_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        # Get the latest AI processing job for this evidence
        ai_jobs = await DatabaseOperations.find_many(
            "mvp1_ai_jobs",
            {"target_id": evidence_id},
            limit=1,
            sort=[("created_at", -1)]
        )
        ai_job = ai_jobs[0] if ai_jobs else None
        
        # Get system recommendations generated from this analysis
        recommendations = []
        if ai_job and ai_job.get("status") == "completed":
            recommendations = await DatabaseOperations.find_many(
                "mvp1_system_recommendations",
                {
                    "engagement_id": evidence.get("engagement_id"),
                    "control_id": evidence.get("control_id"),
                    "organization_id": current_user.organization_id
                },
                limit=5,
                sort=[("created_at", -1)]
            )
        
        return {
            "evidence_id": evidence_id,
            "filename": evidence.get("original_filename"),
            "processing_status": evidence.get("processing_status", "pending"),
            "ai_confidence_score": evidence.get("ai_confidence_score"),
            "ai_analysis_results": evidence.get("ai_analysis_results"),
            "ai_analysis_completed": evidence.get("ai_analysis_completed", False),
            "ai_job_status": ai_job.get("status") if ai_job else None,
            "system_recommendations": recommendations,
            "uploaded_at": evidence.get("uploaded_at"),
            "ai_processed_at": evidence.get("ai_processed_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get evidence status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evidence status"
        )


# =====================================
# HELPER FUNCTIONS
# =====================================

async def get_framework_questions(framework: str, control_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get framework-specific questions for intake form"""
    # Framework-specific question templates
    question_templates = {
        "ISO 27001": [
            {
                "id": "implementation_status",
                "type": "select",
                "question": "What is the current implementation status of this control?",
                "options": ["not_implemented", "partially_implemented", "fully_implemented"],
                "required": True
            },
            {
                "id": "implementation_description",
                "type": "textarea",
                "question": "Describe the current implementation of this control in detail:",
                "placeholder": "Provide a comprehensive description of how this control is currently implemented...",
                "required": True,
                "min_length": 50
            },
            {
                "id": "current_controls_in_place",
                "type": "multiselect",
                "question": "Which controls are currently in place?",
                "options": ["policies", "procedures", "technical_controls", "training", "monitoring", "documentation"],
                "required": False
            },
            {
                "id": "identified_gaps",
                "type": "checkbox_list",
                "question": "What gaps have you identified?",
                "options": ["missing_policy", "inadequate_procedure", "insufficient_training", "lack_of_monitoring", "poor_documentation", "technical_deficiency"],
                "required": False
            },
            {
                "id": "risk_assessment",
                "type": "select",
                "question": "What is your risk assessment for this control?",
                "options": ["low", "medium", "high", "critical"],
                "required": True
            },
            {
                "id": "business_impact_if_failed",
                "type": "textarea",
                "question": "Describe the business impact if this control fails:",
                "required": True
            }
        ],
        "NIST CSF": [
            {
                "id": "implementation_status", 
                "type": "select",
                "question": "Current maturity level for this function/category:",
                "options": ["not_implemented", "partially_implemented", "fully_implemented"],
                "required": True
            },
            {
                "id": "implementation_description",
                "type": "textarea", 
                "question": "Describe current cybersecurity practices for this category:",
                "required": True,
                "min_length": 50
            },
            {
                "id": "current_controls_in_place",
                "type": "multiselect",
                "question": "Which NIST CSF practices are currently implemented?",
                "options": ["identify", "protect", "detect", "respond", "recover"],
                "required": False
            }
        ],
        "SOC 2 Type I": [
            {
                "id": "implementation_status",
                "type": "select", 
                "question": "Trust Service Criteria implementation status:",
                "options": ["not_implemented", "partially_implemented", "fully_implemented"],
                "required": True
            },
            {
                "id": "implementation_description",
                "type": "textarea",
                "question": "Describe how this Trust Service Criteria is addressed:",
                "required": True,
                "min_length": 50
            }
        ],
        "Ghana CII Directives": [
            {
                "id": "implementation_status",
                "type": "select",
                "question": "CII Directive compliance status:",
                "options": ["not_implemented", "partially_implemented", "fully_implemented"], 
                "required": True
            },
            {
                "id": "implementation_description",
                "type": "textarea",
                "question": "Describe compliance with Ghana CII requirements:",
                "required": True,
                "min_length": 50
            }
        ]
    }
    
    base_questions = question_templates.get(framework, question_templates["ISO 27001"])
    
    # Add common questions
    common_questions = [
        {
            "id": "required_resources",
            "type": "multiselect",
            "question": "What resources are required for full implementation?",
            "options": ["budget", "personnel", "training", "technology", "external_support", "time"],
            "required": False
        },
        {
            "id": "estimated_implementation_time",
            "type": "number",
            "question": "Estimated implementation time (in hours):",
            "min": 1,
            "max": 1000,
            "required": False
        },
        {
            "id": "target_completion_date",
            "type": "date",
            "question": "Target completion date:",
            "required": False
        }
    ]
    
    return base_questions + common_questions

def get_validation_rules(framework: str) -> Dict[str, Any]:
    """Get validation rules for framework"""
    return {
        "required_fields": ["implementation_status", "implementation_description", "risk_assessment", "business_impact_if_failed"],
        "min_lengths": {
            "implementation_description": 50,
            "business_impact_if_failed": 20
        },
        "field_dependencies": {
            "identified_gaps": {
                "show_when": "implementation_status",
                "values": ["not_implemented", "partially_implemented"]
            }
        }
    }

def calculate_form_completion(form_data: Dict[str, Any]) -> float:
    """Calculate form completion percentage"""
    required_fields = ["implementation_status", "implementation_description", "risk_assessment", "business_impact_if_failed"]
    completed_fields = sum(1 for field in required_fields if form_data.get(field))
    return (completed_fields / len(required_fields)) * 100

async def trigger_ai_analysis(target_id: str, job_type: str, organization_id: str):
    """Trigger AI analysis for form or evidence"""
    try:
        ai_job = {
            "id": str(uuid.uuid4()),
            "job_type": job_type,
            "target_type": "evidence" if job_type == "evidence_analysis" else "intake_form",
            "target_id": target_id,
            "engagement_id": "",  # Will be filled from target
            "status": "processing",
            "processing_model": "gpt-4o",
            "processing_parameters": {"confidence_threshold": 0.7},
            "processing_start_time": datetime.utcnow(),
            "organization_id": organization_id,
            "created_at": datetime.utcnow()
        }
        
        await DatabaseOperations.insert_one("mvp1_ai_jobs", ai_job)
        
        # Simulate AI processing (in production, this would trigger actual AI service)
        # For now, we'll create mock analysis results
        mock_results = {
            "confidence_score": 0.85,
            "risk_level": "medium",
            "compliance_assessment": "Partially compliant with room for improvement",
            "mapped_controls": [
                "Ghana CSA Sec. 8.2 - Access Control",
                "ISO 27001 A.9.1.1 - Access Control Policy",
                "NIST AC-2 - Account Management"
            ],
            "compliance_frameworks": [
                "Ghana CSA Act 1038",
                "ISO 27001",
                "NIST CSF"
            ],
            "key_findings": [
                "Control implementation shows good foundation",
                "Documentation needs improvement",
                "Consider additional monitoring mechanisms"
            ],
            "recommendations": [
                "Enhance documentation procedures",
                "Implement automated monitoring",
                "Conduct regular training sessions"
            ]
        }
        
        # Update job with results and make accessible to auditors
        await DatabaseOperations.update_one(
            "mvp1_ai_jobs",
            {"id": ai_job["id"]},
            {
                "status": "completed",
                "processing_results": mock_results,
                "confidence_score": 0.85,
                "generated_recommendations": mock_results["recommendations"],
                "processing_end_time": datetime.utcnow(),
                "processing_duration_seconds": 2.5,
                "visible_to_roles": [UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
            }
        )
        # If this is evidence analysis, update the evidence record
        if job_type == "evidence_analysis":
            await DatabaseOperations.update_one(
                "mvp1_evidence",
                {"id": target_id},
                {
                    "processing_status": AIProcessingStatus.COMPLETED.value,
                    "ai_analysis_completed": True,
                    "ai_analysis_results": mock_results,
                    "ai_confidence_score": 0.85,
                    "ai_processed_at": datetime.utcnow(),
                    "visible_to_roles": [UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN]
                }
            )
        # Log collaboration activity for real-time auditor access
        await log_collaboration_activity(
            organization_id=organization_id,
            engagement_id=ai_job.get("engagement_id", ""),
            activity_type="ai_analysis_completed",
            actor_id="system",
            actor_name="AI Engine",
            actor_role=UserRole.ANALYST,
            activity_description="AI analysis completed and accessible to auditor.",
            visible_to_roles=[UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN],
            target_id=target_id,
            job_type=job_type
        )
    except Exception as e:
        logger.error(f"AI analysis trigger error: {str(e)}")
        # Update evidence as failed if there was an error
        if job_type == "evidence_analysis":
            try:
                await DatabaseOperations.update_one(
                    "mvp1_evidence",
                    {"id": target_id},
                    {
                        "processing_status": AIProcessingStatus.FAILED,
                        "ai_analysis_completed": False
                    }
                )
            except:
                pass


async def log_collaboration_activity(
    organization_id: str,
    engagement_id: str,
    activity_type: str,
    actor_id: str,
    actor_name: str,
    actor_role: UserRole,
    activity_description: str,
    visible_to_roles: List[UserRole],
    **kwargs
):
    """Log collaboration activity for real-time updates"""
    try:
        activity = CollaborationActivity(
            engagement_id=engagement_id,
            activity_type=activity_type,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            activity_description=activity_description,
            visible_to_roles=visible_to_roles,
            organization_id=organization_id,
            **kwargs
        )
        
        await DatabaseOperations.insert_one("mvp1_collaboration_activities", activity.dict())
    except Exception as e:
        logger.error(f"Log collaboration activity error: {str(e)}")

# =====================================
# PROGRESS TRACKING ENDPOINTS
# =====================================

@analyst_router.get("/engagements/{engagement_id}/progress")
@require_role(UserRole.ANALYST)
async def get_engagement_progress(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get detailed progress for specific engagement"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
        # Get controls for this engagement  
        controls = await DatabaseOperations.find_many(
            "mvp1_engagement_controls",
            {"engagement_id": engagement_id}
        )
        
        # Get submitted forms
        submitted_forms = await DatabaseOperations.find_many(
            "mvp1_intake_forms",
            {"engagement_id": engagement_id, "analyst_id": current_user.id}
        )
        
        # Get uploaded evidence
        uploaded_evidence = await DatabaseOperations.find_many(
            "mvp1_evidence",
            {"engagement_id": engagement_id, "uploaded_by": current_user.id}
        )
        
        # Build progress details
        control_progress = []
        for control in controls:
            control_forms = [f for f in submitted_forms if f["control_id"] == control.get("control_id")]
            control_evidence = [e for e in uploaded_evidence if e["control_id"] == control.get("control_id")]
            
            control_progress.append({
                "control_id": control.get("control_id"),
                "control_name": control.get("control_name", "Unknown Control"),
                "form_status": control_forms[0]["status"] if control_forms else "not_started",
                "form_completion": control_forms[0]["completion_percentage"] if control_forms else 0,
                "evidence_count": len(control_evidence),
                "last_updated": control_forms[0]["last_modified_at"] if control_forms else None
            })
        
        overall_completion = sum(cp["form_completion"] for cp in control_progress) / max(len(control_progress), 1)
        
        return {
            "engagement": {
                "id": engagement["id"],
                "name": engagement["name"],
                "framework": engagement["framework"],
                "status": engagement["status"]
            },
            "overall_progress": {
                "completion_percentage": round(overall_completion, 1),
                "total_controls": len(controls),
                "completed_forms": len([f for f in submitted_forms if f["status"] in ["submitted", "approved"]]),
                "total_evidence": len(uploaded_evidence),
                "pending_reviews": len([f for f in submitted_forms if f["status"] == "under_review"])
            },
            "control_progress": control_progress,
            "recent_activities": await DatabaseOperations.find_many(
                "mvp1_collaboration_activities",
                {"engagement_id": engagement_id},
                limit=5,
                sort=[("timestamp", -1)]
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get engagement progress error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement progress"
        )


# =====================================
# ENGAGEMENT STATUS ENDPOINT
# =====================================

@analyst_router.get("/engagements/{engagement_id}/status")
@require_role(UserRole.ANALYST)
async def get_engagement_status(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get engagement stage status: forms filled, documents uploaded, AI run, in auditor review"""
    try:
        # Verify engagement access
        engagement = await DatabaseOperations.find_one(
            "mvp1_engagements",
            {
                "id": engagement_id,
                "organization_id": current_user.organization_id,
                "assigned_analysts": {"$in": [current_user.id]}
            }
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found or access denied"
            )
        
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
        
        # Check if in auditor review stage — check current_review_state and form statuses
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