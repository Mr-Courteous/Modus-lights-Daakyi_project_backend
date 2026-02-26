import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Local project imports
from database import get_database, close_database, DatabaseOperations
from routers.authlogin import router as authlogin_router
from routers.admin import router as admin_router
from mvp1_auth import MVP1AuthService
from mvp1_models import MVP1User, MVP1Organization, UserRole, UserStatus, UserPermissions
from mvp1_api import mvp1_router  # Core API (Org, Engagements)
from mvp1_analyst_workflow import analyst_router  # Analyst Workflow (Forms, AI)
from mvp1_auditor_workflow import auditor_router # Auditor Workflow (Review, Feedback)
from mvp1_admin_portal_api import admin_portal_router # Enhanced Admin Portal API
from ai_gap_analysis_api import router as ai_gap_analysis_router
from assessment_analytics_api import router as assessment_analytics_router
from advanced_ai_api import advanced_ai_router

# Evidence APIs
from evidence_linkage_api import router as evidence_linkage_router
from evidence_lifecycle_api import evidence_lifecycle_router

# Real-time Status and Risk Intelligence
from control_status_api import router as control_status_router
from risk_intelligence_api import router as risk_intelligence_router

# Report Generation APIs
from tokuro_report_api import router as tokuro_report_router

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("daakyi-compaas-main")


async def ensure_platform_admin():
    """Ensure the platform administrator exists upon startup"""
    try:
        email = "admin@daakyi.com"
        password = "1234567890"

        # 1. Ensure Platform Organization exists
        platform_org = await DatabaseOperations.find_one("mvp1_organizations", {"name": "DAAKYI Platform"})
        if not platform_org:
            org_id = str(uuid.uuid4())
            platform_org_obj = MVP1Organization(
                id=org_id,
                name="DAAKYI Platform",
                industry="Technology",
                size="Enterprise (1000+ employees)",
                subscription_tier="enterprise"
            )
            await DatabaseOperations.insert_one("mvp1_organizations", platform_org_obj.dict())
            logger.info("Created DAAKYI Platform organization")
        else:
            org_id = platform_org["id"]

        # 2. Ensure Admin User exists
        admin_user = await DatabaseOperations.find_one("mvp1_users", {"email": email})
        hashed_password = MVP1AuthService.hash_password(password)

        if not admin_user:
            admin_obj = MVP1User(
                name="Platform Admin",
                email=email,
                organization_id=org_id,
                role=UserRole.ADMIN,
                password_hash=hashed_password,
                status=UserStatus.ACTIVE,
                permissions=UserPermissions.ADMIN_PERMISSIONS,
                created_at=datetime.utcnow()
            )
            await DatabaseOperations.insert_one("mvp1_users", admin_obj.dict())
            logger.info(f"Platform admin created successfully: {email}")
        else:
            # Update password and ensure active status/admin role
            await DatabaseOperations.update_one(
                "mvp1_users",
                {"email": email},
                {
                    "password_hash": hashed_password,
                    "role": UserRole.ADMIN,
                    "status": UserStatus.ACTIVE,
                    "updated_at": datetime.utcnow()
                }
            )
            logger.info(f"Platform admin credentials updated: {email}")

    except Exception as e:
        logger.error(f"Error ensuring platform admin: {str(e)}")


# 2. Lifecycle Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    await get_database()

    # Ensure platform admin exists
    logger.info("Initializing system defaults...")
    await ensure_platform_admin()

    yield
    # Shutdown: Clean up connections
    logger.info("Closing database connection...")
    await close_database()


# 3. Initialize FastAPI
app = FastAPI(
    title="DAAKYI CompaaS API - Main",
    description="Clean main server entrypoint (self-contained)",
    version="1.0.0",
    lifespan=lifespan
)


# 4. Security: CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 5. Routing: include routers from local modules
# Mount the MVP1 router under /api/v2 to preserve existing routing structure
app.include_router(mvp1_router, prefix="/api/v2")

# Mount the authlogin router (routes are prefixed by the router itself)
app.include_router(authlogin_router, prefix="/api/v2")

# Mount the admin router (routes are prefixed by the router itself: /api/mvp1/admin)
app.include_router(admin_router)

# Mount the analyst router
app.include_router(analyst_router)

# Mount the auditor router
app.include_router(auditor_router)

# Mount the enhanced admin portal router
app.include_router(admin_portal_router)


# Mount AI and Analytics routers
app.include_router(ai_gap_analysis_router)
app.include_router(assessment_analytics_router)
app.include_router(advanced_ai_router)

# Mount Evidence routers
app.include_router(evidence_linkage_router)
app.include_router(evidence_lifecycle_router)

# Mount Control Status and Risk Intelligence
app.include_router(control_status_router)
app.include_router(risk_intelligence_router)

# Mount Report Generation router
app.include_router(tokuro_report_router)


@app.get("/health", tags=["System"]) 
async def health_check():
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ── Audit Logging Endpoint (called by frontend RBAC guards) ──────────────────

class AccessAttemptLog(BaseModel):
    action_type: str
    action_description: str
    result: str                          # 'GRANTED' or 'DENIED'
    reason: str
    route: str
    additional_data: Optional[Dict[str, Any]] = None


@app.post("/api/audit/access-attempt", tags=["Audit"])
async def log_access_attempt(payload: AccessAttemptLog, request: Request):
    """Receives RBAC access attempt logs from the frontend and persists them."""
    try:
        log_doc = {
            "id": str(uuid.uuid4()),
            "action_type": payload.action_type,
            "action_description": payload.action_description,
            "result": payload.result,
            "reason": payload.reason,
            "route": payload.route,
            "additional_data": payload.additional_data or {},
            "client_ip": request.client.host if request.client else "unknown",
            "timestamp": datetime.utcnow().isoformat(),
        }
        await DatabaseOperations.insert_one("mvp1_audit_access_logs", log_doc)
        logger.info(f"Access attempt logged: {payload.result} - {payload.route}")
        return {"status": "logged", "id": log_doc["id"]}
    except Exception as e:
        # Never let audit logging break the app — just swallow and log
        logger.warning(f"Failed to persist access attempt log: {e}")
        return {"status": "logged", "id": str(uuid.uuid4())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
