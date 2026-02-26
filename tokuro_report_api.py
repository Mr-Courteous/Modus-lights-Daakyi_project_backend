"""
Tokuro AI Report Generation API
FastAPI endpoints for DAAKYI's AI-powered report generation system

Features:
- Report generation request handling
- Multi-format export support (PDF, PPTX, DOCX, XLSX)
- Real-time progress tracking
- Template management
- Download management with expiration
- Analytics and usage tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import uuid
from pathlib import Path

from models import (
    User, ReportGenerationRequest, ReportGeneration, ReportTemplate,
    ReportType, ReportFormat, ReportStatus, ReportDownloadResponse,
    ReportAnalytics, TokuroAIReportData
)
from database import DatabaseOperations
from mvp1_auth import get_current_user, require_permission, require_admin
from mvp1_models import MVP1User
from tokuro_report_engine import TokuroReportEngine

logger = logging.getLogger(__name__)

# Initialize router with prefix
router = APIRouter(
    prefix="/api/reports",
    tags=["Tokuro AI Reports"],
    responses={404: {"description": "Not found"}}
)

# Initialize report engine
report_engine = TokuroReportEngine()

# ==================== REPORT GENERATION ENDPOINTS ====================

@router.post("/generate")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Generate a new report using Tokuro AI
    Supports multiple formats: PDF, PPTX, DOCX, XLSX
    """
    try:
        # Validate user permissions
        if request.assessment_id:
            # Check if user has access to the engagement
            engagement = await DatabaseOperations.find_one(
                "mvp1_engagements",
                {
                    "id": request.assessment_id,
                    "organization_id": current_user.organization_id
                }
            )
            if not engagement:
                raise HTTPException(
                    status_code=404,
                    detail="Engagement not found or access denied"
                )
        
        # Create report generation record
        report_config = ReportGeneration(
            name=request.name,
            description=request.description,
            assessment_id=request.assessment_id,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            report_type=request.report_type,
            report_format=request.report_format,
            template_id=request.template_id or "default_basic",
            include_tokuro_ai=request.include_tokuro_ai,
            include_executive_summary=request.include_executive_summary,
            include_remediation_plan=request.include_remediation_plan,
            custom_branding=request.custom_branding
        )
        
        # Convert to dict and serialize datetime fields for database storage
        report_dict = report_config.dict()
        for key in ['created_at', 'generation_started_at', 'generation_completed_at', 'download_expires_at', 'last_accessed_at']:
            if report_dict.get(key) and isinstance(report_dict[key], datetime):
                report_dict[key] = report_dict[key].isoformat()
        
        # Save to database
        await DatabaseOperations.insert_one(
            "report_generations",
            report_dict
        )
        
        # Start background report generation
        background_tasks.add_task(
            _generate_report_background,
            report_config
        )
        
        logger.info(f"Report generation started: {report_config.id}")
        
        return {
            "report_id": report_config.id,
            "status": report_config.status,
            "message": "Report generation started",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Report generation request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start report generation: {str(e)}"
        )

async def _generate_report_background(report_config: ReportGeneration):
    """Background task for report generation"""
    try:
        output_path = await report_engine.generate_report(report_config)
        logger.info(f"Report generated successfully: {output_path}")
    except Exception as e:
        logger.error(f"Background report generation failed: {str(e)}")

@router.get("/")
async def get_reports(
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Get list of reports for the current user's organization
    Supports filtering by type and status
    """
    try:
        # Build filter
        filter_criteria = {
            "organization_id": current_user.organization_id
        }
        
        if report_type:
            filter_criteria["report_type"] = report_type.value
        
        if status:
            filter_criteria["status"] = status.value
        
        # Get reports
        reports = await DatabaseOperations.find_many(
            "report_generations",
            filter_criteria,
            sort=[("created_at", -1)],
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total_count = await DatabaseOperations.count_documents(
            "report_generations",
            filter_criteria
        )
        
        return {
            "reports": reports,
            "total_count": total_count,
            "returned_count": len(reports)
        }
        
    except Exception as e:
        logger.error(f"Get reports failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch reports"
        )

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get specific report details"""
    try:
        report = await DatabaseOperations.find_one(
            "report_generations",
            {
                "id": report_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        # Update last accessed timestamp
        await DatabaseOperations.update_one(
            "report_generations",
            {"id": report_id},
            {"last_accessed_at": datetime.utcnow()}
        )
        
        return {"report": report}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch report"
        )

@router.get("/{report_id}/status")
async def get_report_status(
    report_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get real-time report generation status and progress"""
    try:
        status_info = await report_engine.get_report_status(report_id)
        
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        # Verify user access
        report = await DatabaseOperations.find_one(
            "report_generations",
            {
                "id": report_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        return {
            "report_id": report_id,
            "status": status_info["status"],
            "progress_percentage": status_info.get("progress_percentage", 0),
            "error_message": status_info.get("error_message"),
            "estimated_completion": status_info.get("generation_started_at"),
            "is_ready": status_info["status"] == "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report status failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch report status"
        )

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Download generated report file"""
    try:
        # Get report record
        report = await DatabaseOperations.find_one(
            "report_generations",
            {
                "id": report_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        # Check if report is completed
        if report.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail="Report is not ready for download"
            )
        
        # Check if file exists
        file_path = report.get("output_file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Report file not found"
            )
        
        # Check download expiration
        expires_at = report.get("download_expires_at")
        if expires_at and datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.utcnow():
            raise HTTPException(
                status_code=410,
                detail="Download link has expired"
            )
        
        # Update download count/timestamp
        await DatabaseOperations.update_one(
            "report_generations",
            {"id": report_id},
            {
                "last_accessed_at": datetime.utcnow(),
                "status": "downloaded"
            }
        )
        
        # Determine content type
        content_type_map = {
            'pdf': 'application/pdf',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        file_extension = Path(file_path).suffix[1:]  # Remove dot
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            filename=report.get("output_filename"),
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download report failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download report"
        )


@router.get("/download/{report_id}")
async def download_report_by_id(
    report_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Alternate download route: /api/reports/download/{report_id} - serves the generated file"""
    try:
        # Reuse same logic as previous download endpoint
        report = await DatabaseOperations.find_one(
            "report_generations",
            {"id": report_id, "organization_id": current_user.organization_id}
        )

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Report is not ready for download")

        file_path = report.get("output_file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")

        expires_at = report.get("download_expires_at")
        if expires_at and datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Download link has expired")

        # Update metadata
        await DatabaseOperations.update_one(
            "report_generations",
            {"id": report_id},
            {"last_accessed_at": datetime.utcnow(), "status": "downloaded"}
        )

        file_extension = Path(file_path).suffix[1:]
        content_type_map = {
            'pdf': 'application/pdf',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        content_type = content_type_map.get(file_extension, 'application/octet-stream')

        return FileResponse(path=file_path, filename=report.get('output_filename'), media_type=content_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download (by id) failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download report")

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Delete a report and its associated files"""
    try:
        # Get report record
        report = await DatabaseOperations.find_one(
            "report_generations",
            {
                "id": report_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        # Delete physical file if exists
        file_path = report.get("output_file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        await DatabaseOperations.delete_one(
            "report_generations",
            {"id": report_id}
        )
        
        logger.info(f"Report deleted: {report_id}")
        
        return {
            "message": "Report deleted successfully",
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete report failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete report"
        )

# ==================== TEMPLATE MANAGEMENT ENDPOINTS ====================

@router.get("/templates/")
async def get_report_templates(
    report_type: Optional[ReportType] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get available report templates"""
    try:
        # Build filter for templates
        filter_criteria = {
            "$or": [
                {"organization_id": current_user.organization_id},
                {"organization_id": None}  # System templates
            ],
            "is_active": True
        }
        
        if report_type:
            filter_criteria["report_type"] = report_type.value
        
        # Get templates
        templates = await DatabaseOperations.find_many(
            "report_templates",
            filter_criteria,
            sort=[("name", 1)]
        )
        
        return {
            "templates": templates,
            "total_count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Get templates failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch templates"
        )

@router.post("/templates/")
@require_admin
async def create_report_template(
    template_data: dict,
    current_user: MVP1User = Depends(get_current_user)
):
    """Create a new report template (Admin only)"""
    try:
        template = ReportTemplate(
            **template_data,
            organization_id=current_user.organization_id,
            created_by=current_user.id
        )
        
        # Save template
        await DatabaseOperations.insert_one(
            "report_templates",
            template.dict()
        )
        
        return {
            "template": template.dict(),
            "message": "Template created successfully"
        }
        
    except Exception as e:
        logger.error(f"Create template failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create template"
        )

@router.put("/templates/{template_id}")
@require_admin
async def update_report_template(
    template_id: str,
    template_data: dict,
    current_user: MVP1User = Depends(get_current_user)
):
    """Update a report template (Admin only)"""
    try:
        # Check if template exists and user has permission
        template = await DatabaseOperations.find_one(
            "report_templates",
            {
                "id": template_id,
                "$or": [
                    {"organization_id": current_user.organization_id},
                    {"organization_id": None}
                ]
            }
        )
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )
        
        # Update template
        template_data["updated_at"] = datetime.utcnow()
        
        await DatabaseOperations.update_one(
            "report_templates",
            {"id": template_id},
            template_data
        )
        
        return {
            "message": "Template updated successfully",
            "template_id": template_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update template"
        )

# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/")
async def get_report_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: MVP1User = Depends(get_current_user)
):
    """Get report generation analytics for the organization"""
    try:
        # Date filter
        start_date = datetime.utcnow() - timedelta(days=days)
        
        filter_criteria = {
            "organization_id": current_user.organization_id,
            "created_at": {"$gte": start_date}
        }
        
        # Get all reports for the period
        reports = await DatabaseOperations.find_many(
            "report_generations",
            filter_criteria
        )
        
        # Calculate analytics
        analytics = ReportAnalytics()
        analytics.total_reports = len(reports)
        
        # Reports by type
        for report in reports:
            report_type = report.get("report_type", "unknown")
            analytics.reports_by_type[report_type] = analytics.reports_by_type.get(report_type, 0) + 1
        
        # Reports by format
        for report in reports:
            report_format = report.get("report_format", "unknown")
            analytics.reports_by_format[report_format] = analytics.reports_by_format.get(report_format, 0) + 1
        
        # Reports by status
        for report in reports:
            status = report.get("status", "unknown")
            analytics.reports_by_status[status] = analytics.reports_by_status.get(status, 0) + 1
        
        # Calculate average generation time
        completed_reports = [r for r in reports if r.get("status") == "completed" and r.get("generation_started_at") and r.get("generation_completed_at")]
        if completed_reports:
            total_time = 0
            for report in completed_reports:
                start_time = datetime.fromisoformat(report["generation_started_at"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(report["generation_completed_at"].replace('Z', '+00:00'))
                total_time += (end_time - start_time).total_seconds()
            
            analytics.average_generation_time_seconds = total_time / len(completed_reports)
        
        # Tokuro AI usage percentage
        tokuro_reports = [r for r in reports if r.get("include_tokuro_ai", False)]
        if reports:
            analytics.tokuro_ai_usage_percentage = (len(tokuro_reports) / len(reports)) * 100
        
        # Most used templates
        template_usage = {}
        for report in reports:
            template_id = report.get("template_id", "unknown")
            template_usage[template_id] = template_usage.get(template_id, 0) + 1
        
        analytics.most_used_templates = [
            {"template_id": template_id, "usage_count": count}
            for template_id, count in sorted(template_usage.items(), key=lambda x: x[1], reverse=True)
        ][:5]  # Top 5
        
        return {
            "analytics": analytics.dict(),
            "period_days": days,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Get analytics failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch analytics"
        )

# ==================== ADMIN ENDPOINTS ====================

@router.post("/cleanup")
@require_admin
async def cleanup_old_reports(
    days_old: int = Query(30, ge=1, le=365),
    current_user: MVP1User = Depends(get_current_user)
):
    """Clean up old report files (Admin only)"""
    try:
        cleaned_count = await report_engine.cleanup_old_reports(days_old)
        
        return {
            "message": f"Cleaned up {cleaned_count} old reports",
            "cleaned_count": cleaned_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup old reports"
        )

@router.get("/system/status")
@require_admin
async def get_system_status(
    current_user: MVP1User = Depends(get_current_user)
):
    """Get report generation system status (Admin only)"""
    try:
        # Count reports by status
        pending_count = await DatabaseOperations.count_documents(
            "report_generations",
            {"status": "pending"}
        )
        
        generating_count = await DatabaseOperations.count_documents(
            "report_generations",
            {"status": "generating"}
        )
        
        completed_count = await DatabaseOperations.count_documents(
            "report_generations",
            {"status": "completed"}
        )
        
        failed_count = await DatabaseOperations.count_documents(
            "report_generations",
            {"status": "failed"}
        )
        
        # Check disk space
        output_dir = Path("generated_reports")
        total_size = sum(f.stat().st_size for f in output_dir.glob('**/*') if f.is_file())
        
        return {
            "system_status": "operational",
            "report_queue": {
                "pending": pending_count,
                "generating": generating_count,
                "completed": completed_count,
                "failed": failed_count
            },
            "storage": {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            "tokuro_ai_status": "operational",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Get system status failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch system status"
        )