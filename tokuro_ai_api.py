"""
TOKURO AI API - REST Endpoints for DAAKYI's Proprietary AI Engine
================================================================

This module provides REST API endpoints for Tokuro AI functionality:
- Document analysis and framework mapping
- Analysis result retrieval
- Audit log access
- Confidence scoring and recommendations

Author: DAAKYI Development Team
Version: 1.0.0
"""

import os
import tempfile
import aiofiles
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

from mvp1_auth import get_current_user
from mvp1_models import MVP1User
from tokuro_ai_engine import (
    tokuro_ai_service,
    TokuroAnalysisResult,
    TokuroAuditLog,
    ConfidenceLevel,
    TokuroAnalysisStatus
)
import logging

tokuro_api_logger = logging.getLogger("TokuroAI_API")

# Initialize router
router = APIRouter(prefix="/api/mvp1/tokuro", tags=["Tokuro AI"])

# Request/Response Models
class DocumentAnalysisRequest(BaseModel):
    document_name: str
    frameworks: List[str]
    assessment_id: str

class DocumentAnalysisResponse(BaseModel):
    analysis_id: str
    status: TokuroAnalysisStatus
    message: str

class AnalysisResultResponse(BaseModel):
    analysis_id: str
    document_name: str
    document_type: str
    frameworks_analyzed: List[str]
    mappings: List[Dict[str, Any]]
    overall_confidence: float
    confidence_level: ConfidenceLevel
    confidence_label: str
    status: TokuroAnalysisStatus
    processing_time: float
    reasoning_summary: str
    recommendations: List[str]
    created_at: datetime

class FrameworksListResponse(BaseModel):
    frameworks: Dict[str, Dict[str, Any]]

class AuditLogsResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total_count: int

@router.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    frameworks: str = Form(...),  # JSON string of framework list
    assessment_id: str = Form(...),
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Upload and analyze document with Tokuro AI
    
    This endpoint accepts a document upload and triggers Tokuro AI analysis
    to map the document content to specified compliance frameworks.
    """
    try:
        import json
        
        # Parse frameworks from JSON string
        try:
            frameworks_list = json.loads(frameworks)
        except json.JSONDecodeError:
            frameworks_list = [frameworks]  # Fallback for single framework
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx', '.xlsx']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Supported: PDF, DOCX, XLSX"
            )
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        
        try:
            # Save uploaded file
            content = await file.read()
            async with aiofiles.open(temp_file.name, 'wb') as f:
                await f.write(content)
            
            tokuro_api_logger.info(f"Processing document: {file.filename} for user: {current_user.email}")
            
            # Trigger Tokuro AI analysis (this runs in the background)
            analysis_result = await tokuro_ai_service.analyze_document(
                file_path=temp_file.name,
                document_name=file.filename,
                frameworks=frameworks_list,
                user_id=current_user.id,
                assessment_id=assessment_id
            )
            
            return DocumentAnalysisResponse(
                analysis_id=analysis_result.analysis_id,
                status=analysis_result.status,
                message="Tokuro AI analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                tokuro_api_logger.warning(f"Failed to cleanup temp file: {e}")
                
    except HTTPException:
        raise
    except Exception as e:
        tokuro_api_logger.error(f"Document analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Tokuro AI analysis failed: {str(e)}"
        )

@router.get("/analysis/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Retrieve Tokuro AI analysis result by ID
    
    Returns the complete analysis result including mappings, 
    confidence scores, and recommendations.
    """
    try:
        result = await tokuro_ai_service.get_analysis_result(analysis_id)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Analysis result not found: {analysis_id}"
            )
        
        # Convert mappings to dict format for response
        mappings_dict = [mapping.dict() for mapping in result.mappings]
        
        # Get confidence label
        confidence_label = tokuro_ai_service.get_confidence_label(result.confidence_level)
        
        return AnalysisResultResponse(
            analysis_id=result.analysis_id,
            document_name=result.document_name,
            document_type=result.document_type,
            frameworks_analyzed=result.frameworks_analyzed,
            mappings=mappings_dict,
            overall_confidence=result.overall_confidence,
            confidence_level=result.confidence_level,
            confidence_label=confidence_label,
            status=result.status,
            processing_time=result.processing_time,
            reasoning_summary=result.reasoning_summary,
            recommendations=result.recommendations,
            created_at=result.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        tokuro_api_logger.error(f"Failed to retrieve analysis result: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve analysis result"
        )

@router.get("/frameworks", response_model=FrameworksListResponse)
async def get_supported_frameworks(
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Get list of supported frameworks for Tokuro AI analysis
    
    Returns all available compliance frameworks that Tokuro AI
    can analyze and map documents against.
    """
    try:
        frameworks = tokuro_ai_service.frameworks
        
        return FrameworksListResponse(frameworks=frameworks)
        
    except Exception as e:
        tokuro_api_logger.error(f"Failed to retrieve frameworks: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve supported frameworks"
        )

@router.get("/audit-logs", response_model=AuditLogsResponse)
async def get_tokuro_audit_logs(
    assessment_id: Optional[str] = None,
    limit: int = 50,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Retrieve Tokuro AI audit logs
    
    Returns audit trail of all Tokuro AI activities including
    analysis results, user actions, and system events.
    """
    try:
        # Only admins and auditors can view all logs
        if current_user.role not in ["admin", "auditor"]:
            # Regular users can only see their own logs
            logs = await tokuro_ai_service.get_audit_logs(
                user_id=current_user.id,
                assessment_id=assessment_id,
                limit=limit
            )
        else:
            logs = await tokuro_ai_service.get_audit_logs(
                assessment_id=assessment_id,
                limit=limit
            )
        
        logs_dict = [log.dict() for log in logs]
        
        return AuditLogsResponse(
            logs=logs_dict,
            total_count=len(logs_dict)
        )
        
    except Exception as e:
        tokuro_api_logger.error(f"Failed to retrieve audit logs: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve Tokuro AI audit logs"
        )

@router.post("/validate-analysis/{analysis_id}")
async def validate_analysis(
    analysis_id: str,
    action: str,  # "approve", "reject", "request_review"
    notes: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Human validation of Tokuro AI analysis results
    
    Allows users to approve, reject, or request additional review
    for Tokuro AI analysis results.
    """
    try:
        # Validate action
        valid_actions = ["approve", "reject", "request_review"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        # Get analysis result
        result = await tokuro_ai_service.get_analysis_result(analysis_id)
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Analysis result not found: {analysis_id}"
            )
        
        # Log validation activity
        from tokuro_ai_engine import TokuroAuditLog
        validation_log = TokuroAuditLog(
            analysis_id=analysis_id,
            user_id=current_user.id,
            assessment_id="",  # Will be updated if available
            action=f"validate_{action}",
            document_name=result.document_name,
            framework_used=", ".join(result.frameworks_analyzed),
            confidence_score=result.overall_confidence,
            tokuro_recommendation=result.reasoning_summary,
            user_decision=action,
            metadata={
                "validation_notes": notes,
                "original_confidence": result.overall_confidence,
                "validator_role": current_user.role
            }
        )
        
        from database import DatabaseOperations
        await DatabaseOperations.insert_one("tokuro_audit_logs", validation_log.dict())
        
        tokuro_api_logger.info(f"Analysis {analysis_id} validated with action: {action} by user: {current_user.email}")
        
        return {
            "message": f"Analysis {action}ed successfully",
            "analysis_id": analysis_id,
            "action": action,
            "validator": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        tokuro_api_logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to validate analysis"
        )

@router.get("/statistics")
async def get_tokuro_statistics(
    assessment_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """
    Get Tokuro AI usage statistics and performance metrics
    """
    try:
        from database import DatabaseOperations
        
        # Build query filter
        query = {}
        if assessment_id:
            query["assessment_id"] = assessment_id
        
        # Get analysis results
        analyses = await DatabaseOperations.find_many("tokuro_analysis_results", query)
        
        # Calculate statistics
        total_analyses = len(analyses)
        successful_analyses = len([a for a in analyses if a.get("status") == "completed"])
        failed_analyses = len([a for a in analyses if a.get("status") == "failed"])
        
        # Calculate confidence distribution
        confidence_scores = [a.get("overall_confidence", 0) for a in analyses if a.get("overall_confidence")]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        high_confidence = len([c for c in confidence_scores if c >= 90])
        medium_confidence = len([c for c in confidence_scores if 70 <= c < 90])
        low_confidence = len([c for c in confidence_scores if c < 70])
        
        # Calculate processing times
        processing_times = [a.get("processing_time", 0) for a in analyses if a.get("processing_time")]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0,
            "confidence_distribution": {
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence, 
                "low_confidence": low_confidence
            },
            "average_confidence": round(avg_confidence, 2),
            "average_processing_time": round(avg_processing_time, 2),
            "frameworks_used": list(set([
                framework 
                for analysis in analyses 
                for framework in analysis.get("frameworks_analyzed", [])
            ]))
        }
        
    except Exception as e:
        tokuro_api_logger.error(f"Failed to retrieve statistics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve Tokuro AI statistics"
        )

@router.get("/health")
async def tokuro_health_check():
    """
    Health check endpoint for Tokuro AI service
    """
    try:
        # Check if API key is configured
        api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
        
        # Check if Tokuro AI is enabled
        enabled = os.getenv("TOKURO_AI_ENABLED", "true").lower() == "true"
        
        # Check model configuration
        model = os.getenv("TOKURO_AI_MODEL", "gpt-4")
        
        status = "healthy" if (api_key_configured and enabled) else "degraded"
        
        return {
            "status": status,
            "api_key_configured": api_key_configured,
            "enabled": enabled,
            "model": model,
            "service": "Tokuro AI - DAAKYI's Proprietary AI Engine",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        tokuro_api_logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "Tokuro AI",
            "timestamp": datetime.utcnow().isoformat()
        }