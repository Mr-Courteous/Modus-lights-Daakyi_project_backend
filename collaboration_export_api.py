"""
DAAKYI CompaaS - Collaboration Export Summary API
Export collaboration data including comments, decisions, and audit trails
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

# RBAC imports
from mvp1_auth import get_current_user, ensure_organization_access
from mvp1_models import MVP1User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collaboration/export", tags=["collaboration-export"])

# Pydantic Models for Collaboration Export
class ExportDateRange(BaseModel):
    start: datetime
    end: datetime

class CollaborationExportRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    format: str  # 'PDF', 'DOCX'
    entity_type: str  # 'assessment', 'remediation', 'evidence'
    entity_id: str
    entity_title: str
    date_range: ExportDateRange
    include_comments: bool = True
    include_replies: bool = True
    include_mentions: bool = True
    include_status_changes: bool = True
    include_decision_logs: bool = True
    include_resolution_summaries: bool = True
    include_audit_trail: bool = True
    include_timestamps: bool = True
    include_user_profiles: bool = True
    include_attachments: bool = False
    filter_by_users: List[str] = []
    recipients: List[str] = []
    delivery_note: Optional[str] = ""
    watermark: str = "CONFIDENTIAL"
    include_signature: bool = True

class CollaborationExportResponse(BaseModel):
    id: str
    title: str
    format: str
    entity_type: str
    entity_id: str
    entity_title: str
    status: str  # 'generating', 'completed', 'failed'
    created_by: str
    created_at: datetime
    file_url: Optional[str] = None
    file_size: Optional[str] = None
    recipient_count: int
    completion_time: Optional[datetime] = None

class CollaborationSummary(BaseModel):
    total_comments: int
    total_replies: int
    total_mentions: int
    total_participants: int
    status_changes: int
    decision_points: int
    resolution_items: int
    collaboration_period: ExportDateRange
    top_contributors: List[Dict[str, Any]]
    key_decisions: List[Dict[str, Any]]
    resolutions: List[Dict[str, Any]]

class CollaborationUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    comment_count: int

@router.get("/summary/{entity_type}/{entity_id}", response_model=CollaborationSummary)
async def get_collaboration_summary(
    entity_type: str,
    entity_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get collaboration summary for an entity (All authenticated users)"""
    try:
        # Set date range
        end_dt = datetime.utcnow() if not end_date else datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        start_dt = end_dt - timedelta(days=30) if not start_date else datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Mock collaboration data - in production, this would aggregate from database
        mock_summary = CollaborationSummary(
            total_comments=24,
            total_replies=18,
            total_mentions=12,
            total_participants=4,
            status_changes=6,
            decision_points=8,
            resolution_items=5,
            collaboration_period=ExportDateRange(start=start_dt, end=end_dt),
            top_contributors=[
                {
                    "user": {
                        "id": "4",
                        "name": "Lisa Davis", 
                        "email": "lisa.davis@company.com",
                        "role": "admin"
                    },
                    "contributions": 15
                },
                {
                    "user": {
                        "id": "1",
                        "name": "John Smith",
                        "email": "john.smith@company.com", 
                        "role": "admin"
                    },
                    "contributions": 12
                },
                {
                    "user": {
                        "id": "2", 
                        "name": "Sarah Johnson",
                        "email": "sarah.johnson@company.com",
                        "role": "user"
                    },
                    "contributions": 8
                },
                {
                    "user": {
                        "id": "3",
                        "name": "Mike Chen",
                        "email": "mike.chen@company.com",
                        "role": "user" 
                    },
                    "contributions": 6
                }
            ],
            key_decisions=[
                {
                    "id": "decision-1",
                    "summary": "Governance policy implementation approach approved",
                    "participants": ["John Smith", "Sarah Johnson"],
                    "timestamp": "2025-01-25T14:30:00Z",
                    "status": "approved"
                },
                {
                    "id": "decision-2",
                    "summary": "Quarterly review process structure finalized", 
                    "participants": ["Lisa Davis", "Mike Chen"],
                    "timestamp": "2025-01-24T10:15:00Z",
                    "status": "implemented"
                }
            ],
            resolutions=[
                {
                    "id": "resolution-1",
                    "summary": "Access control monitoring enhancement completed",
                    "assignee": "Mike Chen",
                    "completed_at": "2025-01-26T12:00:00Z",
                    "comments": 8
                },
                {
                    "id": "resolution-2", 
                    "summary": "Incident response documentation updated",
                    "assignee": "Lisa Davis",
                    "completed_at": "2025-01-25T16:30:00Z",
                    "comments": 6
                }
            ]
        )
        
        logger.info(f"Retrieved collaboration summary for {entity_type}:{entity_id}")
        return mock_summary
    
    except Exception as e:
        logger.error(f"Error getting collaboration summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve collaboration summary")

@router.get("/participants/{entity_type}/{entity_id}", response_model=List[CollaborationUser])
async def get_collaboration_participants(
    entity_type: str,
    entity_id: str,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of collaboration participants for an entity (All authenticated users)"""
    try:
        # Mock participant data - in production, this would query database
        mock_participants = [
            CollaborationUser(
                id="1",
                name="John Smith",
                email="john.smith@company.com", 
                role="admin",
                avatar=None,
                comment_count=12
            ),
            CollaborationUser(
                id="2",
                name="Sarah Johnson",
                email="sarah.johnson@company.com",
                role="user", 
                avatar=None,
                comment_count=8
            ),
            CollaborationUser(
                id="3", 
                name="Mike Chen",
                email="mike.chen@company.com",
                role="user",
                avatar=None,
                comment_count=6
            ),
            CollaborationUser(
                id="4",
                name="Lisa Davis",
                email="lisa.davis@company.com",
                role="admin",
                avatar=None, 
                comment_count=15
            )
        ]
        
        logger.info(f"Retrieved {len(mock_participants)} participants for {entity_type}:{entity_id}")
        return mock_participants
    
    except Exception as e:
        logger.error(f"Error getting collaboration participants: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve participants")

@router.post("/create", response_model=CollaborationExportResponse)
async def create_collaboration_export(
    export_request: CollaborationExportRequest,
    background_tasks: BackgroundTasks,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a new collaboration export (All authenticated users)"""
    try:
        export_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Create export record
        export_data = {
            "id": export_id,
            "title": export_request.title,
            "description": export_request.description,
            "format": export_request.format,
            "entity_type": export_request.entity_type,
            "entity_id": export_request.entity_id,
            "entity_title": export_request.entity_title,
            "status": "generating",
            "created_by": current_user.id,  # Use actual authenticated user
            "created_at": current_time,
            "file_url": None,
            "file_size": None,
            "recipient_count": len(export_request.recipients),
            "completion_time": None,
            "export_config": export_request.model_dump(),
            "version": 1
        }
        
        # Insert into database
        result = await db.collaboration_exports.insert_one(export_data)
        
        # Schedule background export generation
        background_tasks.add_task(
            generate_collaboration_export,
            export_id,
            export_request.model_dump()
        )
        
        logger.info(f"Created collaboration export: {export_id}")
        
        return CollaborationExportResponse(
            id=export_id,
            title=export_request.title,
            format=export_request.format,
            entity_type=export_request.entity_type,
            entity_id=export_request.entity_id,
            entity_title=export_request.entity_title,
            status="generating",
            created_by=current_user.name,
            created_at=current_time,
            file_url=None,
            file_size=None,
            recipient_count=len(export_request.recipients),
            completion_time=None
        )
    
    except Exception as e:
        logger.error(f"Error creating collaboration export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create collaboration export")

@router.get("/{export_id}/status")
async def get_export_status(
    export_id: str, 
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get the status of a collaboration export (All authenticated users)"""
    try:
        # Mock status check - in production, this would query database
        mock_status = {
            "export_id": export_id,
            "status": "completed",
            "progress": 100,
            "created_at": datetime.utcnow() - timedelta(minutes=5),
            "completion_time": datetime.utcnow() - timedelta(minutes=2),
            "file_url": f"/collaboration/exports/{export_id}/summary.pdf",
            "file_size": "1.8 MB",
            "recipient_count": 2,
            "delivery_status": "sent"
        }
        
        logger.info(f"Retrieved export status for {export_id}")
        return mock_status
    
    except Exception as e:
        logger.error(f"Error getting export status {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get export status")

@router.get("/", response_model=List[CollaborationExportResponse])
async def get_collaboration_exports(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of collaboration exports with optional filtering (All authenticated users)"""
    try:
        # Mock export history data
        current_time = datetime.utcnow()
        mock_exports = [
            {
                "id": "export-001",
                "title": "Q4 2025 NIST CSF Assessment Collaboration Summary",
                "format": "PDF",
                "entity_type": "assessment",
                "entity_id": "assess-456",
                "entity_title": "Q4 2025 NIST CSF Assessment", 
                "status": "completed",
                "created_by": "John Smith",
                "created_at": current_time - timedelta(hours=2),
                "file_url": "/collaboration/exports/export-001/summary.pdf",
                "file_size": "2.1 MB",
                "recipient_count": 3,
                "completion_time": current_time - timedelta(hours=1, minutes=45)
            },
            {
                "id": "export-002",
                "title": "Governance Policy Implementation Discussion Summary",
                "format": "DOCX", 
                "entity_type": "remediation",
                "entity_id": "REM-001",
                "entity_title": "Enhance Governance Policy Implementation",
                "status": "completed",
                "created_by": "Sarah Johnson",
                "created_at": current_time - timedelta(days=1),
                "file_url": "/collaboration/exports/export-002/summary.docx",
                "file_size": "1.7 MB",
                "recipient_count": 2,
                "completion_time": current_time - timedelta(days=1) + timedelta(minutes=3)
            },
            {
                "id": "export-003",
                "title": "Evidence Analysis Collaboration Review",
                "format": "PDF",
                "entity_type": "evidence",
                "entity_id": "ev-123",
                "entity_title": "Cybersecurity Policy Document Analysis",
                "status": "generating", 
                "created_by": "Lisa Davis",
                "created_at": current_time - timedelta(minutes=15),
                "file_url": None,
                "file_size": None,
                "recipient_count": 1,
                "completion_time": None
            }
        ]
        
        # Apply filters
        filtered_exports = mock_exports
        if entity_type:
            filtered_exports = [e for e in filtered_exports if e["entity_type"] == entity_type]
        if entity_id:
            filtered_exports = [e for e in filtered_exports if e["entity_id"] == entity_id]
        if status:
            filtered_exports = [e for e in filtered_exports if e["status"] == status]
        
        # Convert to response models
        response_exports = []
        for export_data in filtered_exports[:limit]:
            response_exports.append(CollaborationExportResponse(
                id=export_data["id"],
                title=export_data["title"],
                format=export_data["format"],
                entity_type=export_data["entity_type"],
                entity_id=export_data["entity_id"],
                entity_title=export_data["entity_title"],
                status=export_data["status"],
                created_by=export_data["created_by"],
                created_at=export_data["created_at"],
                file_url=export_data.get("file_url"),
                file_size=export_data.get("file_size"),
                recipient_count=export_data["recipient_count"],
                completion_time=export_data.get("completion_time")
            ))
        
        logger.info(f"Retrieved {len(response_exports)} collaboration exports")
        return response_exports
    
    except Exception as e:
        logger.error(f"Error getting collaboration exports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve collaboration exports")

@router.delete("/{export_id}")
async def delete_collaboration_export(
    export_id: str, 
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete a collaboration export (All authenticated users - own exports only)"""
    try:
        # In production, this would delete from database and cleanup files
        result = {"deleted": True}
        
        logger.info(f"Deleted collaboration export: {export_id}")
        
        return {
            "message": "Collaboration export deleted successfully",
            "export_id": export_id
        }
    
    except Exception as e:
        logger.error(f"Error deleting collaboration export {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete collaboration export")

@router.get("/analytics/stats")
async def get_collaboration_export_analytics(
    current_user: MVP1User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get collaboration export analytics and statistics (All authenticated users)"""
    try:
        # Mock analytics data
        stats = {
            "total_exports": 47,
            "completed_exports": 43,
            "generating_exports": 2, 
            "failed_exports": 2,
            "total_participants": 28,
            "format_distribution": [
                {"format": "PDF", "count": 32, "percentage": 68},
                {"format": "DOCX", "count": 15, "percentage": 32}
            ],
            "entity_distribution": [
                {"entity_type": "assessment", "count": 18, "percentage": 38},
                {"entity_type": "remediation", "count": 19, "percentage": 40},
                {"entity_type": "evidence", "count": 10, "percentage": 21}
            ],
            "recent_activity": [
                {"date": "2025-01-26", "exports_created": 5},
                {"date": "2025-01-25", "exports_created": 3},
                {"date": "2025-01-24", "exports_created": 4}
            ],
            "top_exporters": [
                {"user": "John Smith", "exports": 12},
                {"user": "Sarah Johnson", "exports": 9},
                {"user": "Lisa Davis", "exports": 8}
            ],
            "collaboration_insights": {
                "avg_comments_per_export": 18.5,
                "avg_participants_per_export": 3.2,
                "most_active_time": "14:00-16:00",
                "peak_collaboration_day": "Tuesday"
            }
        }
        
        logger.info("Retrieved collaboration export analytics")
        return stats
    
    except Exception as e:
        logger.error(f"Error getting collaboration export analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

# Background Tasks
async def generate_collaboration_export(
    export_id: str,
    export_config: Dict[str, Any]
):
    """Background task to generate collaboration export"""
    try:
        db = await get_database()
        
        # Simulate export generation process
        logger.info(f"Starting collaboration export generation for {export_id}")
        
        # Update status to generating
        await db.collaboration_exports.update_one(
            {"id": export_id},
            {
                "$set": {
                    "status": "generating",
                    "generation_started_at": datetime.utcnow()
                }
            }
        )
        
        # Simulate processing time based on export size
        processing_time = 2 + (len(export_config.get("recipients", [])) * 0.5)
        time.sleep(processing_time)
        
        # Generate mock file details
        file_extension = export_config["format"].lower()
        file_url = f"/collaboration/exports/{export_id}/summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_size = f"{1.2 + (processing_time * 0.3):.1f} MB"
        
        # Update with completion status
        completion_time = datetime.utcnow()
        await db.collaboration_exports.update_one(
            {"id": export_id},
            {
                "$set": {
                    "status": "completed",
                    "completion_time": completion_time,
                    "file_url": file_url,
                    "file_size": file_size,
                    "delivery_status": "sent" if export_config.get("recipients") else "ready"
                }
            }
        )
        
        # If email delivery is requested, send notifications
        if export_config.get("recipients"):
            logger.info(f"Would send collaboration export {export_id} to {len(export_config['recipients'])} recipients")
        
        logger.info(f"Successfully generated collaboration export {export_id}")
        
    except Exception as e:
        logger.error(f"Error in collaboration export generation for {export_id}: {str(e)}")
        try:
            await db.collaboration_exports.update_one(
                {"id": export_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completion_time": datetime.utcnow()
                    }
                }
            )
        except:
            pass