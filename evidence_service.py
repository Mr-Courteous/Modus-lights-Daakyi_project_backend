"""
DAAKYI CompaaS Evidence Management Service
Handles file upload, storage, and AI-powered analysis workflow
"""

import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import mimetypes
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from models import EvidenceFile, AIAnalysisResult
from database import DatabaseOperations
from ai_service import ai_service

logger = logging.getLogger(__name__)

class EvidenceService:
    """Service for managing evidence files and AI analysis"""
    
    def __init__(self):
        self.upload_directory = Path("uploads")
        self.upload_directory.mkdir(exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'application/pdf': 'PDF',
            'application/msword': 'DOC',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
            'application/vnd.ms-excel': 'XLS',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
            'text/plain': 'TXT',
            'text/csv': 'CSV',
            'image/png': 'PNG',
            'image/jpeg': 'JPG',
            'image/gif': 'GIF'
        }
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

    async def upload_evidence(
        self,
        file: UploadFile,
        assessment_id: str,
        user_id: str,
        auto_analyze: bool = True
    ) -> EvidenceFile:
        """
        Upload and optionally analyze an evidence file
        
        Args:
            file: FastAPI UploadFile object
            assessment_id: ID of the assessment this evidence belongs to
            user_id: ID of the user uploading the file
            auto_analyze: Whether to automatically run AI analysis
            
        Returns:
            EvidenceFile object with upload details
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Read file content
            file_content = await file.read()
            file.file.seek(0)  # Reset file pointer
            
            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = self.upload_directory / unique_filename
            
            # Save file to disk
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Determine file type
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            file_type = self.supported_types.get(mime_type, 'OTHER')
            
            # Create evidence file record
            evidence_file = EvidenceFile(
                filename=unique_filename,
                original_name=file.filename,
                file_path=str(file_path),
                size=len(file_content),
                mime_type=mime_type,
                file_type=file_type,
                assessment_id=assessment_id,
                uploaded_by=user_id,
                processing_status="uploaded" if not auto_analyze else "pending"
            )
            
            # Store in database
            await DatabaseOperations.insert_one("evidence_files", evidence_file.dict())
            
            # Start AI analysis if requested
            if auto_analyze:
                # Run AI analysis in background
                asyncio.create_task(self._analyze_file_background(evidence_file.id, file_content, file.filename, mime_type))
                evidence_file.processing_status = "processing"
            
            logger.info(f"Evidence file uploaded: {file.filename} -> {unique_filename}")
            return evidence_file
            
        except Exception as e:
            logger.error(f"Evidence upload failed: {str(e)}")
            raise

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            raise ValueError(f"File too large. Maximum size is {self.max_file_size / (1024*1024):.1f}MB")
        
        # Check file type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        if mime_type not in self.supported_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

    async def _analyze_file_background(
        self, 
        evidence_id: str, 
        file_content: bytes, 
        filename: str, 
        mime_type: str
    ) -> None:
        """Background task for AI analysis"""
        try:
            logger.info(f"Starting background AI analysis for {filename}")
            
            # Update status to processing
            await DatabaseOperations.update_one(
                "evidence_files",
                {"id": evidence_id},
                {"processing_status": "processing"}
            )
            
            # Perform AI analysis
            analysis_result = await ai_service.analyze_document(file_content, filename, mime_type)
            
            # Update database with analysis results
            await DatabaseOperations.update_one(
                "evidence_files",
                {"id": evidence_id},
                {
                    "ai_analysis": analysis_result.dict(),
                    "mapped_controls": [mapping["control_id"] for mapping in analysis_result.nist_mappings],
                    "processing_status": "completed"
                }
            )
            
            # Update any related control assessments
            await self._update_control_assessments(evidence_id, analysis_result)
            
            logger.info(f"AI analysis completed for {filename}")
            
        except Exception as e:
            logger.error(f"Background AI analysis failed for {filename}: {str(e)}")
            
            # Update status to failed
            await DatabaseOperations.update_one(
                "evidence_files",
                {"id": evidence_id},
                {
                    "processing_status": "failed",
                    "ai_analysis": {
                        "error": str(e),
                        "classification": "ERROR",
                        "confidence": 0.0
                    }
                }
            )

    async def _update_control_assessments(self, evidence_id: str, analysis_result: AIAnalysisResult) -> None:
        """Update control assessments based on AI analysis"""
        try:
            # Get evidence file to find assessment_id
            evidence = await DatabaseOperations.find_one("evidence_files", {"id": evidence_id})
            if not evidence:
                return
            
            assessment_id = evidence["assessment_id"]
            
            # Update controls mentioned in NIST mappings
            for mapping in analysis_result.nist_mappings:
                control_id = mapping["control_id"]
                confidence = mapping.get("confidence", 0.8)
                
                # Find or create control assessment
                existing_control = await DatabaseOperations.find_one(
                    "control_assessments",
                    {"assessment_id": assessment_id, "control_id": control_id}
                )
                
                if existing_control:
                    # Update existing control
                    new_evidence_count = existing_control.get("evidence_count", 0) + 1
                    ai_confidence = max(existing_control.get("ai_confidence", 0), confidence)
                    
                    await DatabaseOperations.update_one(
                        "control_assessments",
                        {"assessment_id": assessment_id, "control_id": control_id},
                        {
                            "evidence_count": new_evidence_count,
                            "ai_confidence": ai_confidence,
                            "last_updated": datetime.utcnow(),
                            "status": "In Progress" if existing_control.get("status") == "Not Started" else existing_control.get("status", "In Progress")
                        }
                    )
                else:
                    # Create new control assessment
                    from models import ControlAssessment
                    control_assessment = ControlAssessment(
                        assessment_id=assessment_id,
                        control_id=control_id,
                        status="In Progress",
                        evidence_count=1,
                        ai_confidence=confidence
                    )
                    
                    await DatabaseOperations.insert_one("control_assessments", control_assessment.dict())
            
            logger.info(f"Updated control assessments for {len(analysis_result.nist_mappings)} controls")
            
        except Exception as e:
            logger.error(f"Failed to update control assessments: {str(e)}")

    async def get_evidence_files(
        self,
        assessment_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get evidence files with optional filtering"""
        try:
            filter_dict = {}
            
            if assessment_id:
                filter_dict["assessment_id"] = assessment_id
            if user_id:
                filter_dict["uploaded_by"] = user_id
            if status:
                filter_dict["processing_status"] = status
            
            evidence_files = await DatabaseOperations.find_many(
                "evidence_files",
                filter_dict,
                sort=[("uploaded_at", -1)]
            )
            
            return evidence_files
            
        except Exception as e:
            logger.error(f"Failed to get evidence files: {str(e)}")
            return []

    async def get_evidence_by_id(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get specific evidence file by ID"""
        try:
            evidence = await DatabaseOperations.find_one("evidence_files", {"id": evidence_id})
            return evidence
        except Exception as e:
            logger.error(f"Failed to get evidence by ID: {str(e)}")
            return None

    async def delete_evidence(self, evidence_id: str, user_id: str) -> bool:
        """Delete evidence file and associated data"""
        try:
            # Get evidence file
            evidence = await DatabaseOperations.find_one("evidence_files", {"id": evidence_id})
            if not evidence:
                return False
            
            # Check if user has permission to delete
            if evidence["uploaded_by"] != user_id:
                # TODO: Add role-based permission checking
                pass
            
            # Delete file from disk
            if evidence.get("file_path"):
                try:
                    os.remove(evidence["file_path"])
                except OSError:
                    logger.warning(f"Could not delete file from disk: {evidence['file_path']}")
            
            # Delete from database
            deleted_count = await DatabaseOperations.delete_one("evidence_files", {"id": evidence_id})
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete evidence: {str(e)}")
            return False

    async def reanalyze_evidence(self, evidence_id: str) -> bool:
        """Rerun AI analysis on an existing evidence file"""
        try:
            evidence = await DatabaseOperations.find_one("evidence_files", {"id": evidence_id})
            if not evidence:
                return False
            
            # Read file content
            file_path = evidence["file_path"]
            if not os.path.exists(file_path):
                logger.error(f"File not found for reanalysis: {file_path}")
                return False
            
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Start background reanalysis
            asyncio.create_task(
                self._analyze_file_background(
                    evidence_id, 
                    file_content, 
                    evidence["original_name"], 
                    evidence["mime_type"]
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reanalyze evidence: {str(e)}")
            return False

# Singleton instance
evidence_service = EvidenceService()