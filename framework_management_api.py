"""
DAAKYI CompaaS - Phase 1: Assessment Framework Setup & Library API
Framework Management API endpoints for uploading, managing, and organizing compliance frameworks

This module provides comprehensive framework management capabilities including:
- Framework upload and validation
- Control library management
- Control mapping engine
- Assessment template configuration
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query, Form
from typing import List, Optional, Dict, Any
import pandas as pd
import json
import yaml
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field

from models import (
    ComplianceFramework, 
    FrameworkControl, 
    ControlMapping, 
    AssessmentTemplate,
    FrameworkUpload,
    FrameworkUploadRequest,
    FrameworkListResponse,
    ControlListResponse,
    MappingRequest,
    AssessmentTemplateRequest,
    FrameworkStatistics,
    SystemOverview,
    User
)
from auth import get_current_user

# Initialize router
router = APIRouter(prefix="/api/framework-management", tags=["Framework Management"])

# Upload directory configuration
UPLOAD_DIR = Path("uploads/frameworks")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Supported file formats and their processors
SUPPORTED_FORMATS = {
    'xlsx': 'process_excel_file',
    'csv': 'process_csv_file', 
    'json': 'process_json_file',
    'yaml': 'process_yaml_file',
    'yml': 'process_yaml_file'
}

# =====================================
# PHASE 1A: FRAMEWORK LOADER ENDPOINTS
# =====================================

@router.post("/upload", summary="Upload Framework File")
async def upload_framework(
    file: UploadFile = File(...),
    framework_name: str = Form(...),
    framework_version: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form("General"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and validate a compliance framework file
    
    Supported formats: .xlsx, .csv, .json, .yaml
    
    Required fields per control:
    - Control ID (e.g., A.5.1.1)
    - Control Name/Title
    - Control Description
    - Category/Domain
    - Reference Standard
    - Tags (optional)
    """
    
    try:
        # Validate file format
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Unsupported file format",
                    "message": f"File format '.{file_extension}' is not supported",
                    "supported_formats": list(SUPPORTED_FORMATS.keys()),
                    "file_name": file.filename
                }
            )
        
        # Generate upload session
        upload_session = FrameworkUpload(
            filename=file.filename,
            file_format=file_extension,
            file_size=0,  # Will be updated after saving
            framework_name=framework_name,
            framework_version=framework_version,
            uploaded_by=current_user.id,  # Use actual user ID
            organization_id=current_user.organization_id  # Use actual organization ID
        )
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{upload_session.id}_{file.filename}"
        file_content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        upload_session.file_path = str(file_path)
        upload_session.file_size = len(file_content)
        
        # Process and validate file based on format
        processor_name = SUPPORTED_FORMATS[file_extension]
        processor = globals()[processor_name]
        
        validation_result = await processor(file_path, upload_session)
        
        # Update upload session with validation results
        upload_session.validation_status = validation_result["status"]
        upload_session.validation_errors = validation_result.get("errors", [])
        upload_session.validation_warnings = validation_result.get("warnings", [])
        upload_session.total_controls_detected = validation_result.get("total_controls", 0)
        upload_session.preview_data = validation_result.get("preview", {})
        
        # Store upload session (in real implementation, this would go to database)
        # For now, return the validation results
        
        return {
            "upload_id": upload_session.id,
            "status": upload_session.validation_status,
            "framework_name": framework_name,
            "framework_version": framework_version,
            "file_format": file_extension,
            "file_size": upload_session.file_size,
            "total_controls_detected": upload_session.total_controls_detected,
            "validation_errors": upload_session.validation_errors,
            "validation_warnings": upload_session.validation_warnings,
            "preview_data": upload_session.preview_data,
            "can_proceed": len(upload_session.validation_errors) == 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.post("/upload/{upload_id}/confirm", summary="Confirm Framework Import")
async def confirm_framework_import(
    upload_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Confirm and complete the framework import after validation
    """
    
    try:
        # In real implementation, retrieve upload session from database
        # For now, simulate the import process
        
        # Create framework record
        framework = ComplianceFramework(
            name=f"Imported Framework {upload_id[:8]}",
            display_name="Sample Framework",
            version="1.0",
            reference_standard="Sample Standard",
            category="Information Security",
            uploaded_by=current_user.id,
            organization_id=current_user.organization_id,
            total_controls=25,  # Mock data
            original_filename="sample.xlsx",
            file_format="xlsx"
        )
        
        # Generate sample controls
        sample_controls = generate_sample_controls(framework.id, 25)
        
        return {
            "framework_id": framework.id,
            "status": "imported",
            "framework_name": framework.name,
            "total_controls_imported": len(sample_controls),
            "import_completed_at": datetime.utcnow().isoformat(),
            "message": "Framework successfully imported"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import confirmation failed: {str(e)}")

@router.get("/upload/{upload_id}/preview", summary="Get Upload Preview")
async def get_upload_preview(
    upload_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get preview of uploaded framework data before confirmation
    """
    
    # Mock preview data
    preview_data = {
        "upload_id": upload_id,
        "total_rows": 25,
        "columns_detected": [
            "Control ID",
            "Control Name", 
            "Description",
            "Category",
            "Reference Standard",
            "Tags"
        ],
        "sample_rows": [
            {
                "Control ID": "A.5.1.1",
                "Control Name": "Policies for information security",
                "Description": "A set of policies for information security shall be defined...",
                "Category": "Organizational security",
                "Reference Standard": "ISO 27001:2022",
                "Tags": "Policy, Governance"
            },
            {
                "Control ID": "A.5.1.2", 
                "Control Name": "Information security roles and responsibilities",
                "Description": "Information security roles and responsibilities shall be defined...",
                "Category": "Organizational security",
                "Reference Standard": "ISO 27001:2022",
                "Tags": "Roles, Governance"
            }
        ],
        "validation_summary": {
            "total_errors": 0,
            "total_warnings": 2,
            "duplicate_ids": [],
            "missing_required_fields": []
        }
    }
    
    return preview_data

# =====================================
# FILE PROCESSING FUNCTIONS
# =====================================

async def process_excel_file(file_path: Path, upload_session: FrameworkUpload) -> Dict[str, Any]:
    """Process Excel (.xlsx) framework files"""
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Validate required columns
        required_columns = ['Control ID', 'Control Name', 'Description', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "failed",
                "errors": [f"Missing required columns: {', '.join(missing_columns)}"],
                "warnings": [],
                "total_controls": 0
            }
        
        # Check for duplicates
        duplicate_ids = df[df['Control ID'].duplicated()]['Control ID'].tolist()
        
        # Check for empty required fields
        empty_fields = []
        for col in required_columns:
            empty_count = df[col].isna().sum()
            if empty_count > 0:
                empty_fields.append(f"{col}: {empty_count} empty values")
        
        # Generate preview data
        preview_data = {
            "columns": df.columns.tolist(),
            "sample_rows": df.head(3).to_dict('records'),
            "total_rows": len(df)
        }
        
        # Prepare validation result
        errors = []
        warnings = []
        
        if duplicate_ids:
            errors.append(f"Duplicate Control IDs found: {', '.join(duplicate_ids)}")
        
        if empty_fields:
            warnings.extend(empty_fields)
        
        return {
            "status": "passed" if not errors else "failed",
            "errors": errors,
            "warnings": warnings,
            "total_controls": len(df),
            "preview": preview_data
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "errors": [f"Excel processing error: {str(e)}"],
            "warnings": [],
            "total_controls": 0
        }

async def process_csv_file(file_path: Path, upload_session: FrameworkUpload) -> Dict[str, Any]:
    """Process CSV framework files"""
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Similar validation logic as Excel
        required_columns = ['Control ID', 'Control Name', 'Description', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "failed",
                "errors": [f"Missing required columns: {', '.join(missing_columns)}"],
                "warnings": [],
                "total_controls": 0
            }
        
        # Check for duplicates and validation
        duplicate_ids = df[df['Control ID'].duplicated()]['Control ID'].tolist()
        
        preview_data = {
            "columns": df.columns.tolist(),
            "sample_rows": df.head(3).to_dict('records'),
            "total_rows": len(df)
        }
        
        errors = []
        warnings = []
        
        if duplicate_ids:
            errors.append(f"Duplicate Control IDs found: {', '.join(duplicate_ids)}")
        
        return {
            "status": "passed" if not errors else "failed",
            "errors": errors,
            "warnings": warnings,
            "total_controls": len(df),
            "preview": preview_data
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "errors": [f"CSV processing error: {str(e)}"],
            "warnings": [],
            "total_controls": 0
        }

async def process_json_file(file_path: Path, upload_session: FrameworkUpload) -> Dict[str, Any]:
    """Process JSON framework files"""
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Expect JSON structure: {"controls": [...]}
        if 'controls' not in data:
            return {
                "status": "failed",
                "errors": ["JSON file must contain 'controls' array"],
                "warnings": [],
                "total_controls": 0
            }
        
        controls = data['controls']
        if not isinstance(controls, list):
            return {
                "status": "failed",
                "errors": ["'controls' must be an array"],
                "warnings": [],
                "total_controls": 0
            }
        
        # Validate control structure
        required_fields = ['control_id', 'name', 'description', 'category']
        errors = []
        
        for i, control in enumerate(controls[:5]):  # Check first 5 controls
            missing = [field for field in required_fields if field not in control]
            if missing:
                errors.append(f"Control {i+1} missing fields: {', '.join(missing)}")
        
        preview_data = {
            "total_controls": len(controls),
            "sample_controls": controls[:3],
            "structure": "JSON with controls array"
        }
        
        return {
            "status": "passed" if not errors else "failed",
            "errors": errors,
            "warnings": [],
            "total_controls": len(controls),
            "preview": preview_data
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "errors": [f"JSON processing error: {str(e)}"],
            "warnings": [],
            "total_controls": 0
        }

async def process_yaml_file(file_path: Path, upload_session: FrameworkUpload) -> Dict[str, Any]:
    """Process YAML framework files"""
    
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Similar structure validation as JSON
        if 'controls' not in data:
            return {
                "status": "failed",
                "errors": ["YAML file must contain 'controls' section"],
                "warnings": [],
                "total_controls": 0
            }
        
        controls = data['controls'] 
        required_fields = ['control_id', 'name', 'description', 'category']
        errors = []
        
        for i, control in enumerate(controls[:5]):
            missing = [field for field in required_fields if field not in control]
            if missing:
                errors.append(f"Control {i+1} missing fields: {', '.join(missing)}")
        
        preview_data = {
            "total_controls": len(controls),
            "sample_controls": controls[:3],
            "structure": "YAML with controls section"
        }
        
        return {
            "status": "passed" if not errors else "failed",
            "errors": errors,
            "warnings": [],
            "total_controls": len(controls),
            "preview": preview_data
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "errors": [f"YAML processing error: {str(e)}"],
            "warnings": [],
            "total_controls": 0
        }

# =====================================
# HELPER FUNCTIONS
# =====================================

def generate_sample_controls(framework_id: str, count: int) -> List[FrameworkControl]:
    """Generate sample controls for testing purposes"""
    
    sample_controls = []
    categories = ["Access Control", "Asset Management", "Cryptography", "Physical Security", "Operations Security"]
    
    for i in range(count):
        control = FrameworkControl(
            framework_id=framework_id,
            control_id=f"A.{i//5 + 5}.{i%5 + 1}.{i%3 + 1}",
            control_name=f"Sample Control {i+1}",
            control_description=f"This is a sample control description for control {i+1}",
            category=categories[i % len(categories)],
            reference_standard="Sample Standard",
            framework_version="1.0",
            tags=["sample", "testing"],
            priority_level="medium"
        )
        sample_controls.append(control)
    
    return sample_controls

# =====================================
# FRAMEWORK LISTING ENDPOINTS (Preview for Phase 1B)
# =====================================

@router.get("/frameworks", summary="List All Frameworks")
async def list_frameworks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    List all imported frameworks with filtering and pagination
    """
    
    # Mock data for demonstration
    mock_frameworks = [
        ComplianceFramework(
            id=str(uuid.uuid4()),
            name="ISO/IEC 27001:2022",
            display_name="ISO 27001:2022",
            version="2022",
            reference_standard="ISO 27001:2022",
            category="Information Security",
            uploaded_by="admin_user",
            organization_id="org_001",
            total_controls=93,
            original_filename="iso27001_2022.xlsx",
            file_format="xlsx"
        ),
        ComplianceFramework(
            id=str(uuid.uuid4()),
            name="NIST Cybersecurity Framework v2.0",
            display_name="NIST CSF v2.0",
            version="2.0",
            reference_standard="NIST CSF 2.0",
            category="Cybersecurity",
            uploaded_by="admin_user",
            organization_id="org_001",
            total_controls=106,
            original_filename="nist_csf_v2.xlsx",
            file_format="xlsx"
        ),
        ComplianceFramework(
            id=str(uuid.uuid4()),
            name="SOC 2 Trust Services Criteria",
            display_name="SOC 2",
            version="2017",
            reference_standard="SOC 2",
            category="Trust Services",
            uploaded_by="admin_user",
            organization_id="org_001",
            total_controls=64,
            original_filename="soc2_criteria.csv",
            file_format="csv"
        )
    ]
    
    # Apply filtering
    filtered_frameworks = mock_frameworks
    if category:
        filtered_frameworks = [f for f in filtered_frameworks if f.category.lower() == category.lower()]
    
    if search:
        filtered_frameworks = [f for f in filtered_frameworks if search.lower() in f.name.lower()]
    
    # Apply pagination
    total_count = len(filtered_frameworks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_frameworks = filtered_frameworks[start_idx:end_idx]
    
    return FrameworkListResponse(
        frameworks=page_frameworks,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=(total_count + page_size - 1) // page_size
    )

@router.get("/frameworks/{framework_id}", summary="Get Framework Details")
async def get_framework_details(
    framework_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific framework
    """
    
    # Mock framework details
    framework_details = {
        "framework": {
            "id": framework_id,
            "name": "ISO/IEC 27001:2022",
            "display_name": "ISO 27001:2022",
            "version": "2022",
            "category": "Information Security",
            "total_controls": 93,
            "upload_date": "2024-01-15T10:30:00Z",
            "uploaded_by": "admin_user",
            "status": "active"
        },
        "statistics": {
            "total_controls": 93,
            "mapped_controls": 67,
            "unmapped_controls": 26,
            "mapping_coverage": 72.0,
            "category_breakdown": {
                "Organizational security": 15,
                "Human resource security": 8,
                "Asset management": 12,
                "Access control": 18,
                "Cryptography": 6,
                "Physical security": 10,
                "Operations security": 14,
                "Communications security": 6,
                "System development": 4
            }
        },
        "recent_activity": [
            {
                "action": "controls_mapped",
                "count": 5,
                "date": "2024-01-20T15:45:00Z",
                "user": "compliance_admin"
            },
            {
                "action": "assessment_created",
                "count": 1,
                "date": "2024-01-18T09:30:00Z",
                "user": "audit_manager"
            }
        ]
    }
    
    return framework_details

# Add health check for the framework management module
@router.get("/health", summary="Framework Management Health Check")
async def framework_management_health():
    """
    Health check endpoint for framework management module
    """
    
    return {
        "status": "healthy",
        "module": "Framework Management",
        "version": "1.0.0",
        "phase": "1B - Control Library Viewer",
        "capabilities": [
            "Framework Upload (.xlsx, .csv, .json, .yaml)",
            "File Validation",
            "Preview Generation",
            "Framework Import",
            "Framework Listing",
            "Control Library Viewing",
            "Advanced Control Filtering",
            "Multi-field Control Search",
            "Control Export Capabilities"
        ],
        "upload_directory": str(UPLOAD_DIR),
        "supported_formats": list(SUPPORTED_FORMATS.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================
# PHASE 1B: CONTROL LIBRARY VIEWER ENDPOINTS
# =====================================

@router.get("/frameworks/{framework_id}/controls", summary="List Framework Controls")
async def get_framework_controls(
    framework_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Search across control ID, name, description"),
    category: Optional[str] = Query(None, description="Filter by control category"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    status: Optional[str] = Query(None, description="Filter by control status"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    sort_by: str = Query("control_id", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user)
):
    """
    Get all controls for a specific framework with advanced filtering, searching, and sorting
    
    Features:
    - Multi-field search across control_id, name, description
    - Category, priority, status, and tag filtering
    - Configurable sorting by any field
    - Pagination for large control sets
    - Export-ready data structure
    """
    
    try:
        # Generate comprehensive mock control data for different frameworks
        mock_controls = generate_framework_controls(framework_id)
        
        # Apply search filter
        filtered_controls = mock_controls
        if search:
            search_lower = search.lower()
            filtered_controls = [
                control for control in filtered_controls
                if search_lower in control.control_id.lower() or
                   search_lower in control.control_name.lower() or
                   search_lower in control.control_description.lower() or
                   any(search_lower in tag.lower() for tag in control.tags)
            ]
        
        # Apply category filter
        if category:
            filtered_controls = [
                control for control in filtered_controls
                if control.category.lower() == category.lower()
            ]
        
        # Apply priority filter
        if priority:
            filtered_controls = [
                control for control in filtered_controls
                if control.priority_level.lower() == priority.lower()
            ]
        
        # Apply status filter (assuming we add status to control model)
        if status:
            # For mock data, we'll simulate status
            filtered_controls = [
                control for control in filtered_controls
                if getattr(control, 'status', 'active').lower() == status.lower()
            ]
        
        # Apply tags filter
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(',')]
            filtered_controls = [
                control for control in filtered_controls
                if any(tag in [t.lower() for t in control.tags] for tag in tag_list)
            ]
        
        # Apply sorting
        reverse_sort = sort_order == "desc"
        
        # Define sortable fields with their attribute names
        sort_fields = {
            "control_id": "control_id",
            "name": "control_name",
            "category": "category",
            "priority": "priority_level",
            "created_at": "created_at"
        }
        
        if sort_by in sort_fields:
            sort_attr = sort_fields[sort_by]
            filtered_controls.sort(
                key=lambda x: getattr(x, sort_attr, "").lower() if isinstance(getattr(x, sort_attr, ""), str) else getattr(x, sort_attr, ""),
                reverse=reverse_sort
            )
        
        # Apply pagination
        total_count = len(filtered_controls)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_controls = filtered_controls[start_idx:end_idx]
        
        # Get unique values for filter options
        filter_options = {
            "categories": list(set(control.category for control in mock_controls)),
            "priorities": list(set(control.priority_level for control in mock_controls)),
            "statuses": ["active", "draft", "pending", "archived"],
            "all_tags": list(set(tag for control in mock_controls for tag in control.tags))
        }
        
        return ControlListResponse(
            controls=page_controls,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size,
            filters_applied={
                "search": search,
                "category": category,
                "priority": priority,
                "status": status,
                "tags": tags,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve controls: {str(e)}")

@router.get("/frameworks/{framework_id}/controls/export", summary="Export Framework Controls")
async def export_framework_controls(
    framework_id: str,
    format: str = Query("csv", regex="^(csv|xlsx|json)$", description="Export format"),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to export"),
    current_user: User = Depends(get_current_user)
):
    """
    Export framework controls in various formats (CSV, Excel, JSON)
    
    Supports same filtering options as the main control listing endpoint
    """
    
    try:
        # Get filtered controls using the same logic as the main endpoint
        mock_controls = generate_framework_controls(framework_id)
        
        # Apply the same filtering logic (simplified for brevity)
        filtered_controls = mock_controls
        if search:
            search_lower = search.lower()
            filtered_controls = [
                control for control in filtered_controls
                if search_lower in control.control_id.lower() or
                   search_lower in control.control_name.lower() or
                   search_lower in control.control_description.lower()
            ]
        
        # Define export columns
        available_columns = {
            "control_id": "Control ID",
            "control_name": "Control Name",
            "control_description": "Description",
            "category": "Category",
            "priority_level": "Priority",
            "tags": "Tags",
            "created_at": "Created Date"
        }
        
        # Determine which columns to export
        if columns:
            export_columns = [col.strip() for col in columns.split(',') if col.strip() in available_columns]
        else:
            export_columns = ["control_id", "control_name", "category", "priority_level", "tags"]
        
        # Prepare export data
        export_data = []
        for control in filtered_controls:
            row = {}
            for col in export_columns:
                if col == "tags":
                    row[available_columns[col]] = ", ".join(control.tags)
                elif col == "created_at":
                    row[available_columns[col]] = control.created_at.isoformat()
                else:
                    row[available_columns[col]] = getattr(control, col, "")
            export_data.append(row)
        
        # Return export metadata (in real implementation, this would generate actual files)
        return {
            "export_id": str(uuid.uuid4()),
            "framework_id": framework_id,
            "framework_name": get_framework_name(framework_id),
            "format": format,
            "total_controls": len(export_data),
            "columns_exported": [available_columns[col] for col in export_columns],
            "filters_applied": {
                "search": search,
                "category": category,
                "priority": priority,
                "status": status,
                "tags": tags
            },
            "export_url": f"/api/framework-management/downloads/{str(uuid.uuid4())}.{format}",
            "generated_at": datetime.utcnow().isoformat(),
            "expires_after": "24 hours"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/frameworks/{framework_id}/controls/stats", summary="Get Control Statistics")
async def get_control_statistics(
    framework_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive statistics about controls in a framework
    """
    
    try:
        controls = generate_framework_controls(framework_id)
        
        # Calculate statistics
        total_controls = len(controls)
        category_stats = {}
        priority_stats = {}
        tag_stats = {}
        
        for control in controls:
            # Category statistics
            category_stats[control.category] = category_stats.get(control.category, 0) + 1
            
            # Priority statistics
            priority_stats[control.priority_level] = priority_stats.get(control.priority_level, 0) + 1
            
            # Tag statistics
            for tag in control.tags:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1
        
        return {
            "framework_id": framework_id,
            "framework_name": get_framework_name(framework_id),
            "total_controls": total_controls,
            "statistics": {
                "by_category": category_stats,
                "by_priority": priority_stats,
                "by_tags": dict(sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10 tags
            },
            "coverage_metrics": {
                "controls_with_descriptions": len([c for c in controls if c.control_description]),
                "controls_with_tags": len([c for c in controls if c.tags]),
                "controls_with_guidance": len([c for c in controls if c.implementation_guidance]),
                "average_tags_per_control": sum(len(c.tags) for c in controls) / total_controls if total_controls > 0 else 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")

@router.get("/frameworks/{framework_id}/controls/{control_id}", summary="Get Control Details")
async def get_control_details(
    framework_id: str,
    control_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific control within a framework
    """
    
    try:
        # Generate framework controls
        framework_controls = generate_framework_controls(framework_id)
        
        # Find the specific control
        control = next((c for c in framework_controls if c.control_id == control_id), None)
        
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")
        
        # Return detailed control information
        return {
            "control": control,
            "framework_info": {
                "id": framework_id,
                "name": get_framework_name(framework_id)
            },
            "related_controls": [
                {
                    "control_id": c.control_id,
                    "control_name": c.control_name,
                    "category": c.category
                }
                for c in framework_controls
                if c.category == control.category and c.control_id != control_id
            ][:5],  # Limit to 5 related controls
            "implementation_examples": [
                {
                    "title": "Technical Implementation",
                    "description": "Example technical approach for implementing this control",
                    "type": "technical"
                },
                {
                    "title": "Policy Template",
                    "description": "Sample policy template for compliance documentation",
                    "type": "policy"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve control details: {str(e)}")

# =====================================
# PHASE 1C: CONTROL MAPPING ENGINE MODELS & APIS
# =====================================

# Enhanced Mapping Models
class ControlMappingRelationship(BaseModel):
    """Advanced control mapping with relationship intelligence and AI-powered suggestions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str  # Reference to FrameworkControl
    control_name: str  # For display purposes
    framework_id: str  # Source framework
    
    # Target Information
    target_type: str  # "assessment_section", "policy", "risk_category", "business_unit"
    target_id: str  # ID of target entity
    target_name: str  # Display name of target
    
    # Mapping Intelligence
    mapping_strength: float = 0.8  # 0.0-1.0 confidence score
    mapping_type: str = "direct"  # "direct", "indirect", "regulatory", "recommended", "derived"
    auto_detected: bool = False  # AI-suggested vs manual mapping
    ai_suggestion_score: Optional[float] = None  # AI confidence if auto-detected
    
    # Business Context
    business_units: List[str] = []  # Applicable business units
    industry_relevance: List[str] = []  # Healthcare, Finance, etc.
    compliance_requirements: List[str] = []  # GDPR, HIPAA, SOC2, etc.
    regulatory_citations: List[str] = []  # Specific regulatory references
    
    # Validation & Status
    status: str = "active"  # "active", "pending_review", "deprecated", "archived"
    validation_status: str = "unvalidated"  # "validated", "conflicts", "needs_review", "unvalidated"
    conflict_reasons: List[str] = []
    resolution_notes: Optional[str] = None
    
    # Relationship Context
    mapping_rationale: Optional[str] = None  # Why this mapping exists
    evidence_references: List[str] = []  # Supporting documentation
    implementation_notes: Optional[str] = None
    
    # Metadata
    mapped_by: str  # User ID who created the mapping
    reviewed_by: Optional[str] = None  # User ID who validated
    approved_by: Optional[str] = None  # Final approver
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None
    
    # Organization context
    organization_id: str

class MappingTarget(BaseModel):
    """Available targets for control mapping"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    target_type: str  # "assessment_section", "policy", "risk_category", "business_unit"
    
    # Hierarchy and Classification
    parent_id: Optional[str] = None  # For hierarchical targets
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = []
    
    # Mapping Context
    accepts_controls_from: List[str] = []  # Framework types that can map here
    max_control_mappings: Optional[int] = None  # Limit mappings if needed
    
    # Status and Metadata
    status: str = "active"  # "active", "deprecated", "archived"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    organization_id: str

class MappingSuggestion(BaseModel):
    """AI-powered mapping suggestions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str
    suggested_target_id: str
    suggested_target_name: str
    target_type: str
    
    # AI Analysis
    confidence_score: float  # 0.0-1.0
    reasoning: str  # Why this mapping is suggested
    similarity_factors: List[str] = []  # Keywords, patterns that matched
    
    # Suggestion Context
    suggestion_type: str = "ai_semantic"  # "ai_semantic", "pattern_match", "industry_standard"
    based_on_existing: bool = False  # Based on similar existing mappings
    reference_mappings: List[str] = []  # Similar mappings used as reference
    
    # Status
    status: str = "pending"  # "pending", "accepted", "rejected", "reviewed"
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    organization_id: str

class MappingBulkOperation(BaseModel):
    """Bulk mapping operations for efficiency"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str  # "create", "update", "delete", "validate", "approve"
    
    # Target Selection
    control_ids: List[str] = []  # Controls involved
    target_ids: List[str] = []  # Targets involved
    framework_ids: List[str] = []  # Frameworks involved
    
    # Operation Parameters
    mapping_type: Optional[str] = None  # For create operations
    mapping_strength: Optional[float] = None
    business_units: List[str] = []
    compliance_requirements: List[str] = []
    
    # Execution Status
    status: str = "pending"  # "pending", "processing", "completed", "failed", "partial"
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    error_details: List[str] = []
    
    # Results
    created_mappings: List[str] = []  # IDs of created mappings
    updated_mappings: List[str] = []
    deleted_mappings: List[str] = []
    
    # Metadata
    initiated_by: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    organization_id: str

# API Request/Response Models for Phase 1C
class CreateMappingRequest(BaseModel):
    """Request to create a new control mapping"""
    control_id: str
    target_type: str
    target_id: str
    target_name: str
    mapping_type: str = "direct"
    mapping_strength: float = 0.8
    mapping_rationale: Optional[str] = None
    business_units: List[str] = []
    compliance_requirements: List[str] = []

class BulkMappingRequest(BaseModel):
    """Request for bulk mapping operations"""
    operation_type: str
    control_ids: List[str]
    target_type: str
    target_ids: List[str]
    mapping_parameters: Dict[str, Any] = {}

class MappingAnalyticsResponse(BaseModel):
    """Response with mapping analytics and insights"""
    framework_id: str
    framework_name: str
    total_controls: int
    mapped_controls: int
    unmapped_controls: int
    mapping_coverage_percentage: float
    
    # Breakdown by target type
    mappings_by_target_type: Dict[str, int]
    mappings_by_strength: Dict[str, int]
    mappings_by_status: Dict[str, int]
    
    # Quality Metrics
    validated_mappings: int
    conflicted_mappings: int
    ai_suggested_mappings: int
    manual_mappings: int
    
    # Recent Activity
    recent_mappings_count: int  # Last 30 days
    active_mapping_sessions: int
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# =====================================
# PHASE 1C-A: CORE MAPPING ENGINE API ENDPOINTS
# =====================================

@router.post("/frameworks/{framework_id}/mappings", summary="Create Control Mapping")
async def create_control_mapping(
    framework_id: str,
    mapping_request: CreateMappingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new control mapping with intelligent validation and conflict detection
    """
    
    try:
        # Validate control exists
        framework_controls = generate_framework_controls(framework_id)
        control = next((c for c in framework_controls if c.control_id == mapping_request.control_id), None)
        
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")
        
        # Create mapping with intelligence
        mapping = ControlMappingRelationship(
            control_id=mapping_request.control_id,
            control_name=control.control_name,
            framework_id=framework_id,
            target_type=mapping_request.target_type,
            target_id=mapping_request.target_id,
            target_name=mapping_request.target_name,
            mapping_type=mapping_request.mapping_type,
            mapping_strength=mapping_request.mapping_strength,
            mapping_rationale=mapping_request.mapping_rationale,
            business_units=mapping_request.business_units,
            compliance_requirements=mapping_request.compliance_requirements,
            mapped_by=current_user.id,  # Use actual user ID
            organization_id=current_user.organization_id  # Use actual organization ID
        )
        
        # TODO: In real implementation, save to database and check for conflicts
        
        return {
            "mapping_id": mapping.id,
            "status": "created",
            "control_id": mapping.control_id,
            "target_type": mapping.target_type,
            "target_id": mapping.target_id,
            "mapping_strength": mapping.mapping_strength,
            "validation_status": mapping.validation_status,
            "conflicts_detected": [],  # TODO: Implement conflict detection
            "created_at": mapping.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mapping: {str(e)}")

@router.get("/frameworks/{framework_id}/mappings", summary="List Framework Mappings")  
async def get_framework_mappings(
    framework_id: str,
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    status: Optional[str] = Query(None, description="Filter by mapping status"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status"),
    mapping_type: Optional[str] = Query(None, description="Filter by mapping type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Get all mappings for a framework with filtering and analytics
    """
    
    try:
        # Generate mock mappings for demonstration
        mock_mappings = generate_mock_mappings(framework_id)
        
        # Apply filters
        filtered_mappings = mock_mappings
        if target_type:
            filtered_mappings = [m for m in filtered_mappings if m.target_type == target_type]
        if status:
            filtered_mappings = [m for m in filtered_mappings if m.status == status]
        if validation_status:
            filtered_mappings = [m for m in filtered_mappings if m.validation_status == validation_status]
        if mapping_type:
            filtered_mappings = [m for m in filtered_mappings if m.mapping_type == mapping_type]
        
        # Apply pagination
        total_count = len(filtered_mappings)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_mappings = filtered_mappings[start_idx:end_idx]
        
        return {
            "mappings": page_mappings,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "analytics": {
                "total_mappings": len(mock_mappings),
                "by_target_type": get_mapping_breakdown(mock_mappings, "target_type"),
                "by_status": get_mapping_breakdown(mock_mappings, "status"),
                "by_validation": get_mapping_breakdown(mock_mappings, "validation_status"),
                "average_strength": sum(m.mapping_strength for m in mock_mappings) / len(mock_mappings) if mock_mappings else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mappings: {str(e)}")

@router.put("/mappings/{mapping_id}", summary="Update Control Mapping")
async def update_control_mapping(
    mapping_id: str,
    mapping_updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing control mapping with validation
    """
    
    try:
        # TODO: In real implementation, fetch mapping from database
        
        # Simulate update
        updated_fields = []
        for field, value in mapping_updates.items():
            if field in ["mapping_strength", "mapping_type", "status", "validation_status", "mapping_rationale"]:
                updated_fields.append(field)
        
        return {
            "mapping_id": mapping_id,
            "status": "updated",
            "updated_fields": updated_fields,
            "updated_at": datetime.utcnow().isoformat(),
            "validation_required": "mapping_strength" in updated_fields or "mapping_type" in updated_fields
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")

@router.delete("/mappings/{mapping_id}", summary="Delete Control Mapping")
async def delete_control_mapping(
    mapping_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a control mapping with audit trail
    """
    
    try:
        # TODO: In real implementation, soft delete with audit trail
        
        return {
            "mapping_id": mapping_id,
            "status": "deleted", 
            "deleted_at": datetime.utcnow().isoformat(),
            "audit_trail_created": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mapping: {str(e)}")

@router.get("/mapping-targets", summary="Get Available Mapping Targets")
async def get_mapping_targets(
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available targets for control mapping
    """
    
    try:
        # Generate mock targets
        mock_targets = generate_mock_targets()
        
        # Apply filter
        if target_type:
            mock_targets = [t for t in mock_targets if t.target_type == target_type]
        
        # Group by target type
        targets_by_type = {}
        for target in mock_targets:
            if target.target_type not in targets_by_type:
                targets_by_type[target.target_type] = []
            targets_by_type[target.target_type].append(target)
        
        return {
            "targets": mock_targets,
            "targets_by_type": targets_by_type,
            "total_targets": len(mock_targets),
            "target_types": list(targets_by_type.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mapping targets: {str(e)}")

@router.get("/frameworks/{framework_id}/mapping-analytics", summary="Get Mapping Analytics")
async def get_mapping_analytics(
    framework_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive mapping analytics and coverage insights
    """
    
    try:
        # Get framework info
        framework_name = get_framework_name(framework_id)
        controls = generate_framework_controls(framework_id)
        mappings = generate_mock_mappings(framework_id)
        
        # Calculate analytics
        total_controls = len(controls)
        mapped_controls = len(set(m.control_id for m in mappings))
        unmapped_controls = total_controls - mapped_controls
        coverage_percentage = (mapped_controls / total_controls * 100) if total_controls > 0 else 0
        
        analytics = MappingAnalyticsResponse(
            framework_id=framework_id,
            framework_name=framework_name,
            total_controls=total_controls,
            mapped_controls=mapped_controls,
            unmapped_controls=unmapped_controls,
            mapping_coverage_percentage=round(coverage_percentage, 1),
            mappings_by_target_type=get_mapping_breakdown(mappings, "target_type"),
            mappings_by_strength={
                "high": len([m for m in mappings if m.mapping_strength >= 0.8]),
                "medium": len([m for m in mappings if 0.5 <= m.mapping_strength < 0.8]),
                "low": len([m for m in mappings if m.mapping_strength < 0.5])
            },
            mappings_by_status=get_mapping_breakdown(mappings, "status"),
            validated_mappings=len([m for m in mappings if m.validation_status == "validated"]),
            conflicted_mappings=len([m for m in mappings if m.validation_status == "conflicts"]),
            ai_suggested_mappings=len([m for m in mappings if m.auto_detected]),
            manual_mappings=len([m for m in mappings if not m.auto_detected]),
            recent_mappings_count=len([m for m in mappings if (datetime.utcnow() - m.created_at).days <= 30]),
            active_mapping_sessions=3  # Mock data
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate mapping analytics: {str(e)}")

# =====================================
# PHASE 1C-C: ADVANCED ANALYTICS & OPTIMIZATION ENDPOINTS
# =====================================

@router.get("/frameworks/{framework_id}/coverage-heatmap", summary="Get Coverage Heatmap Data")
async def get_coverage_heatmap(
    framework_id: str,
    dimension: str = Query("category", description="Heatmap dimension: category, business_unit, target_type"),
    current_user: User = Depends(get_current_user)
):
    """
    Get coverage heatmap data for advanced visualization
    
    Provides matrix data showing control coverage across different dimensions
    """
    
    try:
        controls = generate_framework_controls(framework_id)
        mappings = generate_mock_mappings(framework_id)
        targets = generate_mock_targets()
        
        # Build heatmap data based on dimension
        if dimension == "category":
            # Coverage by control category vs target type
            categories = list(set(c.category for c in controls))
            target_types = ["assessment_section", "policy", "risk_category", "business_unit"]
            
            heatmap_data = []
            for category in categories:
                category_controls = [c.control_id for c in controls if c.category == category]
                row_data = {"category": category, "total_controls": len(category_controls)}
                
                for target_type in target_types:
                    mapped_count = len([m for m in mappings 
                                      if m.control_id in category_controls and m.target_type == target_type])
                    coverage_pct = (mapped_count / len(category_controls) * 100) if category_controls else 0
                    row_data[target_type] = {
                        "mapped_count": mapped_count,
                        "coverage_percentage": round(coverage_pct, 1),
                        "strength_average": round(sum(m.mapping_strength for m in mappings 
                                                    if m.control_id in category_controls and m.target_type == target_type) / 
                                                (mapped_count if mapped_count > 0 else 1), 2)
                    }
                
                heatmap_data.append(row_data)
                
        elif dimension == "business_unit":
            # Coverage by business unit vs control category
            business_units = [t.name for t in targets if t.target_type == "business_unit"]
            categories = list(set(c.category for c in controls))
            
            heatmap_data = []
            for unit in business_units:
                row_data = {"business_unit": unit}
                
                for category in categories:
                    category_controls = [c.control_id for c in controls if c.category == category]
                    mapped_count = len([m for m in mappings 
                                      if m.control_id in category_controls and unit in m.business_units])
                    coverage_pct = (mapped_count / len(category_controls) * 100) if category_controls else 0
                    row_data[category.replace(" ", "_").lower()] = {
                        "mapped_count": mapped_count,
                        "coverage_percentage": round(coverage_pct, 1)
                    }
                
                heatmap_data.append(row_data)
        
        else:  # target_type
            # Coverage by target type vs priority level
            target_types = ["assessment_section", "policy", "risk_category", "business_unit"]
            priorities = ["critical", "high", "medium", "low"]
            
            heatmap_data = []
            for target_type in target_types:
                row_data = {"target_type": target_type}
                
                for priority in priorities:
                    priority_controls = [c.control_id for c in controls if c.priority_level == priority]
                    mapped_count = len([m for m in mappings 
                                      if m.control_id in priority_controls and m.target_type == target_type])
                    coverage_pct = (mapped_count / len(priority_controls) * 100) if priority_controls else 0
                    row_data[priority] = {
                        "mapped_count": mapped_count,
                        "coverage_percentage": round(coverage_pct, 1)
                    }
                
                heatmap_data.append(row_data)
        
        return {
            "framework_id": framework_id,
            "dimension": dimension,
            "heatmap_data": heatmap_data,
            "metadata": {
                "total_controls": len(controls),
                "total_mappings": len(mappings),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap data: {str(e)}")

@router.get("/frameworks/{framework_id}/relationship-graph", summary="Get Mapping Relationship Graph")
async def get_relationship_graph(
    framework_id: str,
    include_ai_suggestions: bool = Query(False, description="Include AI mapping suggestions"),
    current_user: User = Depends(get_current_user)
):
    """
    Get relationship graph data for network visualization of control mappings
    """
    
    try:
        controls = generate_framework_controls(framework_id)
        mappings = generate_mock_mappings(framework_id)
        targets = generate_mock_targets()
        
        # Build nodes (controls and targets)
        nodes = []
        
        # Control nodes
        for control in controls:
            control_mappings = [m for m in mappings if m.control_id == control.control_id]
            nodes.append({
                "id": control.control_id,
                "label": control.control_id,
                "name": control.control_name,
                "type": "control",
                "category": control.category,
                "priority": control.priority_level,
                "mapping_count": len(control_mappings),
                "size": max(10, min(50, len(control_mappings) * 8)),  # Node size based on mappings
                "color": get_priority_color(control.priority_level)
            })
        
        # Target nodes
        target_mapping_counts = {}
        for mapping in mappings:
            key = f"{mapping.target_type}_{mapping.target_id}"
            target_mapping_counts[key] = target_mapping_counts.get(key, 0) + 1
        
        for target in targets:
            key = f"{target.target_type}_{target.id}"
            mapping_count = target_mapping_counts.get(key, 0)
            
            nodes.append({
                "id": key,
                "label": target.name,
                "name": target.name,
                "type": "target",
                "target_type": target.target_type,
                "category": target.category,
                "mapping_count": mapping_count,
                "size": max(8, min(40, mapping_count * 6)),
                "color": get_target_type_color(target.target_type)
            })
        
        # Build edges (mappings)
        edges = []
        for mapping in mappings:
            target_key = f"{mapping.target_type}_{mapping.target_id}"
            edges.append({
                "id": mapping.id,
                "source": mapping.control_id,
                "target": target_key,
                "strength": mapping.mapping_strength,
                "type": mapping.mapping_type,
                "auto_detected": mapping.auto_detected,
                "validation_status": mapping.validation_status,
                "width": max(1, mapping.mapping_strength * 5),  # Edge width based on strength
                "color": get_mapping_strength_color(mapping.mapping_strength),
                "style": "dashed" if mapping.auto_detected else "solid"
            })
        
        # Calculate network metrics
        network_metrics = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "control_nodes": len([n for n in nodes if n["type"] == "control"]),
            "target_nodes": len([n for n in nodes if n["type"] == "target"]),
            "average_connections_per_control": len(edges) / len([n for n in nodes if n["type"] == "control"]) if controls else 0,
            "most_connected_control": max(nodes, key=lambda x: x["mapping_count"] if x["type"] == "control" else 0)["label"] if nodes else None,
            "most_connected_target": max(nodes, key=lambda x: x["mapping_count"] if x["type"] == "target" else 0)["label"] if nodes else None
        }
        
        return {
            "framework_id": framework_id,
            "graph_data": {
                "nodes": nodes,
                "edges": edges
            },
            "network_metrics": network_metrics,
            "legend": {
                "node_types": {
                    "control": "Framework Controls",
                    "target": "Mapping Targets"
                },
                "target_types": {
                    "assessment_section": "Assessment Sections",
                    "policy": "Policies",
                    "risk_category": "Risk Categories",
                    "business_unit": "Business Units"
                },
                "mapping_strengths": {
                    "high": "0.8 - 1.0",
                    "medium": "0.5 - 0.8",
                    "low": "0.0 - 0.5"
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate relationship graph: {str(e)}")

@router.get("/frameworks/{framework_id}/gap-trend-analysis", summary="Get Gap and Trend Analysis")
async def get_gap_trend_analysis(
    framework_id: str,
    time_period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user)
):
    """
    Get gap analysis and trend data for mapping progress and coverage evolution
    """
    
    try:
        controls = generate_framework_controls(framework_id)
        mappings = generate_mock_mappings(framework_id)
        
        # Generate historical data for trends (mock implementation)
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[time_period]
        trend_data = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i)
            # Simulate gradual mapping progress
            progress_factor = (i + 1) / days
            simulated_mappings = int(len(mappings) * progress_factor)
            simulated_coverage = (simulated_mappings / len(controls) * 100) if controls else 0
            
            trend_data.append({
                "date": date.isoformat()[:10],
                "total_mappings": simulated_mappings,
                "coverage_percentage": round(simulated_coverage, 1),
                "new_mappings": max(0, simulated_mappings - (int(len(mappings) * ((i) / days)) if i > 0 else 0)),
                "validated_mappings": int(simulated_mappings * 0.7),  # 70% validated
                "ai_suggested": int(simulated_mappings * 0.3)  # 30% AI suggested
            })
        
        # Gap analysis - identify unmapped controls and patterns
        mapped_control_ids = set(m.control_id for m in mappings)
        unmapped_controls = [c for c in controls if c.control_id not in mapped_control_ids]
        
        # Analyze gaps by category
        gap_by_category = {}
        for control in unmapped_controls:
            category = control.category
            if category not in gap_by_category:
                gap_by_category[category] = {"count": 0, "controls": [], "priority_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0}}
            
            gap_by_category[category]["count"] += 1
            gap_by_category[category]["controls"].append({
                "control_id": control.control_id,
                "name": control.control_name,
                "priority": control.priority_level
            })
            gap_by_category[category]["priority_breakdown"][control.priority_level] += 1
        
        # Identify mapping quality issues
        quality_issues = {
            "low_strength_mappings": [
                {
                    "control_id": m.control_id,
                    "target_name": m.target_name,
                    "strength": m.mapping_strength,
                    "type": m.mapping_type
                }
                for m in mappings if m.mapping_strength < 0.5
            ],
            "unvalidated_mappings": [
                {
                    "control_id": m.control_id,
                    "target_name": m.target_name,
                    "validation_status": m.validation_status,
                    "created_at": m.created_at.isoformat()[:10]
                }
                for m in mappings if m.validation_status == "unvalidated"
            ],
            "conflicted_mappings": [
                {
                    "control_id": m.control_id,
                    "target_name": m.target_name,
                    "conflict_reasons": m.conflict_reasons,
                    "resolution_notes": m.resolution_notes
                }
                for m in mappings if m.validation_status == "conflicts"
            ]
        }
        
        # Progress predictions (simple linear projection)
        current_rate = len(trend_data[-7:]) if len(trend_data) >= 7 else 1
        if current_rate > 0:
            daily_mapping_rate = sum(d["new_mappings"] for d in trend_data[-7:]) / 7
            days_to_completion = (len(unmapped_controls) / daily_mapping_rate) if daily_mapping_rate > 0 else float('inf')
            estimated_completion = datetime.utcnow() + timedelta(days=days_to_completion) if days_to_completion != float('inf') else None
        else:
            daily_mapping_rate = 0
            estimated_completion = None
        
        return {
            "framework_id": framework_id,
            "time_period": time_period,
            "trend_analysis": {
                "historical_data": trend_data,
                "current_coverage": round((len(mappings) / len(controls) * 100) if controls else 0, 1),
                "coverage_change": round(trend_data[-1]["coverage_percentage"] - trend_data[0]["coverage_percentage"], 1) if trend_data else 0,
                "daily_mapping_rate": round(daily_mapping_rate, 2),
                "estimated_completion": estimated_completion.isoformat()[:10] if estimated_completion else None
            },
            "gap_analysis": {
                "total_unmapped": len(unmapped_controls),
                "unmapped_by_category": gap_by_category,
                "priority_gaps": {
                    "critical": len([c for c in unmapped_controls if c.priority_level == "critical"]),
                    "high": len([c for c in unmapped_controls if c.priority_level == "high"]),
                    "medium": len([c for c in unmapped_controls if c.priority_level == "medium"]),
                    "low": len([c for c in unmapped_controls if c.priority_level == "low"])
                }
            },
            "quality_analysis": quality_issues,
            "recommendations": generate_mapping_recommendations(controls, mappings, unmapped_controls),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate gap and trend analysis: {str(e)}")

@router.get("/frameworks/{framework_id}/analytics-export", summary="Export Analytics Report")
async def export_analytics_report(
    framework_id: str,
    report_type: str = Query("comprehensive", description="Report type: comprehensive, coverage, gaps, trends"),
    format: str = Query("pdf", description="Export format: pdf, xlsx, json, csv"),
    include_charts: bool = Query(True, description="Include charts and visualizations"),
    current_user: User = Depends(get_current_user)
):
    """
    Export comprehensive analytics report in various formats
    """
    
    try:
        # Gather all analytics data
        framework_name = get_framework_name(framework_id)
        controls = generate_framework_controls(framework_id)
        mappings = generate_mock_mappings(framework_id)
        
        # Get analytics data based on report type
        if report_type == "comprehensive":
            # Include all analytics
            coverage_data = await get_coverage_heatmap(framework_id, "category", current_user)
            relationship_data = await get_relationship_graph(framework_id, False, current_user)
            gap_trend_data = await get_gap_trend_analysis(framework_id, "30d", current_user)
            basic_analytics = await get_mapping_analytics(framework_id, current_user)
            
            export_data = {
                "report_type": "Comprehensive Analytics Report",
                "framework": {"id": framework_id, "name": framework_name},
                "executive_summary": {
                    "total_controls": len(controls),
                    "mapped_controls": len(set(m.control_id for m in mappings)),
                    "coverage_percentage": basic_analytics.mapping_coverage_percentage,
                    "quality_score": calculate_quality_score(mappings),
                    "completion_trend": "Improving" if len(mappings) > 0 else "Not Started"
                },
                "coverage_analysis": coverage_data,
                "relationship_network": relationship_data,
                "gap_and_trends": gap_trend_data,
                "detailed_metrics": basic_analytics
            }
            
        elif report_type == "coverage":
            coverage_data = await get_coverage_heatmap(framework_id, "category", current_user)
            export_data = {
                "report_type": "Coverage Analysis Report",
                "framework": {"id": framework_id, "name": framework_name},
                "coverage_analysis": coverage_data
            }
            
        elif report_type == "gaps":
            gap_data = await get_gap_trend_analysis(framework_id, "30d", current_user)
            export_data = {
                "report_type": "Gap Analysis Report", 
                "framework": {"id": framework_id, "name": framework_name},
                "gap_analysis": gap_data["gap_analysis"],
                "quality_analysis": gap_data["quality_analysis"],
                "recommendations": gap_data["recommendations"]
            }
            
        else:  # trends
            trend_data = await get_gap_trend_analysis(framework_id, "90d", current_user)
            export_data = {
                "report_type": "Trend Analysis Report",
                "framework": {"id": framework_id, "name": framework_name},
                "trend_analysis": trend_data["trend_analysis"]
            }
        
        # Generate export metadata
        export_id = str(uuid.uuid4())
        export_filename = f"{framework_name.replace(' ', '_')}_{report_type}_analytics_{datetime.utcnow().strftime('%Y%m%d')}".lower()
        
        return {
            "export_id": export_id,
            "framework_id": framework_id,
            "framework_name": framework_name,
            "report_type": report_type,
            "format": format,
            "filename": f"{export_filename}.{format}",
            "include_charts": include_charts,
            "data_summary": {
                "total_sections": len(export_data.keys()) - 2,  # Exclude report_type and framework
                "total_controls_analyzed": len(controls),
                "total_mappings_included": len(mappings),
                "data_points": count_data_points(export_data)
            },
            "download_url": f"/api/framework-management/downloads/{export_id}.{format}",
            "export_data": export_data if format == "json" else None,  # Include data for JSON format
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "generated_by": current_user.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export analytics report: {str(e)}")

# =====================================
# PHASE 1C-C: HELPER FUNCTIONS
# =====================================

def get_priority_color(priority: str) -> str:
    """Get color code for control priority levels"""
    colors = {
        "critical": "#ef4444",  # red-500
        "high": "#f97316",      # orange-500
        "medium": "#eab308",    # yellow-500
        "low": "#22c55e"        # green-500
    }
    return colors.get(priority, "#6b7280")  # gray-500

def get_target_type_color(target_type: str) -> str:
    """Get color code for target types"""
    colors = {
        "assessment_section": "#3b82f6",  # blue-500
        "policy": "#8b5cf6",              # violet-500
        "risk_category": "#f59e0b",       # amber-500
        "business_unit": "#10b981"        # emerald-500
    }
    return colors.get(target_type, "#6b7280")  # gray-500

def get_mapping_strength_color(strength: float) -> str:
    """Get color code for mapping strength"""
    if strength >= 0.8:
        return "#22c55e"  # green-500 (high)
    elif strength >= 0.5:
        return "#eab308"  # yellow-500 (medium)
    else:
        return "#ef4444"  # red-500 (low)

def calculate_quality_score(mappings: List[ControlMappingRelationship]) -> float:
    """Calculate overall quality score for mappings"""
    if not mappings:
        return 0.0
    
    # Factors: validation status, strength, conflicts
    total_score = 0
    for mapping in mappings:
        score = mapping.mapping_strength  # Base score from strength
        
        # Validation bonus/penalty
        if mapping.validation_status == "validated":
            score += 0.2
        elif mapping.validation_status == "conflicts":
            score -= 0.3
        
        # AI suggestion bonus (shows good automation)
        if mapping.auto_detected and mapping.ai_suggestion_score and mapping.ai_suggestion_score > 0.8:
            score += 0.1
        
        total_score += min(1.0, max(0.0, score))  # Clamp between 0-1
    
    return round(total_score / len(mappings), 2)

def generate_mapping_recommendations(
    controls: List[FrameworkControl], 
    mappings: List[ControlMappingRelationship], 
    unmapped_controls: List[FrameworkControl]
) -> List[Dict[str, Any]]:
    """Generate intelligent mapping recommendations"""
    
    recommendations = []
    
    # Priority-based recommendations
    critical_unmapped = [c for c in unmapped_controls if c.priority_level == "critical"]
    if critical_unmapped:
        recommendations.append({
            "type": "priority",
            "title": "Map Critical Controls First",
            "description": f"{len(critical_unmapped)} critical controls are unmapped and should be prioritized",
            "action": "Review and map critical priority controls immediately",
            "impact": "high",
            "controls": [c.control_id for c in critical_unmapped[:5]]  # Show first 5
        })
    
    # Quality improvement recommendations
    low_strength = [m for m in mappings if m.mapping_strength < 0.5]
    if low_strength:
        recommendations.append({
            "type": "quality",
            "title": "Improve Low-Strength Mappings",
            "description": f"{len(low_strength)} mappings have low strength scores and may need review",
            "action": "Review and strengthen weak mappings or consider removing if not applicable",
            "impact": "medium",
            "mappings": [{"control_id": m.control_id, "strength": m.mapping_strength} for m in low_strength[:5]]
        })
    
    # Validation recommendations
    unvalidated = [m for m in mappings if m.validation_status == "unvalidated"]
    if unvalidated:
        recommendations.append({
            "type": "validation",
            "title": "Validate Pending Mappings", 
            "description": f"{len(unvalidated)} mappings are pending validation",
            "action": "Review and validate mappings to ensure accuracy and compliance",
            "impact": "medium",
            "count": len(unvalidated)
        })
    
    # Coverage gap recommendations
    category_gaps = {}
    for control in unmapped_controls:
        category_gaps[control.category] = category_gaps.get(control.category, 0) + 1
    
    if category_gaps:
        worst_category = max(category_gaps.items(), key=lambda x: x[1])
        recommendations.append({
            "type": "coverage",
            "title": f"Address {worst_category[0]} Coverage Gap",
            "description": f"{worst_category[1]} controls in {worst_category[0]} category are unmapped",
            "action": f"Focus mapping efforts on {worst_category[0]} controls to improve coverage balance",
            "impact": "medium",
            "category": worst_category[0],
            "unmapped_count": worst_category[1]
        })
    
    return recommendations

def count_data_points(data: Dict[str, Any]) -> int:
    """Recursively count data points in nested dictionary"""
    count = 0
    for value in data.values():
        if isinstance(value, dict):
            count += count_data_points(value)
        elif isinstance(value, list):
            count += len(value)
        else:
            count += 1
    return count

# =====================================
# PHASE 1C-A: HELPER FUNCTIONS
# =====================================

def generate_mock_mappings(framework_id: str) -> List[ControlMappingRelationship]:
    """Generate mock mapping data for demonstration"""
    
    controls = generate_framework_controls(framework_id)
    mappings = []
    
    # Create sample mappings for first few controls
    target_types = ["assessment_section", "policy", "risk_category", "business_unit"]
    mapping_types = ["direct", "indirect", "regulatory", "recommended"]
    statuses = ["active", "pending_review", "validated"]
    validation_statuses = ["validated", "unvalidated", "needs_review", "conflicts"]
    
    for i, control in enumerate(controls[:min(int(len(controls) * 0.6), len(controls))]):  # Map only 60% of controls to ensure gaps
        # Create 1-3 mappings per control
        num_mappings = min(3, (i % 3) + 1)
        
        for j in range(num_mappings):
            mapping = ControlMappingRelationship(
                control_id=control.control_id,
                control_name=control.control_name,
                framework_id=framework_id,
                target_type=target_types[j % len(target_types)],
                target_id=f"target_{i}_{j}",
                target_name=f"Sample {target_types[j % len(target_types)].replace('_', ' ').title()} {i+1}",
                mapping_strength=round(0.5 + (i * 0.05) + (j * 0.1), 2),
                mapping_type=mapping_types[j % len(mapping_types)],
                auto_detected=(i + j) % 4 == 0,  # Some AI-suggested
                ai_suggestion_score=0.85 if (i + j) % 4 == 0 else None,
                business_units=["IT", "Compliance"] if i % 2 == 0 else ["Legal", "Risk"],
                compliance_requirements=["GDPR", "SOC2"] if i % 3 == 0 else ["HIPAA"],
                status=statuses[i % len(statuses)],
                validation_status=validation_statuses[j % len(validation_statuses)],
                mapped_by=f"user_{(i + j) % 3 + 1}",
                organization_id="org_001"
            )
            mappings.append(mapping)
    
    return mappings

def generate_mock_targets() -> List[MappingTarget]:
    """Generate mock mapping targets"""
    
    targets = []
    
    # Assessment sections
    assessment_sections = [
        "Access Control Management", "Data Protection & Privacy", "Risk Assessment & Management",
        "Incident Response", "Business Continuity", "Asset Management", "Vendor Management",
        "Security Awareness Training", "Physical Security", "Network Security"
    ]
    
    for i, section in enumerate(assessment_sections):
        target = MappingTarget(
            name=section,
            description=f"Assessment section covering {section.lower()} requirements",
            target_type="assessment_section",
            category="Assessment",
            tags=["assessment", "evaluation"],
            created_by=f"admin_user_{i % 3 + 1}",
            organization_id="org_001"
        )
        targets.append(target)
    
    # Policies
    policies = [
        "Information Security Policy", "Data Retention Policy", "Access Control Policy",
        "Incident Response Policy", "Business Continuity Policy", "Vendor Management Policy"
    ]
    
    for i, policy in enumerate(policies):
        target = MappingTarget(
            name=policy,
            description=f"Organizational policy for {policy.lower().replace(' policy', '')}",
            target_type="policy",
            category="Policy",
            tags=["policy", "governance"],
            created_by=f"admin_user_{i % 3 + 1}",
            organization_id="org_001"
        )
        targets.append(target)
    
    # Risk categories
    risk_categories = [
        "Operational Risk", "Data Privacy Risk", "Cybersecurity Risk", "Compliance Risk",
        "Financial Risk", "Reputational Risk", "Strategic Risk"
    ]
    
    for i, risk in enumerate(risk_categories):
        target = MappingTarget(
            name=risk,
            description=f"Risk category covering {risk.lower()} management",
            target_type="risk_category",
            category="Risk",
            tags=["risk", "management"],
            created_by=f"admin_user_{i % 3 + 1}",
            organization_id="org_001"
        )
        targets.append(target)
    
    # Business units
    business_units = [
        "Information Technology", "Human Resources", "Finance & Accounting", 
        "Legal & Compliance", "Operations", "Marketing & Sales"
    ]
    
    for i, unit in enumerate(business_units):
        target = MappingTarget(
            name=unit,
            description=f"Business unit responsible for {unit.lower()} operations",
            target_type="business_unit",
            category="Organization",
            tags=["business", "organization"],
            created_by=f"admin_user_{i % 3 + 1}",
            organization_id="org_001"
        )
        targets.append(target)
    
    return targets

def get_mapping_breakdown(mappings: List[ControlMappingRelationship], field: str) -> Dict[str, int]:
    """Get breakdown of mappings by a specific field"""
    
    breakdown = {}
    for mapping in mappings:
        value = getattr(mapping, field, "unknown")
        breakdown[value] = breakdown.get(value, 0) + 1
    
    return breakdown

# =====================================
# PHASE 1B: HELPER FUNCTIONS
# =====================================

def generate_framework_controls(framework_id: str) -> List[FrameworkControl]:
    """
    Generate comprehensive mock control data for different frameworks
    """
    
    # Framework-specific control data
    framework_configs = {
        "iso-27001-2022": {
            "name": "ISO/IEC 27001:2022",
            "controls": [
                {
                    "control_id": "A.5.1.1",
                    "name": "Policies for information security",
                    "description": "A set of policies for information security shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel and relevant interested parties.",
                    "category": "Organizational security",
                    "tags": ["Policy", "Governance", "Management"],
                    "priority": "high"
                },
                {
                    "control_id": "A.5.1.2",
                    "name": "Information security roles and responsibilities",
                    "description": "Information security roles and responsibilities shall be defined and allocated according to the organization needs.",
                    "category": "Organizational security", 
                    "tags": ["Roles", "Governance", "Responsibility"],
                    "priority": "high"
                },
                {
                    "control_id": "A.6.1.1",
                    "name": "Access control policy",
                    "description": "An access control policy shall be established, documented and reviewed based on business and information security requirements.",
                    "category": "Access control",
                    "tags": ["Access", "Policy", "Control"],
                    "priority": "critical"
                },
                {
                    "control_id": "A.6.1.2",
                    "name": "Access to networks and network services",
                    "description": "Users shall only be provided with access to the network and network services that they have been specifically authorized to use.",
                    "category": "Access control",
                    "tags": ["Network", "Access", "Authorization"],
                    "priority": "critical"
                },
                {
                    "control_id": "A.7.1.1",
                    "name": "Screening",
                    "description": "Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws, regulations and ethics.",
                    "category": "Human resource security",
                    "tags": ["HR", "Screening", "Background"],
                    "priority": "medium"
                },
                {
                    "control_id": "A.8.1.1",
                    "name": "Inventory of assets",
                    "description": "Assets associated with information and information processing facilities shall be identified, and an inventory of these assets shall be drawn up and maintained.",
                    "category": "Asset management",
                    "tags": ["Assets", "Inventory", "Management"],
                    "priority": "high"
                },
                {
                    "control_id": "A.8.1.2",
                    "name": "Ownership of assets",
                    "description": "Assets maintained in the inventory shall be owned.",
                    "category": "Asset management",
                    "tags": ["Assets", "Ownership", "Accountability"],
                    "priority": "medium"
                },
                {
                    "control_id": "A.10.1.1",
                    "name": "Use of cryptography policy",
                    "description": "A policy on the use of cryptographic controls for protection of information shall be developed and implemented.",
                    "category": "Cryptography",
                    "tags": ["Cryptography", "Policy", "Protection"],
                    "priority": "high"
                }
            ]
        },
        "nist-csf-v2": {
            "name": "NIST Cybersecurity Framework v2.0",  
            "controls": [
                {
                    "control_id": "ID.AM-1",
                    "name": "Physical devices and systems within the organization are inventoried",
                    "description": "Maintain an accurate, complete, and up-to-date inventory of physical devices and systems within the organization.",
                    "category": "Asset Management",
                    "tags": ["Identity", "Assets", "Inventory"],
                    "priority": "high"
                },
                {
                    "control_id": "ID.AM-2", 
                    "name": "Software platforms and applications within the organization are inventoried",
                    "description": "Maintain an accurate, complete, and up-to-date inventory of software platforms and applications within the organization.",
                    "category": "Asset Management",
                    "tags": ["Identity", "Software", "Inventory"],
                    "priority": "high"
                },
                {
                    "control_id": "PR.AC-1",
                    "name": "Identities and credentials are issued, managed, verified, revoked, and audited",
                    "description": "Identity management processes and technologies are used to control access to assets and systems.",
                    "category": "Access Control",
                    "tags": ["Protect", "Identity", "Credentials"],
                    "priority": "critical"
                },
                {
                    "control_id": "PR.DS-1",
                    "name": "Data-at-rest is protected",
                    "description": "Data at rest is protected through appropriate mechanisms to prevent unauthorized access.",
                    "category": "Data Security",
                    "tags": ["Protect", "Data", "Encryption"],
                    "priority": "critical"
                },
                {
                    "control_id": "DE.AE-1",
                    "name": "A baseline of network operations and expected data flows is established and managed",
                    "description": "Network operations are monitored to identify potential cybersecurity events.",
                    "category": "Anomalies and Events",
                    "tags": ["Detect", "Network", "Monitoring"],
                    "priority": "medium"
                },
                {
                    "control_id": "RS.RP-1",
                    "name": "Response plan is executed during or after an incident",
                    "description": "Response processes and procedures are executed and maintained to ensure response to detected cybersecurity incidents.",
                    "category": "Response Planning",
                    "tags": ["Respond", "Planning", "Incident"],
                    "priority": "high"
                }
            ]
        },
        "soc2-tsc": {
            "name": "SOC 2 Trust Services Criteria",
            "controls": [
                {
                    "control_id": "CC1.1",
                    "name": "The entity demonstrates a commitment to integrity and ethical values",
                    "description": "Management and the board of directors demonstrate commitment to integrity and ethical values through their directives, actions, and behavior.",
                    "category": "Control Environment",
                    "tags": ["Common", "Ethics", "Governance"],
                    "priority": "critical"
                },
                {
                    "control_id": "CC2.1",
                    "name": "The entity demonstrates a commitment to competence",
                    "description": "Management defines competencies for key roles and evaluates competence across the organization.",
                    "category": "Control Environment", 
                    "tags": ["Common", "Competence", "HR"],
                    "priority": "high"
                },
                {
                    "control_id": "A1.1",
                    "name": "The entity authorizes, processes, and records transactions to meet the description of controls",
                    "description": "Transactions are authorized, processed, and recorded to provide reasonable assurance regarding the achievement of objectives.",
                    "category": "Availability",
                    "tags": ["Availability", "Processing", "Authorization"],
                    "priority": "high"
                },
                {
                    "control_id": "P1.1",
                    "name": "The entity provides notice about its privacy practices to meet the description of controls",
                    "description": "Notice is provided to data subjects about privacy practices to meet the description of controls in the system description.",
                    "category": "Privacy",
                    "tags": ["Privacy", "Notice", "Communication"],
                    "priority": "medium"
                }
            ]
        }
    }
    
    # Get framework config or use default
    config = framework_configs.get(framework_id, {
        "name": "Generic Framework",
        "controls": [
            {
                "control_id": "GEN.1.1",
                "name": "Generic Control 1",
                "description": "This is a generic control for demonstration purposes.",
                "category": "General",
                "tags": ["Generic", "Demo"],
                "priority": "medium"
            }
        ]
    })
    
    # Convert to FrameworkControl objects
    controls = []
    for i, control_data in enumerate(config["controls"]):
        control = FrameworkControl(
            framework_id=framework_id,
            control_id=control_data["control_id"],
            control_name=control_data["name"],
            control_description=control_data["description"],
            category=control_data["category"],
            reference_standard=config["name"],
            framework_version="1.0",
            tags=control_data["tags"],
            priority_level=control_data["priority"],
            implementation_guidance=f"Implementation guidance for {control_data['name']}",
            testing_procedures=f"Testing procedures for {control_data['control_id']}",
            evidence_requirements=[
                "Policy documentation",
                "Process procedures", 
                "Evidence of implementation",
                "Testing results"
            ]
        )
        controls.append(control)
    
    return controls

def get_framework_name(framework_id: str) -> str:
    """Get display name for framework"""
    names = {
        "iso-27001-2022": "ISO/IEC 27001:2022",
        "nist-csf-v2": "NIST Cybersecurity Framework v2.0",
        "soc2-tsc": "SOC 2 Trust Services Criteria"
    }
    return names.get(framework_id, "Unknown Framework")