"""
Phase 2B: Assessment Templates API
Implements assessment template management with framework control integration,
customizable workflows, and seamless integration with Phase 1 Control Mapping Engine.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
from models import (
    # Phase 2B Models
    AssessmentTemplate, AssessmentControlLink, CreateAssessmentFromTemplateRequest,
    AssessmentControlLinkRequest,
    
    # Phase 2A Models  
    AssessmentEngine, AssessmentConfiguration,
    
    # Existing Models
    User, ComplianceFramework, FrameworkControl
)
from auth import get_current_user

# Initialize router
assessment_templates_router = APIRouter()

# =====================================
# ASSESSMENT TEMPLATE MANAGEMENT
# =====================================

@assessment_templates_router.get("/templates", response_model=List[AssessmentTemplate])
async def list_assessment_templates(
    framework_id: Optional[str] = None,
    template_type: Optional[str] = None,
    complexity_level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List available assessment templates with filtering"""
    try:
        # Mock templates for development
        templates = [
            AssessmentTemplate(
                id=str(uuid.uuid4()),
                name="NIST CSF 2.0 Comprehensive Assessment",
                description="Complete assessment template covering all NIST Cybersecurity Framework 2.0 categories with detailed control mappings and evidence requirements.",
                framework_id="nist-csf-v2",
                framework_name="NIST CSF 2.0",
                linked_controls=[
                    "GV.OC-01", "GV.RM-01", "ID.AM-01", "ID.RA-01", 
                    "PR.AC-01", "PR.DS-01", "DE.CM-01", "RS.RP-01", "RC.RP-01"
                ],
                control_mapping={
                    "GV.OC-01": {
                        "weight": 1.5,
                        "required_evidence_types": ["policy", "procedure"],
                        "minimum_evidence_count": 2
                    },
                    "PR.AC-01": {
                        "weight": 2.0,
                        "required_evidence_types": ["policy", "procedure", "log"],
                        "minimum_evidence_count": 3
                    }
                },
                template_type="standard",
                complexity_level="advanced",
                estimated_duration_hours=40,
                business_units=["IT", "Security", "Compliance", "Legal"],
                required_roles=["CISO", "IT Manager", "Compliance Officer"],
                evidence_requirements={
                    "GV.OC-01": ["organizational_chart", "governance_policy"],
                    "PR.AC-01": ["access_control_policy", "user_access_logs", "role_matrix"]
                },
                mandatory_sections=["Governance", "Identity & Access Management", "Data Security"],
                review_workflow={
                    "levels": 2,
                    "roles": ["Compliance Manager", "CISO"],
                    "auto_approval_threshold": 85.0
                },
                approval_levels=2,
                question_templates=[
                    {
                        "control_id": "PR.AC-01",
                        "question_type": "multiple_choice",
                        "question_text": "How comprehensive is your organization's access control implementation?",
                        "options": [
                            {"value": "comprehensive", "label": "Comprehensive - Fully implemented across all systems", "score": 4},
                            {"value": "substantial", "label": "Substantial - Implemented for most critical systems", "score": 3},
                            {"value": "basic", "label": "Basic - Limited implementation", "score": 2},
                            {"value": "minimal", "label": "Minimal - Very limited or no implementation", "score": 1}
                        ]
                    }
                ],
                scoring_configuration={
                    "method": "weighted_average",
                    "weights": {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5},
                    "thresholds": {"excellent": 90, "good": 75, "satisfactory": 60, "needs_improvement": 40}
                },
                usage_count=24,
                average_completion_time=38.5,
                success_rate=92.3,
                created_by=current_user.id,
                organization_id=current_user.organization_id
            ),
            AssessmentTemplate(
                id=str(uuid.uuid4()),
                name="ISO 27001:2022 Rapid Assessment",
                description="Streamlined assessment template for ISO 27001:2022 compliance focusing on key control families with efficient evidence collection.",
                framework_id="iso-27001-2022",
                framework_name="ISO 27001:2022",
                linked_controls=[
                    "A.5.1.1", "A.8.1.1", "A.12.1.2", "A.13.1.1", "A.18.1.1"
                ],
                control_mapping={
                    "A.5.1.1": {
                        "weight": 1.8,
                        "required_evidence_types": ["policy"],
                        "minimum_evidence_count": 1
                    },
                    "A.8.1.1": {
                        "weight": 1.6,
                        "required_evidence_types": ["procedure", "log"],
                        "minimum_evidence_count": 2
                    }
                },
                template_type="regulatory",
                complexity_level="intermediate",
                estimated_duration_hours=20,
                business_units=["IT", "Security", "Operations"],
                required_roles=["IT Manager", "Security Officer"],
                evidence_requirements={
                    "A.5.1.1": ["information_security_policy"],
                    "A.8.1.1": ["asset_inventory", "asset_classification_procedure"]
                },
                mandatory_sections=["Information Security Management", "Asset Management"],
                review_workflow={
                    "levels": 1,
                    "roles": ["IT Manager"],
                    "auto_approval_threshold": 80.0
                },
                approval_levels=1,
                usage_count=15,
                average_completion_time=18.2,
                success_rate=87.5,
                created_by=current_user.id,
                organization_id=current_user.organization_id
            ),
            AssessmentTemplate(
                id=str(uuid.uuid4()),
                name="SOC 2 Type II Readiness Template",
                description="Comprehensive template for SOC 2 Type II audit preparation with focus on Trust Service Criteria and operational effectiveness.",
                framework_id="soc2-tsc",
                framework_name="SOC 2",
                linked_controls=[
                    "CC1.1", "CC2.1", "CC6.1", "CC7.1", "A1.1"
                ],
                control_mapping={
                    "CC1.1": {
                        "weight": 2.0,
                        "required_evidence_types": ["policy", "procedure", "evidence"],
                        "minimum_evidence_count": 3
                    }
                },
                template_type="regulatory",
                complexity_level="advanced",
                estimated_duration_hours=35,
                business_units=["IT", "Operations", "Finance", "HR"],
                required_roles=["COO", "IT Director", "Compliance Manager"],
                evidence_requirements={
                    "CC1.1": ["control_environment_policy", "governance_structure", "risk_assessment"]
                },
                mandatory_sections=["Control Environment", "Logical Access", "System Operations"],
                review_workflow={
                    "levels": 3,
                    "roles": ["IT Director", "COO", "External Auditor"],
                    "auto_approval_threshold": 90.0
                },
                approval_levels=3,
                usage_count=8,
                average_completion_time=42.1,
                success_rate=95.0,
                is_default=False,
                created_by=current_user.id,
                organization_id=current_user.organization_id
            )
        ]
        
        # Apply filters
        if framework_id:
            templates = [t for t in templates if t.framework_id == framework_id]
        if template_type:
            templates = [t for t in templates if t.template_type == template_type]
        if complexity_level:
            templates = [t for t in templates if t.complexity_level == complexity_level]
        
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment templates: {str(e)}"
        )

@assessment_templates_router.get("/templates/{template_id}", response_model=AssessmentTemplate)
async def get_assessment_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific assessment template"""
    try:
        # Mock template details (would retrieve from database)
        template = AssessmentTemplate(
            id=template_id,
            name="NIST CSF 2.0 Comprehensive Assessment",
            description="Complete assessment template covering all NIST Cybersecurity Framework 2.0 categories with detailed control mappings and evidence requirements.",
            framework_id="nist-csf-v2",
            framework_name="NIST CSF 2.0",
            linked_controls=[
                "GV.OC-01", "GV.RM-01", "ID.AM-01", "ID.RA-01", 
                "PR.AC-01", "PR.DS-01", "DE.CM-01", "RS.RP-01", "RC.RP-01"
            ],
            control_mapping={
                "GV.OC-01": {
                    "weight": 1.5,
                    "required_evidence_types": ["policy", "procedure"],
                    "minimum_evidence_count": 2,
                    "priority": "high"
                },
                "PR.AC-01": {
                    "weight": 2.0,
                    "required_evidence_types": ["policy", "procedure", "log"],
                    "minimum_evidence_count": 3,
                    "priority": "critical"
                }
            },
            template_type="standard",
            complexity_level="advanced",
            estimated_duration_hours=40,
            business_units=["IT", "Security", "Compliance", "Legal"],
            required_roles=["CISO", "IT Manager", "Compliance Officer"],
            evidence_requirements={
                "GV.OC-01": ["organizational_chart", "governance_policy", "board_resolutions"],
                "PR.AC-01": ["access_control_policy", "user_access_logs", "role_matrix", "privileged_access_procedures"]
            },
            mandatory_sections=["Governance", "Identity & Access Management", "Data Security", "Incident Response"],
            review_workflow={
                "levels": 2,
                "workflow_steps": [
                    {"step": 1, "role": "Compliance Manager", "required": True},
                    {"step": 2, "role": "CISO", "required": True}
                ],
                "auto_approval_threshold": 85.0,
                "escalation_timeout_hours": 48
            },
            approval_levels=2,
            question_templates=[
                {
                    "id": str(uuid.uuid4()),
                    "control_id": "PR.AC-01",
                    "question_type": "multiple_choice",
                    "question_text": "How comprehensive is your organization's access control implementation?",
                    "help_text": "Evaluate the scope and effectiveness of access controls across your organization's systems and data.",
                    "is_required": True,
                    "section": "Identity & Access Management",
                    "options": [
                        {"value": "comprehensive", "label": "Comprehensive - Fully implemented across all systems", "score": 4},
                        {"value": "substantial", "label": "Substantial - Implemented for most critical systems", "score": 3},
                        {"value": "basic", "label": "Basic - Limited implementation", "score": 2},
                        {"value": "minimal", "label": "Minimal - Very limited or no implementation", "score": 1}
                    ]
                },
                {
                    "id": str(uuid.uuid4()),
                    "control_id": "PR.AC-01",
                    "question_type": "file_upload",
                    "question_text": "Upload evidence of your access control policies and procedures.",
                    "help_text": "Provide documentation demonstrating your access control implementation.",
                    "is_required": True,
                    "section": "Identity & Access Management",
                    "allowed_file_types": ["pdf", "docx", "xlsx"],
                    "max_files": 5,
                    "max_file_size_mb": 10
                }
            ],
            scoring_configuration={
                "method": "weighted_average",
                "weights": {
                    "critical": 2.0,
                    "high": 1.5,
                    "medium": 1.0,
                    "low": 0.5
                },
                "thresholds": {
                    "excellent": 90,
                    "good": 75,
                    "satisfactory": 60,
                    "needs_improvement": 40
                },
                "normalization": "linear"
            },
            conditional_logic_rules=[
            {
                "rule_id": str(uuid.uuid4()),
                "condition": {
                    "if": {"==": [{"var": "PR.AC-01"}, "minimal"]},
                    "then": {"show": ["remediation_plan_upload", "implementation_timeline"]},
                    "else": {"show": ["evidence_upload"]}
                },
                "description": "Show remediation planning fields for minimal implementations"
            }
        ],
            usage_count=24,
            average_completion_time=38.5,
            success_rate=92.3,
            version="2.1",
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        return template
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment template: {str(e)}"
        )

@assessment_templates_router.post("/templates", response_model=AssessmentTemplate) 
async def create_assessment_template(
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new assessment template"""
    try:
        # Validate required fields
        required_fields = ["name", "framework_id", "framework_name"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create new template
        template = AssessmentTemplate(
            id=str(uuid.uuid4()),
            name=template_data["name"],
            description=template_data.get("description"),
            framework_id=template_data["framework_id"],
            framework_name=template_data["framework_name"],
            linked_controls=template_data.get("linked_controls", []),
            control_mapping=template_data.get("control_mapping", {}),
            template_type=template_data.get("template_type", "custom"),
            complexity_level=template_data.get("complexity_level", "intermediate"),
            estimated_duration_hours=template_data.get("estimated_duration_hours"),
            business_units=template_data.get("business_units", []),
            required_roles=template_data.get("required_roles", []),
            evidence_requirements=template_data.get("evidence_requirements", {}),
            mandatory_sections=template_data.get("mandatory_sections", []),
            review_workflow=template_data.get("review_workflow", {}),
            approval_levels=template_data.get("approval_levels", 1),
            question_templates=template_data.get("question_templates", []),
            scoring_configuration=template_data.get("scoring_configuration", {}),
            conditional_logic_rules=template_data.get("conditional_logic_rules", []),
            status="draft",
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        return template
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assessment template: {str(e)}"
        )

# =====================================
# ASSESSMENT CREATION FROM TEMPLATES
# =====================================

@assessment_templates_router.post("/templates/{template_id}/create-assessment", response_model=AssessmentEngine)
async def create_assessment_from_template(
    template_id: str,
    request: CreateAssessmentFromTemplateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new assessment from a template"""
    try:
        # Get the template (would retrieve from database)
        template = await get_assessment_template(template_id, current_user)
        
        # Create assessment from template
        assessment = AssessmentEngine(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description or template.description,
            framework_id=template.framework_id,
            framework_name=template.framework_name,
            configuration_id=str(uuid.uuid4()),  # Create default configuration
            assessment_type="template_based",
            status="draft",
            
            # Apply template configuration
            included_controls=request.selected_controls if request.customize_controls else template.linked_controls,
            business_units=template.business_units,
            
            # Team assignments from request
            owner_id=current_user.id,
            participants=request.team_assignments.get("participants", [current_user.id]),
            reviewers=request.team_assignments.get("reviewers", []),
            
            # Timeline
            due_date=request.due_date,
            
            # Initialize from template
            total_questions=len(template.question_templates),
            
            # Metadata
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Create control links based on template
        control_links = []
        controls_to_use = request.selected_controls if request.customize_controls else template.linked_controls
        
        for control_id in controls_to_use:
            control_config = template.control_mapping.get(control_id, {})
            
            control_link = AssessmentControlLink(
                id=str(uuid.uuid4()),
                assessment_id=assessment.id,
                control_id=control_id,
                framework_id=template.framework_id,
                is_required=True,
                weight=control_config.get("weight", 1.0),
                priority=control_config.get("priority", "medium"),
                required_evidence_types=control_config.get("required_evidence_types", []),
                minimum_evidence_count=control_config.get("minimum_evidence_count", 1),
                evidence_quality_threshold=control_config.get("evidence_quality_threshold", 70.0),
                organization_id=current_user.organization_id
            )
            control_links.append(control_link)
        
        # In real implementation, would save assessment and control links to database
        
        return assessment
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assessment from template: {str(e)}"
        )

# =====================================
# FRAMEWORK CONTROL INTEGRATION
# =====================================

@assessment_templates_router.get("/frameworks/{framework_id}/controls")
async def get_framework_controls_for_template(
    framework_id: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get framework controls for template configuration"""
    try:
        # Mock controls for template integration
        controls = [
            {
                "id": "PR.AC-01",
                "name": "Identity and Access Management",
                "description": "Identities and credentials are issued, managed, verified, revoked, and audited for authorized devices, users and processes",
                "category": "Identity & Access Management",
                "priority": "critical",
                "evidence_types": ["policy", "procedure", "log", "screenshot"],
                "typical_evidence_count": 3,
                "complexity_score": 8.5,
                "usage_frequency": 95.2
            },
            {
                "id": "PR.DS-01", 
                "name": "Data Security",
                "description": "Data-at-rest is protected",
                "category": "Data Protection",
                "priority": "high",
                "evidence_types": ["policy", "configuration", "audit_report"],
                "typical_evidence_count": 2,
                "complexity_score": 7.2,
                "usage_frequency": 87.4
            },
            {
                "id": "DE.CM-01",
                "name": "Continuous Monitoring",
                "description": "Networks and network services are monitored to find potentially adverse events",
                "category": "Detection & Monitoring", 
                "priority": "high",
                "evidence_types": ["log", "screenshot", "report"],
                "typical_evidence_count": 4,
                "complexity_score": 6.8,
                "usage_frequency": 78.9
            },
            {
                "id": "GV.OC-01",
                "name": "Organizational Context",
                "description": "Organizational cybersecurity strategy is established and communicated",
                "category": "Governance",
                "priority": "medium",
                "evidence_types": ["policy", "procedure", "presentation"],
                "typical_evidence_count": 2,
                "complexity_score": 5.5,
                "usage_frequency": 65.3
            }
        ]
        
        # Apply filters
        if category:
            controls = [c for c in controls if c["category"].lower() == category.lower()]
        if priority:
            controls = [c for c in controls if c["priority"] == priority]
        
        return {
            "framework_id": framework_id,
            "framework_name": "NIST CSF 2.0",
            "total_controls": len(controls),
            "controls": controls,
            "categories": list(set([c["category"] for c in controls])),
            "priority_distribution": {
                "critical": len([c for c in controls if c["priority"] == "critical"]),
                "high": len([c for c in controls if c["priority"] == "high"]),
                "medium": len([c for c in controls if c["priority"] == "medium"]),
                "low": len([c for c in controls if c["priority"] == "low"])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving framework controls: {str(e)}"
        )

@assessment_templates_router.post("/assessments/{assessment_id}/link-controls")
async def link_controls_to_assessment(
    assessment_id: str,
    request: AssessmentControlLinkRequest,
    current_user: User = Depends(get_current_user)
):
    """Link framework controls to an assessment"""
    try:
        created_links = []
        
        for link_config in request.control_links:
            control_link = AssessmentControlLink(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                control_id=link_config["control_id"],
                framework_id=link_config.get("framework_id", "nist-csf-v2"),
                is_required=link_config.get("is_required", True),
                weight=link_config.get("weight", 1.0),
                priority=link_config.get("priority", "medium"),
                required_evidence_types=link_config.get("required_evidence_types", []),
                minimum_evidence_count=link_config.get("minimum_evidence_count", 1),
                evidence_quality_threshold=link_config.get("evidence_quality_threshold", 70.0),
                organization_id=current_user.organization_id
            )
            created_links.append(control_link)
        
        return {
            "message": f"Successfully linked {len(created_links)} controls to assessment",
            "control_links": created_links,
            "assessment_id": assessment_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error linking controls to assessment: {str(e)}"
        )

@assessment_templates_router.get("/assessments/{assessment_id}/control-links", response_model=List[AssessmentControlLink])
async def get_assessment_control_links(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get control links for an assessment"""
    try:
        # Mock control links
        control_links = [
            AssessmentControlLink(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                control_id="PR.AC-01",
                framework_id="nist-csf-v2",
                is_required=True,
                weight=2.0,
                priority="critical",
                required_evidence_types=["policy", "procedure", "log"],
                minimum_evidence_count=3,
                evidence_quality_threshold=80.0,
                completion_status="in_progress",
                evidence_status="sufficient",
                review_status="under_review",
                control_score=78.5,
                evidence_count=3,
                organization_id=current_user.organization_id
            ),
            AssessmentControlLink(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                control_id="PR.DS-01",
                framework_id="nist-csf-v2",
                is_required=True,
                weight=1.5,
                priority="high",
                required_evidence_types=["policy", "configuration"],
                minimum_evidence_count=2,
                evidence_quality_threshold=75.0,
                completion_status="completed",
                evidence_status="sufficient",
                review_status="approved",
                control_score=85.2,
                evidence_count=2,
                review_feedback="Excellent data protection implementation with comprehensive policies",
                organization_id=current_user.organization_id
            )
        ]
        
        return control_links
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment control links: {str(e)}"
        )

# =====================================
# TEMPLATE ANALYTICS AND INSIGHTS
# =====================================

@assessment_templates_router.get("/templates/analytics/usage")
async def get_template_usage_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get analytics on template usage and performance"""
    try:
        analytics = {
            "total_templates": 15,
            "active_templates": 12,
            "most_used_templates": [
                {
                    "template_id": str(uuid.uuid4()),
                    "name": "NIST CSF 2.0 Comprehensive Assessment",
                    "usage_count": 24,
                    "success_rate": 92.3,
                    "average_completion_time": 38.5
                },
                {
                    "template_id": str(uuid.uuid4()),
                    "name": "ISO 27001:2022 Rapid Assessment", 
                    "usage_count": 15,
                    "success_rate": 87.5,
                    "average_completion_time": 18.2
                }
            ],
            "template_performance": {
                "average_success_rate": 89.1,
                "average_completion_time": 28.7,
                "user_satisfaction": 4.2
            },
            "framework_distribution": {
                "NIST CSF 2.0": 8,
                "ISO 27001:2022": 4, 
                "SOC 2": 2,
                "GDPR": 1
            },
            "complexity_distribution": {
                "basic": 3,
                "intermediate": 7,
                "advanced": 4,
                "expert": 1
            }
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving template analytics: {str(e)}"
        )

# =====================================
# HEALTH CHECK ENDPOINT
# =====================================

@assessment_templates_router.get("/health")
async def assessment_templates_health():
    """Health check endpoint for assessment templates system"""
    return {
        "status": "healthy",
        "module": "Assessment Templates System",
        "phase": "2B - Enhanced Evidence Collection & Workflow Management",
        "capabilities": [
            "Template Management & Creation",
            "Framework Control Integration",
            "Customizable Assessment Workflows",
            "Evidence Requirements Mapping",
            "Conditional Logic Configuration",
            "Template Performance Analytics",
            "Assessment Creation from Templates",
            "Control Linking & Management"
        ],
        "supported_template_types": [
            "standard", "custom", "regulatory", "industry_specific"
        ],
        "supported_complexity_levels": [
            "basic", "intermediate", "advanced", "expert"
        ],
        "integration_points": [
            "Phase 1 Control Mapping Engine",
            "Phase 2A Assessment Engine",
            "Evidence Management System",
            "Framework Management APIs"
        ],
        "timestamp": datetime.utcnow()
    }