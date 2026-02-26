"""
Admin Analytics API
Backend API endpoints for comprehensive admin analytics and system-wide insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from database import get_database
from mvp1_auth import get_current_user

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/analytics/admin", tags=["admin-analytics"])

# Pydantic models for request/response
class SystemOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    total_assessments: int
    completed_assessments: int
    system_uptime: float
    data_processed_gb: float
    avg_compliance_score: float
    total_risks: int
    total_budget: int
    platform_health: float

class UserActivityByRoleResponse(BaseModel):
    role: str
    total_users: int
    active_today: int
    avg_session_time: int  # minutes
    tasks_completed: int
    engagement_rate: float

class FrameworkAdoptionResponse(BaseModel):
    framework: str
    adoption_rate: int
    total_organizations: int
    active_assessments: int
    completion_rate: int
    avg_score: int
    trend: str

class DepartmentPerformanceResponse(BaseModel):
    department: str
    users: int
    compliance: int
    assessments: int
    risks: int
    budget: int
    efficiency: int

class SecurityMetricResponse(BaseModel):
    name: str
    value: Any
    status: str
    trend: Optional[str] = None

class SystemGrowthDataResponse(BaseModel):
    period: str
    total_users: int
    active_users: int
    completed_assessments: int
    system_uptime: float
    data_processed: float

class ReportStatisticsResponse(BaseModel):
    date: str
    total_reports: int
    pdf_reports: int
    excel_reports: int
    powerpoint_reports: int
    custom_reports: int

@router.get("/system-overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    date_range_days: Optional[int] = Query(30, description="Number of days to include in analysis"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get comprehensive system overview metrics for admin dashboard"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)

        # In a real implementation, these would be database queries
        # For now, providing realistic mock data
        system_overview = SystemOverviewResponse(
            total_users=203,
            active_users=142,
            total_assessments=89,
            completed_assessments=58,
            system_uptime=99.8,
            data_processed_gb=4.5,
            avg_compliance_score=91,
            total_risks=23,
            total_budget=1845000,
            platform_health=98.7
        )

        return system_overview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching system overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch system overview")

@router.get("/user-activity", response_model=List[UserActivityByRoleResponse])
async def get_user_activity_by_role(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get user activity breakdown by role"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock data for user activity by role
        user_activity = [
            UserActivityByRoleResponse(
                role="Admin",
                total_users=8,
                active_today=6,
                avg_session_time=45,
                tasks_completed=124,
                engagement_rate=75.0
            ),
            UserActivityByRoleResponse(
                role="Analyst", 
                total_users=47,
                active_today=32,
                avg_session_time=38,
                tasks_completed=892,
                engagement_rate=68.1
            ),
            UserActivityByRoleResponse(
                role="Auditor",
                total_users=23,
                active_today=18,
                avg_session_time=42,
                tasks_completed=456,
                engagement_rate=78.3
            ),
            UserActivityByRoleResponse(
                role="Leadership",
                total_users=15,
                active_today=9,
                avg_session_time=22,
                tasks_completed=78,
                engagement_rate=60.0
            ),
            UserActivityByRoleResponse(
                role="Manager",
                total_users=32,
                active_today=24,
                avg_session_time=35,
                tasks_completed=234,
                engagement_rate=75.0
            )
        ]

        return user_activity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user activity")

@router.get("/framework-adoption", response_model=List[FrameworkAdoptionResponse])
async def get_framework_adoption(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get framework adoption rates across organization"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock framework adoption data
        framework_adoption = [
            FrameworkAdoptionResponse(
                framework="ISO 27001",
                adoption_rate=92,
                total_organizations=25,
                active_assessments=18,
                completion_rate=87,
                avg_score=89,
                trend="up"
            ),
            FrameworkAdoptionResponse(
                framework="SOC 2 Type II",
                adoption_rate=84,
                total_organizations=21,
                active_assessments=15,
                completion_rate=79,
                avg_score=85,
                trend="up"
            ),
            FrameworkAdoptionResponse(
                framework="NIST CSF",
                adoption_rate=88,
                total_organizations=22,
                active_assessments=16,
                completion_rate=82,
                avg_score=91,
                trend="stable"
            ),
            FrameworkAdoptionResponse(
                framework="GDPR",
                adoption_rate=76,
                total_organizations=19,
                active_assessments=12,
                completion_rate=71,
                avg_score=78,
                trend="up"
            ),
            FrameworkAdoptionResponse(
                framework="PCI DSS",
                adoption_rate=69,
                total_organizations=17,
                active_assessments=10,
                completion_rate=65,
                avg_score=82,
                trend="down"
            ),
            FrameworkAdoptionResponse(
                framework="HIPAA",
                adoption_rate=58,
                total_organizations=14,
                active_assessments=8,
                completion_rate=58,
                avg_score=76,
                trend="stable"
            )
        ]

        return framework_adoption

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching framework adoption: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch framework adoption")

@router.get("/department-performance", response_model=List[DepartmentPerformanceResponse])
async def get_department_performance(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get performance metrics by department"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock department performance data
        department_performance = [
            DepartmentPerformanceResponse(
                department="Information Technology",
                users=45,
                compliance=94,
                assessments=28,
                risks=3,
                budget=485000,
                efficiency=89
            ),
            DepartmentPerformanceResponse(
                department="Security Operations",
                users=23,
                compliance=97,
                assessments=35,
                risks=2,
                budget=320000,
                efficiency=93
            ),
            DepartmentPerformanceResponse(
                department="Data Management",
                users=32,
                compliance=89,
                assessments=19,
                risks=6,
                budget=275000,
                efficiency=85
            ),
            DepartmentPerformanceResponse(
                department="Finance & Accounting",
                users=28,
                compliance=92,
                assessments=22,
                risks=4,
                budget=195000,
                efficiency=91
            ),
            DepartmentPerformanceResponse(
                department="Human Resources",
                users=19,
                compliance=86,
                assessments=15,
                risks=7,
                budget=125000,
                efficiency=82
            ),
            DepartmentPerformanceResponse(
                department="Legal & Compliance",
                users=12,
                compliance=98,
                assessments=31,
                risks=1,
                budget=410000,
                efficiency=96
            )
        ]

        return department_performance

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching department performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch department performance")

@router.get("/security-metrics", response_model=List[SecurityMetricResponse])
async def get_security_metrics(
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get security and AI performance metrics"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock security metrics
        security_metrics = [
            SecurityMetricResponse(
                name="Failed Login Attempts",
                value=23,
                status="warning",
                trend="down"
            ),
            SecurityMetricResponse(
                name="Security Incidents",
                value=2,
                status="success",
                trend="stable"
            ),
            SecurityMetricResponse(
                name="AI Analysis Accuracy",
                value=94,
                status="success",
                trend="up"
            ),
            SecurityMetricResponse(
                name="Data Breaches",
                value=0,
                status="success",
                trend="stable"
            ),
            SecurityMetricResponse(
                name="Policy Violations",
                value=5,
                status="warning",
                trend="down"
            ),
            SecurityMetricResponse(
                name="System Vulnerabilities",
                value=8,
                status="error",
                trend="up"
            )
        ]

        return security_metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching security metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch security metrics")

@router.get("/system-growth", response_model=List[SystemGrowthDataResponse])
async def get_system_growth_data(
    months: Optional[int] = Query(6, description="Number of months to include"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get system growth metrics over time"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock system growth data
        system_growth = [
            SystemGrowthDataResponse(period="Jan 2024", total_users=145, active_users=89, completed_assessments=23, system_uptime=99.8, data_processed=2.4),
            SystemGrowthDataResponse(period="Feb 2024", total_users=152, active_users=94, completed_assessments=28, system_uptime=99.9, data_processed=2.8),
            SystemGrowthDataResponse(period="Mar 2024", total_users=168, active_users=103, completed_assessments=35, system_uptime=99.7, data_processed=3.2),
            SystemGrowthDataResponse(period="Apr 2024", total_users=175, active_users=112, completed_assessments=42, system_uptime=99.8, data_processed=3.6),
            SystemGrowthDataResponse(period="May 2024", total_users=189, active_users=127, completed_assessments=51, system_uptime=99.9, data_processed=4.1),
            SystemGrowthDataResponse(period="Jun 2024", total_users=203, active_users=142, completed_assessments=58, system_uptime=99.8, data_processed=4.5)
        ]

        return system_growth[-months:] if months < len(system_growth) else system_growth

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching system growth data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch system growth data")

@router.get("/report-statistics", response_model=List[ReportStatisticsResponse])
async def get_report_statistics(
    days: Optional[int] = Query(30, description="Number of days to include"),
    db = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get report generation statistics"""
    try:
        # Validate admin access
        if not current_user or current_user.get('role') not in ['admin', 'administrator']:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Mock report statistics (would be real data from database)
        base_date = datetime.now() - timedelta(days=days)
        report_stats = []
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            total = max(20, int(45 + (i % 7) * 3 + (i % 3) * 5))  # Vary by day
            
            report_stats.append(ReportStatisticsResponse(
                date=current_date.strftime('%Y-%m-%d'),
                total_reports=total,
                pdf_reports=int(total * 0.4),
                excel_reports=int(total * 0.3),
                powerpoint_reports=int(total * 0.2),
                custom_reports=int(total * 0.1)
            ))

        return report_stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch report statistics")

@router.get("/health")
async def health_check():
    """Health check endpoint for admin analytics API"""
    return {
        "status": "healthy",
        "service": "Admin Analytics API",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "system_overview_metrics",
            "user_activity_tracking", 
            "framework_adoption_analysis",
            "department_performance_monitoring",
            "security_metrics_reporting",
            "system_growth_analytics",
            "report_generation_statistics",
            "admin_only_access_control"
        ]
    }