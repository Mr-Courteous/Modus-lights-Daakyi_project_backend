"""
Multi-Framework API Endpoints for DAAKYI CompaaS
Phase 2 MVP - Framework Selection, Control Management, and Crosswalk Mapping
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from multi_framework import (
    MultiFrameworkEngine, 
    FrameworkType, 
    FrameworkControl, 
    CrosswalkMapping,
    get_multi_framework_engine
)
import logging

# RBAC imports
from mvp1_auth import get_current_user, require_admin, ensure_organization_access
from mvp1_models import MVP1User

logger = logging.getLogger(__name__)

# Create router for multi-framework endpoints
framework_router = APIRouter(prefix="/api/frameworks", tags=["Multi-Framework"])

# Pydantic models for request/response
class FrameworkSelectionRequest(BaseModel):
    organization_id: str
    selected_frameworks: List[str]
    assessment_name: str
    description: Optional[str] = None

class FrameworkToggleRequest(BaseModel):
    framework_type: str
    active: bool

class CrosswalkMappingResponse(BaseModel):
    id: str
    source_framework: str
    source_control_id: str
    target_framework: str
    target_control_id: str
    mapping_type: str
    confidence_score: float
    mapping_rationale: str

class FrameworkControlResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    function: Optional[str] = None
    framework_type: str
    priority: str

class FrameworkInfoResponse(BaseModel):
    id: str
    name: str
    version: str
    description: str
    framework_type: str
    total_controls: int
    is_active: bool

@framework_router.get("/available", response_model=List[FrameworkInfoResponse])
async def get_available_frameworks(
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Get list of all available compliance frameworks (All authenticated users)
    """
    try:
        frameworks = engine.get_available_frameworks()
        return [FrameworkInfoResponse(**framework) for framework in frameworks]
    except Exception as e:
        logger.error(f"Error fetching available frameworks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch available frameworks")

@framework_router.post("/toggle")
@require_admin
async def toggle_framework(
    request: FrameworkToggleRequest,
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Activate or deactivate a framework for the organization (Admin only)
    """
    try:
        # Convert string to FrameworkType enum
        try:
            framework_type = FrameworkType(request.framework_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid framework type: {request.framework_type}")
        
        if request.active:
            success = engine.activate_framework(framework_type)
            action = "activated"
        else:
            success = engine.deactivate_framework(framework_type)
            action = "deactivated"
        
        if success:
            return {
                "success": True,
                "message": f"Framework {framework_type.value} {action} successfully",
                "framework_type": framework_type.value,
                "active": request.active
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to {action.rstrip('d')} framework")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling framework: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to toggle framework")

@framework_router.get("/{framework_type}/controls", response_model=List[FrameworkControlResponse])
async def get_framework_controls(
    framework_type: str,
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Get all controls for a specific framework (All authenticated users)
    """
    try:
        # Convert string to FrameworkType enum
        try:
            fw_type = FrameworkType(framework_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid framework type: {framework_type}")
        
        controls = engine.get_framework_controls(fw_type)
        
        return [
            FrameworkControlResponse(
                id=control.id,
                title=control.title,
                description=control.description,
                category=control.category,
                function=control.function,
                framework_type=control.framework_type.value,
                priority=control.priority
            )
            for control in controls
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching framework controls: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch framework controls")

@framework_router.get("/crosswalk", response_model=List[CrosswalkMappingResponse])
async def get_crosswalk_mappings(
    source_framework: str = Query(..., description="Source framework type"),
    target_framework: str = Query(..., description="Target framework type"),
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Get crosswalk mappings between two frameworks (All authenticated users)
    """
    try:
        # Convert strings to FrameworkType enums
        try:
            source_fw = FrameworkType(source_framework)
            target_fw = FrameworkType(target_framework)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid framework type: {str(e)}")
        
        mappings = engine.get_crosswalk_mappings(source_fw, target_fw)
        
        return [
            CrosswalkMappingResponse(
                id=mapping.id,
                source_framework=mapping.source_framework.value,
                source_control_id=mapping.source_control_id,
                target_framework=mapping.target_framework.value,
                target_control_id=mapping.target_control_id,
                mapping_type=mapping.mapping_type,
                confidence_score=mapping.confidence_score,
                mapping_rationale=mapping.mapping_rationale
            )
            for mapping in mappings
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching crosswalk mappings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch crosswalk mappings")

@framework_router.get("/controls/{control_id}/related")
async def get_related_controls(
    control_id: str,
    source_framework: str = Query(..., description="Source framework type"),
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Find related controls across other frameworks for a given control (All authenticated users)
    """
    try:
        # Convert string to FrameworkType enum
        try:
            source_fw = FrameworkType(source_framework)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid framework type: {source_framework}")
        
        related_controls = engine.find_related_controls(control_id, source_fw)
        
        result = []
        for control, mapping in related_controls:
            result.append({
                "control": FrameworkControlResponse(
                    id=control.id,
                    title=control.title,
                    description=control.description,
                    category=control.category,
                    function=control.function,
                    framework_type=control.framework_type.value,
                    priority=control.priority
                ),
                "mapping": CrosswalkMappingResponse(
                    id=mapping.id,
                    source_framework=mapping.source_framework.value,
                    source_control_id=mapping.source_control_id,
                    target_framework=mapping.target_framework.value,
                    target_control_id=mapping.target_control_id,
                    mapping_type=mapping.mapping_type,
                    confidence_score=mapping.confidence_score,
                    mapping_rationale=mapping.mapping_rationale
                )
            })
        
        return {
            "control_id": control_id,
            "source_framework": source_framework,
            "related_controls": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding related controls: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to find related controls")

@framework_router.post("/assessments/multi-framework")
@require_admin
async def create_multi_framework_assessment(
    request: FrameworkSelectionRequest,
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Create a new assessment covering multiple frameworks (Admin only)
    """
    try:
        # Convert framework strings to FrameworkType enums
        selected_frameworks = []
        for fw_str in request.selected_frameworks:
            try:
                fw_type = FrameworkType(fw_str)
                selected_frameworks.append(fw_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid framework type: {fw_str}")
        
        # Create the multi-framework assessment
        assessment_data = engine.create_multi_framework_assessment(
            organization_id=request.organization_id,
            selected_frameworks=selected_frameworks
        )
        
        # Add request metadata
        assessment_data.update({
            "assessment_name": request.assessment_name,
            "description": request.description or f"Multi-framework assessment covering {len(selected_frameworks)} frameworks"
        })
        
        return {
            "success": True,
            "message": "Multi-framework assessment created successfully",
            "assessment": assessment_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating multi-framework assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create multi-framework assessment")

@framework_router.get("/stats")
async def get_framework_statistics(
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Get statistics about all frameworks and their relationships (All authenticated users)
    """
    try:
        frameworks = engine.get_available_frameworks()
        
        stats = {
            "total_frameworks": len(frameworks),
            "active_frameworks": len([f for f in frameworks if f["is_active"]]),
            "total_controls": sum(f["total_controls"] for f in frameworks),
            "frameworks_detail": {
                f["framework_type"]: {
                    "name": f["name"],
                    "controls": f["total_controls"],
                    "active": f["is_active"]
                }
                for f in frameworks
            },
            "crosswalk_mappings": {
                "total_mappings": len(engine.crosswalk_mappings),
                "mapping_types": {}
            }
        }
        
        # Count mapping types
        for mapping in engine.crosswalk_mappings:
            mapping_type = mapping.mapping_type
            if mapping_type not in stats["crosswalk_mappings"]["mapping_types"]:
                stats["crosswalk_mappings"]["mapping_types"][mapping_type] = 0
            stats["crosswalk_mappings"]["mapping_types"][mapping_type] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching framework statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch framework statistics")

@framework_router.get("/coverage-analysis")
async def get_framework_coverage_analysis(
    primary_framework: str = Query(..., description="Primary framework to analyze"),
    comparison_frameworks: List[str] = Query(..., description="Frameworks to compare against"),
    current_user: MVP1User = Depends(get_current_user),
    engine: MultiFrameworkEngine = Depends(get_multi_framework_engine)
):
    """
    Analyze coverage and gaps between frameworks (All authenticated users)
    """
    try:
        # Convert strings to FrameworkType enums
        try:
            primary_fw = FrameworkType(primary_framework)
            comparison_fws = [FrameworkType(fw) for fw in comparison_frameworks]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid framework type: {str(e)}")
        
        primary_controls = engine.get_framework_controls(primary_fw)
        
        coverage_analysis = {
            "primary_framework": {
                "type": primary_framework,
                "total_controls": len(primary_controls)
            },
            "comparison_frameworks": {},
            "coverage_summary": {
                "fully_covered": 0,
                "partially_covered": 0,
                "not_covered": 0,
                "overall_coverage_percentage": 0.0
            }
        }
        
        # Analyze each comparison framework
        for comp_fw in comparison_fws:
            mappings = engine.get_crosswalk_mappings(primary_fw, comp_fw)
            comp_controls = engine.get_framework_controls(comp_fw)
            
            direct_mappings = [m for m in mappings if m.mapping_type == "direct"]
            partial_mappings = [m for m in mappings if m.mapping_type in ["partial", "related"]]
            
            coverage_analysis["comparison_frameworks"][comp_fw.value] = {
                "total_controls": len(comp_controls),
                "direct_mappings": len(direct_mappings),
                "partial_mappings": len(partial_mappings),
                "total_mappings": len(mappings),
                "coverage_percentage": (len(mappings) / len(primary_controls) * 100) if primary_controls else 0
            }
        
        # Calculate overall coverage
        if primary_controls:
            all_mapped_controls = set()
            for comp_fw in comparison_fws:
                mappings = engine.get_crosswalk_mappings(primary_fw, comp_fw)
                for mapping in mappings:
                    all_mapped_controls.add(mapping.source_control_id)
            
            coverage_analysis["coverage_summary"]["overall_coverage_percentage"] = (
                len(all_mapped_controls) / len(primary_controls) * 100
            )
            
            # Count coverage types (simplified)
            fully_covered = len([c for c in primary_controls if c.id in all_mapped_controls])
            coverage_analysis["coverage_summary"]["fully_covered"] = fully_covered
            coverage_analysis["coverage_summary"]["not_covered"] = len(primary_controls) - fully_covered
        
        return coverage_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing framework coverage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze framework coverage")