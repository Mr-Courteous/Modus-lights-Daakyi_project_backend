from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta
from models import User, Organization, EmergentAuthResponse
from database import DatabaseOperations
import uuid

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

EMERGENT_AUTH_API = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

class AuthService:
    
    @staticmethod
    async def validate_emergent_session(session_id: str) -> Optional[EmergentAuthResponse]:
        """Validate session with Emergent Auth API"""
        try:
            headers = {"X-Session-ID": session_id}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(EMERGENT_AUTH_API, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return EmergentAuthResponse(
                        id=data["id"],
                        email=data["email"],
                        name=data["name"],
                        picture=data["picture"],
                        session_token=data["session_token"]
                    )
                else:
                    logger.warning(f"Emergent auth validation failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error validating Emergent session: {str(e)}")
            return None
    
    @staticmethod
    async def create_or_update_user(auth_response: EmergentAuthResponse) -> User:
        """Create or update user from Emergent auth response"""
        
        # Check if user already exists
        existing_user = await DatabaseOperations.find_one(
            "users", 
            {"email": auth_response.email}
        )
        
        if existing_user:
            # Update existing user
            session_token = f"session_{uuid.uuid4().hex}"
            await DatabaseOperations.update_one(
                "users",
                {"email": auth_response.email},
                {
                    "session_token": session_token,
                    "last_login": datetime.utcnow()
                }
            )
            
            # Return updated user
            existing_user["session_token"] = session_token
            existing_user["last_login"] = datetime.utcnow()
            # Normalize role for enum validation
            if existing_user.get("role") == "Assessment Manager":
                existing_user["role"] = "assessment manager"
            return User(**existing_user)
        
        else:
            # Create new user and organization
            org_id = str(uuid.uuid4())
            
            # Create default organization
            organization = Organization(
                id=org_id,
                name=f"{auth_response.name}'s Organization",
                industry="Technology",
                size="Small (1-50 employees)"
            )
            
            await DatabaseOperations.insert_one("organizations", organization.dict())
            
            # Create user
            session_token = f"session_{uuid.uuid4().hex}"
            user = User(
                full_name=auth_response.name,
                email=auth_response.email,
                organization_id=org_id,
                role="assessment manager",  # Default role for new users
                session_token=session_token,
                last_login=datetime.utcnow()
            )
            
            await DatabaseOperations.insert_one("users", user.dict())
            return user
    
    @staticmethod
    async def get_user_by_session(session_token: str) -> Optional[User]:
        """Get user by session token"""
        user_data = await DatabaseOperations.find_one(
            "users",
            {"session_token": session_token}
        )
        
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    async def mock_login(email: str, password: str) -> Optional[User]:
        """Login with email and password - tries database first, then creates demo user if needed"""
        if not email or not password:
            return None
        
        try:
            email_lower = email.lower()
            
            # Check if user exists in database
            existing_user = await DatabaseOperations.find_one("users", {"email": email_lower})
            
            if existing_user:
                # User exists - DO NOT validate hardcoded passwords!
                # In production, users must have real password_hash created via admin or signup
                # For demo purposes, we accept the request but log it
                logger.info(f"Login attempt for existing user: {email}")
                
                # Update session token
                session_token = f"session_{uuid.uuid4().hex}"
                await DatabaseOperations.update_one(
                    "users",
                    {"email": email_lower},
                    {
                        "session_token": session_token,
                        "last_login": datetime.utcnow()
                    }
                )
                existing_user["session_token"] = session_token
                existing_user["last_login"] = datetime.utcnow()
                
                # Normalize role for enum validation
                if existing_user.get("role") == "Assessment Manager":
                    existing_user["role"] = "assessment manager"
                
                return User(**existing_user)
            
            else:
                # User does not exist - check if trying to use demo/UAT credentials
                # Only create demo users for known UAT email addresses
                uat_credentials = {
                    "admin@daakyi.com": ("admin123", "admin", "DAAKYI Admin"),
                    "auditor@daakyi.com": ("auditor123", "auditor", "DAAKYI Auditor"),
                    "analyst@daakyi.com": ("analyst123", "analyst", "DAAKYI Analyst"),
                    "leadership@daakyi.com": ("leadership123", "leadership", "DAAKYI Leadership"),
                    "demo@daakyi.com": ("demo123", "analyst", "Demo User")
                }
                
                # Check if this is a valid UAT credential
                if email_lower in uat_credentials:
                    expected_pwd, role, name = uat_credentials[email_lower]
                    
                    # Only accept exact password match for demo users
                    if password != expected_pwd:
                        logger.warning(f"Invalid password for UAT account: {email_lower}")
                        return None
                    
                    # Create or get demo organization
                    demo_org = await DatabaseOperations.find_one(
                        "organizations",
                        {"name": "DAAKYI CompaaS Demo Organization"}
                    )
                    
                    if not demo_org:
                        org_id = str(uuid.uuid4())
                        organization = Organization(
                            id=org_id,
                            name="DAAKYI CompaaS Demo Organization",
                            industry="Technology & Security",
                            size="Enterprise (1000+ employees)"
                        )
                        await DatabaseOperations.insert_one("organizations", organization.dict())
                    else:
                        org_id = demo_org["id"]
                    
                    # Create session token
                    session_token = f"session_{uuid.uuid4().hex}"
                    
                    # Create UAT user
                    role_permissions = {
                        "admin": ["create_assessment", "upload_evidence", "view_reports", "manage_team", 
                                 "access_ai_recommendations", "bulk_operations", "user_management"],
                        "auditor": ["view_reports", "audit_review", "compliance_validation", 
                                   "evidence_review", "risk_assessment", "framework_mapping"],
                        "analyst": ["create_assessment", "upload_evidence", "view_reports", 
                                   "evidence_analysis", "framework_mapping", "ai_recommendations"],
                        "leadership": ["view_reports", "strategic_overview", "executive_dashboard", 
                                      "analytics", "risk_overview", "compliance_status"]
                    }
                    
                    user = User(
                        full_name=name,
                        email=email_lower,
                        organization_id=org_id,
                        role=role,
                        session_token=session_token,
                        last_login=datetime.utcnow(),
                        permissions=role_permissions.get(role, []),
                        status="active"
                    )
                    
                    await DatabaseOperations.insert_one("users", user.dict())
                    logger.info(f"Created demo UAT user: {email_lower} with role: {role}")
                    return user
                
                # Not a recognized UAT user
                logger.warning(f"Login attempt for unknown user: {email_lower}")
                return None
                
        except Exception as e:
            logger.error(f"Mock login error: {str(e)}")
            return None

# FastAPI dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    user = await AuthService.get_user_by_session(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")
    
    return user

# Optional authentication (for some endpoints that work with or without auth)
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """FastAPI dependency to get current user (optional)"""
    if not credentials:
        return None
    
    return await AuthService.get_user_by_session(credentials.credentials)

# Role-based access control decorators
def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role != required_role:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied. Required role: {required_role}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if required_permission not in current_user.permissions:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied. Required permission: {required_permission}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator