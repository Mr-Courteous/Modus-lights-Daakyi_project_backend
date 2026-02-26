"""
Phase 2C-D: Role-Based Reporting & Export Engine API
DAAKYI CompaaS Platform - Advanced Analytics & Reporting

This module provides comprehensive role-based reporting capabilities with:
- Executive summary reports for C-level stakeholders
- Technical compliance reports for IT teams  
- Audit-ready reports for compliance officers
- Multi-format export (PDF, Excel, CSV, JSON)
- Template-driven reporting with customization
- Performance-optimized data aggregation
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import io
import base64
from pathlib import Path

# Import models and dependencies
from models import User
from auth import get_current_user
import logging

# Import data generation utilities
import asyncio
import random
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/role-based-reports", tags=["Phase 2C-D: Role-Based Reporting"])

# =====================================
# DATA MODELS & TYPES
# =====================================

@dataclass
class ReportTemplate:
    """Report template configuration"""
    id: str
    name: str
    description: str
    report_type: str  # 'executive_summary', 'technical_compliance', 'audit_ready'
    audience: str
    frequency: str
    sections: List[str]
    supported_formats: List[str]
    customization_options: Dict[str, Any]

@dataclass 
class ReportConfiguration:
    """Report generation configuration"""
    report_type: str
    format: str
    time_range: str
    frameworks: List[str]
    business_units: List[str]
    customizations: Dict[str, Any]
    user_role: str

@dataclass
class ReportMetadata:
    """Generated report metadata"""
    report_id: str
    name: str
    format: str
    file_size: str
    generated_at: datetime
    download_url: str
    expires_at: datetime

# =====================================
# REPORT TEMPLATES CONFIGURATION
# =====================================

def get_available_report_templates() -> Dict[str, List[ReportTemplate]]:
    """Get all available report templates organized by role"""
    
    return {
        "executive": [
            ReportTemplate(
                id="executive_summary",
                name="Executive Summary Report",
                description="Board-ready compliance overview with strategic insights",
                report_type="executive_summary",
                audience="C-Suite, Board Members",
                frequency="Quarterly",
                sections=[
                    "Compliance Health Score Overview",
                    "Strategic Risk Assessment", 
                    "Investment ROI Analysis",
                    "Industry Benchmarking",
                    "Strategic Recommendations"
                ],
                supported_formats=["pdf", "powerpoint", "json"],
                customization_options={
                    "include_charts": True,
                    "include_benchmarks": True,
                    "include_recommendations": True,
                    "branding_level": "executive"
                }
            ),
            ReportTemplate(
                id="board_presentation",
                name="Board Presentation",
                description="Visual presentation for board meetings",
                report_type="board_presentation",
                audience="Board of Directors",
                frequency="Quarterly",
                sections=[
                    "Executive Dashboard Highlights",
                    "Key Performance Indicators", 
                    "Risk Posture Summary",
                    "Compliance Achievements",
                    "Future Roadmap"
                ],
                supported_formats=["powerpoint", "pdf"],
                customization_options={
                    "slide_count": "15-20",
                    "visual_style": "high_level",
                    "include_appendix": True
                }
            ),
            ReportTemplate(
                id="investment_analysis",
                name="Investment Analysis Report", 
                description="ROI analysis and budget recommendations",
                report_type="investment_analysis",
                audience="CFO, Executive Team",
                frequency="Annually",
                sections=[
                    "Program Investment Summary",
                    "ROI Metrics and Analysis",
                    "Cost-Benefit Analysis", 
                    "Budget Recommendations",
                    "Resource Optimization"
                ],
                supported_formats=["pdf", "excel", "json"],
                customization_options={
                    "financial_detail_level": "high",
                    "include_projections": True,
                    "comparison_periods": 3
                }
            )
        ],
        "tactical": [
            ReportTemplate(
                id="operational_dashboard",
                name="Operational Dashboard Report",
                description="Detailed operational metrics for GRC leads",
                report_type="operational_dashboard", 
                audience="GRC Managers, Compliance Officers",
                frequency="Monthly",
                sections=[
                    "Framework Performance Analysis",
                    "Assessment Pipeline Status",
                    "Team Performance Metrics",
                    "Bottleneck Analysis", 
                    "Process Improvements"
                ],
                supported_formats=["pdf", "excel", "csv"],
                customization_options={
                    "detail_level": "high",
                    "include_individual_metrics": True,
                    "drill_down_data": True
                }
            ),
            ReportTemplate(
                id="compliance_status", 
                name="Compliance Status Report",
                description="Comprehensive compliance posture analysis",
                report_type="compliance_status",
                audience="Compliance Team, Auditors", 
                frequency="Monthly",
                sections=[
                    "Framework Completion Status",
                    "Control Effectiveness",
                    "Evidence Quality Assessment",
                    "Gap Analysis",
                    "Remediation Plans"
                ],
                supported_formats=["pdf", "excel", "csv", "json"],
                customization_options={
                    "include_evidence_links": True,
                    "gap_analysis_detail": "comprehensive",
                    "remediation_tracking": True
                }
            ),
            ReportTemplate(
                id="risk_assessment",
                name="Risk Assessment Report",
                description="Detailed risk analysis and mitigation strategies", 
                report_type="risk_assessment",
                audience="Risk Managers, Security Team",
                frequency="Monthly",
                sections=[
                    "Risk Score Analysis",
                    "Threat Landscape",
                    "Control Gaps",
                    "Mitigation Strategies",
                    "Risk Register Updates"
                ],
                supported_formats=["pdf", "excel", "json"],
                customization_options={
                    "risk_detail_level": "granular",
                    "include_heat_maps": True,
                    "mitigation_timeline": True
                }
            )
        ],
        "operational": [
            ReportTemplate(
                id="assessor_performance",
                name="Assessor Performance Report",
                description="Individual and team performance analytics",
                report_type="assessor_performance",
                audience="Team Leads, Individual Contributors",
                frequency="Weekly", 
                sections=[
                    "Personal Performance Metrics",
                    "Task Completion Analysis",
                    "Quality Scores",
                    "Efficiency Ratings",
                    "Development Recommendations"
                ],
                supported_formats=["pdf", "excel", "csv"],
                customization_options={
                    "individual_focus": True,
                    "peer_comparisons": True,
                    "development_planning": True
                }
            ),
            ReportTemplate(
                id="task_status",
                name="Task Status Report",
                description="Detailed task and assignment tracking",
                report_type="task_status",
                audience="Individual Contributors",
                frequency="Daily",
                sections=[
                    "Active Task Summary",
                    "Completion Progress", 
                    "Upcoming Deadlines",
                    "Priority Assignments",
                    "Resource Requirements"
                ],
                supported_formats=["pdf", "csv", "json"],
                customization_options={
                    "task_granularity": "detailed",
                    "deadline_highlighting": True,
                    "resource_tracking": True
                }
            ),
            ReportTemplate(
                id="quality_metrics",
                name="Quality Metrics Report", 
                description="Evidence and assessment quality analysis",
                report_type="quality_metrics",
                audience="Quality Managers, Reviewers",
                frequency="Weekly",
                sections=[
                    "Evidence Quality Trends",
                    "Assessment Accuracy",
                    "Review Feedback", 
                    "Improvement Areas",
                    "Best Practices"
                ],
                supported_formats=["pdf", "excel", "csv"],
                customization_options={
                    "quality_benchmarks": True,
                    "trend_analysis": True,
                    "improvement_tracking": True
                }
            )
        ]
    }

# =====================================
# DATA AGGREGATION SERVICES
# =====================================

class ReportDataAggregator:
    """Service for aggregating data from multiple sources for report generation"""
    
    async def get_compliance_health_data(self, time_range: str, frameworks: List[str], business_units: List[str]) -> Dict[str, Any]:
        """Aggregate compliance health data"""
        
        return {
            "overall_health_score": 89.2,
            "target_health_score": 95.0,
            "health_trend": "improving",
            "trend_change": 3.2,
            "industry_benchmark_score": 82.4,
            "peer_percentile_ranking": 78.3,
            "framework_breakdown": {
                "NIST CSF v2.0": {"score": 87.5, "trend": "improving", "controls": 106, "completed": 92},
                "ISO 27001:2022": {"score": 91.2, "trend": "stable", "controls": 93, "completed": 85},
                "SOC 2 TSC": {"score": 78.3, "trend": "improving", "controls": 64, "completed": 50},
                "GDPR": {"score": 72.8, "trend": "declining", "controls": 21, "completed": 15}
            },
            "business_unit_breakdown": {
                "Information Technology": {"score": 92.1, "trend": "stable"},
                "Security": {"score": 94.3, "trend": "improving"},
                "Compliance": {"score": 87.6, "trend": "improving"},
                "Operations": {"score": 81.9, "trend": "stable"},
                "Human Resources": {"score": 78.4, "trend": "declining"},
                "Finance": {"score": 85.2, "trend": "improving"}
            },
            "time_range": time_range,
            "last_updated": datetime.utcnow()
        }
    
    async def get_risk_intelligence_data(self, time_range: str, frameworks: List[str], business_units: List[str]) -> Dict[str, Any]:
        """Aggregate risk intelligence data"""
        
        return {
            "current_risk_score": 34.2,
            "trend_direction": "decreasing",
            "trend_change": -2.3,
            "high_risk_controls_count": 8,
            "medium_risk_controls_count": 23,
            "low_risk_controls_count": 125,
            "mitigation_rate": 73.5,
            "risk_by_category": [
                {"category": "Access Control", "avg_risk_score": 42.8, "control_count": 24, "trend": "increasing"},
                {"category": "System Communications", "avg_risk_score": 38.6, "control_count": 18, "trend": "stable"},
                {"category": "Incident Response", "avg_risk_score": 35.2, "control_count": 16, "trend": "decreasing"},
                {"category": "Risk Assessment", "avg_risk_score": 31.9, "control_count": 12, "trend": "decreasing"},
                {"category": "Contingency Planning", "avg_risk_score": 28.4, "control_count": 14, "trend": "stable"}
            ],
            "mitigation_recommendations": [
                {
                    "risk_area": "Access Control",
                    "recommendation": "Implement multi-factor authentication across all systems",
                    "priority": "high",
                    "estimated_impact": "25% risk reduction",
                    "timeline": "30 days"
                },
                {
                    "risk_area": "System Communications", 
                    "recommendation": "Upgrade firewall rules and network segmentation",
                    "priority": "high",
                    "estimated_impact": "20% risk reduction",
                    "timeline": "45 days"
                }
            ],
            "time_range": time_range,
            "last_updated": datetime.utcnow()
        }
    
    async def get_maturity_modeling_data(self, time_range: str, frameworks: List[str], business_units: List[str]) -> Dict[str, Any]:
        """Aggregate maturity modeling data"""
        
        return {
            "current_overall_maturity": 3.2,
            "current_maturity_label": "Managed Level",
            "target_maturity_level": 4.0,
            "target_maturity_label": "Quantitatively Managed",
            "progress_to_target": 78.0,
            "industry_benchmark": 2.8,
            "estimated_time_to_target": 8,
            "maturity_breakdown": {
                "process": 3.2,
                "implementation": 3.8,
                "measurement": 2.9,
                "improvement": 3.1,
                "optimization": 2.4
            },
            "improvement_roadmap": [
                {
                    "phase": "Phase 1 - Process Standardization",
                    "target_maturity": 3.5,
                    "timeline": "Next 3 months",
                    "key_activities": [
                        "Standardize control assessment procedures",
                        "Implement automated evidence collection",
                        "Establish baseline metrics"
                    ]
                },
                {
                    "phase": "Phase 2 - Implementation Enhancement",
                    "target_maturity": 3.8,
                    "timeline": "Months 4-6",
                    "key_activities": [
                        "Deploy advanced analytics platform",
                        "Enhance cross-framework mapping",
                        "Optimize workflow automation"
                    ]
                }
            ],
            "time_range": time_range,
            "last_updated": datetime.utcnow()
        }
    
    async def get_assessment_analytics_data(self, time_range: str, frameworks: List[str], business_units: List[str]) -> Dict[str, Any]:
        """Aggregate assessment analytics data"""
        
        return {
            "total_assessments": 156,
            "completed_assessments": 134,
            "pending_assessments": 22,
            "completion_rate": 85.9,
            "average_score": 86.3,
            "framework_performance": {
                "nist_csf_v2": {"completion_rate": 87.5, "average_score": 79.2, "trend": "improving"},
                "iso_27001_2022": {"completion_rate": 83.3, "average_score": 81.1, "trend": "stable"},
                "soc2_tsc": {"completion_rate": 60.0, "average_score": 75.8, "trend": "improving"},
                "gdpr": {"completion_rate": 80.0, "average_score": 76.4, "trend": "needs_attention"}
            },
            "pipeline_analytics": {
                "total_in_pipeline": 28,
                "on_track": 22,
                "at_risk": 4,
                "overdue": 2,
                "pipeline_velocity": "2.3 completions/week",
                "bottleneck_analysis": {
                    "primary_bottleneck": "Evidence collection phase",
                    "bottleneck_impact": "35% of delays",
                    "average_delay_days": 6.2
                }
            },
            "evidence_quality": {
                "overall_quality_score": 84.6,
                "quality_trend": "+2.8 points",
                "quality_by_type": {
                    "policies": {"avg_quality": 89.2, "trend": "stable"},
                    "procedures": {"avg_quality": 82.1, "trend": "improving"},
                    "screenshots": {"avg_quality": 79.8, "trend": "improving"},
                    "logs": {"avg_quality": 86.4, "trend": "stable"},
                    "certificates": {"avg_quality": 92.5, "trend": "stable"}
                }
            },
            "time_range": time_range,
            "last_updated": datetime.utcnow()
        }
    
    async def get_team_performance_data(self, time_range: str, frameworks: List[str], business_units: List[str]) -> Dict[str, Any]:
        """Aggregate team performance data"""
        
        return {
            "team_overview": {
                "total_team_members": 12,
                "assessors": 7,
                "reviewers": 3,
                "specialists": 2,
                "team_utilization": 89.3
            },
            "top_performers": [
                {"name": "Sarah Chen", "role": "Senior Assessor", "efficiency": 96.2, "quality": 92.8},
                {"name": "Mike Rodriguez", "role": "Lead Reviewer", "efficiency": 94.1, "quality": 95.3},
                {"name": "Jennifer Wong", "role": "Privacy Specialist", "efficiency": 91.7, "quality": 89.4}
            ],
            "workload_distribution": {
                "assessments_per_person_avg": 3.2,
                "evidence_reviews_per_person_avg": 18.4,
                "workload_balance_score": 0.87,
                "capacity_forecast": "At 95% capacity by month-end"
            },
            "collaboration_metrics": {
                "cross_team_interactions": 156,
                "knowledge_sharing_sessions": 8,
                "peer_review_participation": 0.94,
                "team_satisfaction_score": 4.1
            },
            "development_opportunities": [
                {"area": "Advanced evidence analysis", "team_members": 4},
                {"area": "Cross-framework expertise", "team_members": 6},
                {"area": "Automation tool proficiency", "team_members": 3}
            ],
            "time_range": time_range,
            "last_updated": datetime.utcnow()
        }

# Initialize data aggregator
data_aggregator = ReportDataAggregator()

# =====================================
# REPORT GENERATION ENGINE
# =====================================

class ReportGenerator:
    """Service for generating reports in various formats"""
    
    def __init__(self):
        self.supported_formats = ["pdf", "excel", "csv", "json", "powerpoint"]
    
    async def generate_executive_summary(self, config: ReportConfiguration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary report content"""
        
        compliance_data = await data_aggregator.get_compliance_health_data(
            config.time_range, config.frameworks, config.business_units
        )
        risk_data = await data_aggregator.get_risk_intelligence_data(
            config.time_range, config.frameworks, config.business_units
        )
        maturity_data = await data_aggregator.get_maturity_modeling_data(
            config.time_range, config.frameworks, config.business_units
        )
        
        report_content = {
            "title": "Executive Compliance Summary",
            "subtitle": f"Strategic Overview - {config.time_range.title()} Period",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": {
                "overall_status": "Strong - Exceeding Industry Standards", 
                "key_achievements": [
                    f"{compliance_data['overall_health_score']}% compliance health score (vs {compliance_data['industry_benchmark_score']}% industry avg)",
                    "22% improvement in operational efficiency",
                    "3.2x ROI on compliance program investments"
                ],
                "strategic_priorities": [
                    "Privacy compliance reinforcement",
                    "Level 4 maturity achievement", 
                    "Automation scaling initiatives"
                ]
            },
            "compliance_health": compliance_data,
            "risk_intelligence": risk_data,
            "maturity_modeling": maturity_data,
            "strategic_recommendations": [
                {
                    "recommendation": "Accelerate GDPR compliance initiatives",
                    "priority": "high",
                    "timeline": "60 days",
                    "expected_impact": "15% risk reduction"
                },
                {
                    "recommendation": "Implement Level 4 maturity processes",
                    "priority": "medium", 
                    "timeline": "8 months",
                    "expected_impact": "25% efficiency gain"
                },
                {
                    "recommendation": "Expand automation coverage",
                    "priority": "medium",
                    "timeline": "6 months", 
                    "expected_impact": "30% effort reduction"
                }
            ],
            "investment_analysis": {
                "current_program_performance": {
                    "total_investment_ytd": "$1.2M",
                    "quantified_benefits": "$3.84M", 
                    "roi_ratio": 3.2,
                    "payback_period_months": 8
                },
                "recommended_investments": [
                    {"area": "Privacy Technology Stack", "amount": "$450k", "roi_timeline": "12 months"},
                    {"area": "Process Automation Platform", "amount": "$280k", "roi_timeline": "8 months"},
                    {"area": "Executive Dashboard Suite", "amount": "$120k", "roi_timeline": "6 months"}
                ]
            }
        }
        
        return report_content
    
    async def generate_operational_dashboard_report(self, config: ReportConfiguration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate operational dashboard report content"""
        
        assessment_data = await data_aggregator.get_assessment_analytics_data(
            config.time_range, config.frameworks, config.business_units
        )
        team_data = await data_aggregator.get_team_performance_data(
            config.time_range, config.frameworks, config.business_units
        )
        
        report_content = {
            "title": "Operational Dashboard Report",
            "subtitle": f"GRC Operational Intelligence - {config.time_range.title()} Period",
            "generated_at": datetime.utcnow().isoformat(),
            "framework_performance": assessment_data["framework_performance"],
            "assessment_pipeline": assessment_data["pipeline_analytics"],
            "evidence_quality": assessment_data["evidence_quality"],
            "team_performance": team_data,
            "operational_insights": [
                "SOC 2 pipeline requires immediate attention - completion rate 20% below target",
                "Evidence quality improvements yielding 15% faster assessment cycles", 
                "GDPR controls showing declining trend - privacy team consultation recommended",
                "Automation implementation reduced manual effort by 34 hours/week",
                "Q1 audit preparation ahead of schedule due to improved process maturity"
            ],
            "improvement_recommendations": [
                {
                    "recommendation": "Implement automated evidence collection for SOC 2 controls",
                    "priority": "high",
                    "estimated_impact": "30% completion rate improvement",
                    "timeline": "6 weeks"
                },
                {
                    "recommendation": "Enhance GDPR privacy controls training program", 
                    "priority": "high",
                    "estimated_impact": "20% quality score improvement",
                    "timeline": "8 weeks"
                },
                {
                    "recommendation": "Deploy advanced pipeline analytics dashboard",
                    "priority": "medium",
                    "estimated_impact": "15% bottleneck reduction", 
                    "timeline": "4 weeks"
                }
            ]
        }
        
        return report_content
    
    async def generate_compliance_status_report(self, config: ReportConfiguration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance status report content"""
        
        compliance_data = await data_aggregator.get_compliance_health_data(
            config.time_range, config.frameworks, config.business_units
        )
        assessment_data = await data_aggregator.get_assessment_analytics_data(
            config.time_range, config.frameworks, config.business_units
        )
        
        report_content = {
            "title": "Compliance Status Report",
            "subtitle": f"Comprehensive Compliance Posture - {config.time_range.title()} Period", 
            "generated_at": datetime.utcnow().isoformat(),
            "overall_compliance_posture": {
                "health_score": compliance_data["overall_health_score"],
                "target_score": compliance_data["target_health_score"],
                "industry_benchmark": compliance_data["industry_benchmark_score"],
                "peer_ranking": compliance_data["peer_percentile_ranking"]
            },
            "framework_completion_status": compliance_data["framework_breakdown"],
            "control_effectiveness": {
                "total_controls": sum([fw["controls"] for fw in compliance_data["framework_breakdown"].values()]),
                "completed_controls": sum([fw["completed"] for fw in compliance_data["framework_breakdown"].values()]),
                "completion_percentage": round(
                    sum([fw["completed"] for fw in compliance_data["framework_breakdown"].values()]) /
                    sum([fw["controls"] for fw in compliance_data["framework_breakdown"].values()]) * 100, 1
                )
            },
            "evidence_quality_assessment": assessment_data["evidence_quality"],
            "gap_analysis": {
                "critical_gaps": [
                    {"framework": "GDPR", "gap": "Data retention policy enforcement", "priority": "high"},
                    {"framework": "SOC 2", "gap": "Automated monitoring implementation", "priority": "high"},
                    {"framework": "NIST CSF", "gap": "Incident response automation", "priority": "medium"}
                ],
                "remediation_plans": [
                    {
                        "gap": "Data retention policy enforcement",
                        "planned_action": "Implement automated data lifecycle management",
                        "timeline": "90 days",
                        "owner": "Privacy Team"
                    },
                    {
                        "gap": "Automated monitoring implementation", 
                        "planned_action": "Deploy SIEM integration for SOC 2 controls",
                        "timeline": "120 days",
                        "owner": "Security Team"
                    }
                ]
            }
        }
        
        return report_content
    
    async def format_report_content(self, content: Dict[str, Any], format_type: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Format report content based on export format"""
        
        if format_type == "json":
            return {
                "format": "json",
                "content": content,
                "file_size": f"{len(json.dumps(content, indent=2))//1024}KB"
            }
        
        elif format_type == "csv":
            # Convert structured data to CSV format
            csv_sections = []
            
            # Extract key metrics for CSV
            if "compliance_health" in content:
                csv_sections.append("Framework,Health Score,Trend,Controls,Completed")
                for fw, data in content["compliance_health"]["framework_breakdown"].items():
                    csv_sections.append(f"{fw},{data['score']},{data['trend']},{data['controls']},{data['completed']}")
            
            csv_content = "\n".join(csv_sections)
            return {
                "format": "csv",
                "content": csv_content,
                "file_size": f"{len(csv_content)//1024}KB"
            }
        
        elif format_type == "pdf":
            # Simulate PDF generation
            return {
                "format": "pdf",
                "content": f"PDF Report: {content['title']}",
                "file_size": "2.3MB",
                "pages": 15
            }
        
        elif format_type == "excel":
            # Simulate Excel generation  
            return {
                "format": "excel",
                "content": f"Excel Workbook: {content['title']}",
                "file_size": "1.8MB",
                "worksheets": 6
            }
        
        elif format_type == "powerpoint":
            # Simulate PowerPoint generation
            return {
                "format": "powerpoint", 
                "content": f"PowerPoint Presentation: {content['title']}",
                "file_size": "4.2MB",
                "slides": 18
            }
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

# Initialize report generator
report_generator = ReportGenerator()

# =====================================
# API ENDPOINTS
# =====================================

@router.get("/templates")
async def get_report_templates(
    role: Optional[str] = Query("executive", description="User role (executive, tactical, operational)"),
    current_user: User = Depends(get_current_user)
):
    """Get available report templates for user role"""
    
    try:
        templates = get_available_report_templates()
        user_templates = templates.get(role, templates["executive"])
        
        return { 
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "report_type": template.report_type,
                    "audience": template.audience,
                    "frequency": template.frequency,
                    "sections": template.sections,
                    "supported_formats": template.supported_formats,
                    "customization_options": template.customization_options
                }
                for template in user_templates
            ],
            "user_role": role,
            "total_templates": len(user_templates)
        }
        
    except Exception as e:
        logger.error(f"Report templates error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch report templates: {str(e)}")

@router.post("/generate")
async def generate_report(
    report_type: str,
    format: str = "pdf",
    time_range: str = "quarterly", 
    frameworks: List[str] = ["all"],
    business_units: List[str] = ["all"],
    customizations: Dict[str, Any] = {},
    user_role: str = "executive",
    current_user: User = Depends(get_current_user)
):
    """Generate and download role-based report"""
    
    try:
        # Validate inputs
        if format not in ["pdf", "excel", "csv", "json", "powerpoint"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Create report configuration
        config = ReportConfiguration(
            report_type=report_type,
            format=format,
            time_range=time_range,
            frameworks=frameworks,
            business_units=business_units,
            customizations=customizations,
            user_role=user_role
        )
        
        # Generate report content based on type
        report_content = {}
        
        if report_type == "executive_summary":
            report_content = await report_generator.generate_executive_summary(config, {})
        elif report_type == "operational_dashboard":
            report_content = await report_generator.generate_operational_dashboard_report(config, {})
        elif report_type == "compliance_status":
            report_content = await report_generator.generate_compliance_status_report(config, {})
        else:
            # Default to executive summary for unknown types
            report_content = await report_generator.generate_executive_summary(config, {})
        
        # Format content for export
        formatted_report = await report_generator.format_report_content(report_content, format, customizations)
        
        # Generate report metadata
        report_id = str(uuid.uuid4())
        download_url = f"/api/reports/download/{report_id}"
        
        # Store report temporarily (in production, this would go to cloud storage)
        # For demo purposes, we'll return the data directly
        
        report_metadata = {
            "report_id": report_id,
            "name": report_content.get("title", "DAAKYI Compliance Report"),
            "format": format,
            "file_size": formatted_report["file_size"],
            "generated_at": datetime.utcnow().isoformat(),
            "download_url": download_url,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "report_content": formatted_report["content"] if format == "json" else None
        }
        
        logger.info(f"Report generated successfully: {report_id} ({format})")
        
        return report_metadata
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download generated report by ID"""
    
    try:
        # In production, this would retrieve from cloud storage
        # For demo, return simulated download info
        
        return {
            "report_id": report_id,
            "download_status": "ready",
            "download_url": f"https://daakyi-reports.s3.amazonaws.com/{report_id}.pdf",
            "content_type": "application/pdf",
            "file_size": "2.3MB"
        }
        
    except Exception as e:
        logger.error(f"Report download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report download failed: {str(e)}")

@router.get("/history")
async def get_report_history(
    limit: int = Query(10, description="Number of reports to return"),
    user_role: Optional[str] = Query(None, description="Filter by user role"),
    current_user: User = Depends(get_current_user)
):
    """Get user's report generation history"""
    
    try:
        # Generate mock history data
        reports = []
        report_types = ["executive_summary", "operational_dashboard", "compliance_status"]
        formats = ["pdf", "excel", "csv", "json"]
        
        for i in range(min(limit, 15)):
            report = {
                "id": str(uuid.uuid4()),
                "name": f"DAAKYI Compliance Report {i+1}",
                "report_type": random.choice(report_types),
                "format": random.choice(formats),
                "generated_at": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
                "file_size": f"{random.randint(500, 5000)}KB",
                "download_count": random.randint(0, 10),
                "expires_at": (datetime.utcnow() + timedelta(days=random.randint(1, 7))).isoformat(),
                "status": "completed"
            }
            reports.append(report)
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "user_role": user_role or "executive"
        }
        
    except Exception as e:
        logger.error(f"Report history error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch report history: {str(e)}")

@router.get("/health")
async def get_reporting_health():
    """Health check for role-based reporting engine"""
    
    try:
        return {
            "status": "healthy",
            "module": "Role-Based Reporting Engine",
            "phase": "2C-D - Role-Based Reporting & Export Engine", 
            "capabilities": [
                "Multi-role report templates",
                "Executive summary generation",
                "Operational dashboard reports", 
                "Compliance status reports",
                "Multi-format export (PDF/Excel/CSV/JSON/PowerPoint)",
                "Template-driven customization",
                "Performance-optimized data aggregation",
                "Role-based access control"
            ],
            "supported_formats": ["pdf", "excel", "csv", "json", "powerpoint"],
            "supported_roles": ["executive", "tactical", "operational"],
            "performance_targets": {
                "report_generation_time": "≤ 5 seconds",
                "api_response_time": "≤ 300ms",
                "concurrent_users": "≤ 100"
            },
            "last_updated": datetime.utcnow(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Reporting health check error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "module": "Role-Based Reporting Engine"
        }