"""
MVP 1 - Authentication & Authorization System
Role-based authentication with multi-tenant support and session management

Features:
- Internal credential management (email/password)
- Role-based access control (Admin, Analyst, Auditor, Leadership)
- Multi-tenant organization isolation
- Concurrent session support
- Enhanced security with rate limiting and account lockout
"""

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Union
import uuid
import bcrypt
from mvp1_models import (
    MVP1User, MVP1Organization, UserRole, UserStatus, UserPermissions,
    UserCreationRequest, AuditLogEntry
)
from database import DatabaseOperations
import os

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Security Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "mvp1-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MVP1AuthService:
    """Enhanced authentication service for MVP 1 with role-based access"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt.

        Bcrypt has a hard limit of 72 bytes; passlib will raise an error if the
        input exceeds that.  To avoid startup failures (see the platform admin
        creation code) we proactively truncate any incoming password to 72
        bytes.  This mirrors the suggestion in the error message and ensures
        callers don't need to remember the limitation.
        """
        # passlib/bcrypt only cares about the *bytes* length, not the number of
        # characters.  UTF-8 is used throughout the codebase, so count its
        # encoded size before truncating.
        pw_bytes = password.encode('utf-8')
        if len(pw_bytes) > 72:
            password = pw_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def authenticate_user(email: str, password: str, organization_id: Optional[str] = None) -> Optional[MVP1User]:
        """Authenticate user with email/password"""
        try:
            # Find user by email
            query = {"email": email.lower()}
            if organization_id:
                query["organization_id"] = organization_id
            
            user_data = await DatabaseOperations.find_one("mvp1_users", query)
            
            if not user_data:
                logger.warning(f"Authentication failed: User not found - {email}")
                return None
            
            user = MVP1User(**user_data)
            
            # Check if account is locked
            if user.account_locked_until and user.account_locked_until > datetime.utcnow():
                logger.warning(f"Authentication failed: Account locked - {email}")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked until {user.account_locked_until}"
                )
            
            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"Authentication failed: Account not active - {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is not active"
                )
            
            # Verify password
            if not user.password_hash or not MVP1AuthService.verify_password(password, user.password_hash):
                # Increment failed attempts
                await MVP1AuthService._handle_failed_login(user.id)
                logger.warning(f"Authentication failed: Invalid password - {email}")
                return None
            
            # Reset failed attempts on successful login
            await MVP1AuthService._reset_failed_attempts(user.id)
            
            # Update last login
            await DatabaseOperations.update_one(
                "mvp1_users",
                {"id": user.id},
                {
                    "last_login": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
            )
            
            # Log successful authentication
            await MVP1AuthService._log_audit_event(
                organization_id=user.organization_id,
                action_type="user_login",
                action_description=f"User logged in successfully",
                actor_id=user.id,
                actor_name=user.name,
                actor_role=user.role
            )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            return None
    
    @staticmethod
    async def _handle_failed_login(user_id: str):
        """Handle failed login attempt"""
        user_data = await DatabaseOperations.find_one("mvp1_users", {"id": user_id})
        if user_data:
            failed_attempts = user_data.get("failed_login_attempts", 0) + 1
            
            update_data = {"failed_login_attempts": failed_attempts}
            
            # Lock account if max attempts reached
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                lockout_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                update_data["account_locked_until"] = lockout_until
                logger.warning(f"Account locked due to failed attempts: {user_id}")
            
            await DatabaseOperations.update_one("mvp1_users", {"id": user_id}, update_data)
    
    @staticmethod
    async def _reset_failed_attempts(user_id: str):
        """Reset failed login attempts"""
        await DatabaseOperations.update_one(
            "mvp1_users", 
            {"id": user_id}, 
            {
                "failed_login_attempts": 0,
                "account_locked_until": None
            }
        )
    
    @staticmethod
    async def create_user(user_request: UserCreationRequest, created_by: str, organization_id: str) -> tuple[MVP1User, str]:
        """Create new user (Admin only) - Returns user and temporary password"""
        # Check if user already exists
        existing_user = await DatabaseOperations.find_one(
            "mvp1_users", 
            {"email": user_request.email.lower(), "organization_id": organization_id}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Generate temporary password (should be changed on first login)
        temp_password = f"TempPass{uuid.uuid4().hex[:8]}!"
        hashed_password = MVP1AuthService.hash_password(temp_password)
        
        # Set role-based permissions
        permissions = user_request.permissions or MVP1AuthService._get_role_permissions(user_request.role)
        
        # Create user
        new_user = MVP1User(
            name=user_request.name,
            email=user_request.email.lower(),
            organization_id=organization_id,
            role=user_request.role,
            department=user_request.department,
            job_title=user_request.job_title,
            password_hash=hashed_password,
            permissions=permissions,
            assigned_engagements=user_request.assigned_engagements,
            status=UserStatus.PENDING,  # Requires password change
            created_by=created_by
        )
        
        # Insert to database
        await DatabaseOperations.insert_one("mvp1_users", new_user.dict())
        
        # Log user creation
        await MVP1AuthService._log_audit_event(
            organization_id=organization_id,
            action_type="user_created",
            action_description=f"New user created: {user_request.name} ({user_request.role})",
            actor_id=created_by,
            target_type="user",
            target_id=new_user.id,
            target_name=new_user.name
        )
        
        logger.info(f"User created successfully: {new_user.email} with role {new_user.role}")
        logger.info(f"Temporary password for {new_user.email}: {temp_password}")
        
        return new_user, temp_password
    
    @staticmethod
    def _get_role_permissions(role: UserRole) -> List[str]:
        """Get default permissions for role"""
        if role == UserRole.ADMIN:
            return UserPermissions.ADMIN_PERMISSIONS
        elif role == UserRole.ANALYST:
            return UserPermissions.ANALYST_PERMISSIONS
        elif role == UserRole.AUDITOR:
            return UserPermissions.AUDITOR_PERMISSIONS
        elif role == UserRole.LEADERSHIP:
            return UserPermissions.LEADERSHIP_PERMISSIONS
        else:
            return []
    
    @staticmethod
    async def get_user_by_token(token: str) -> Optional[MVP1User]:
        """Get user by JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
        except JWTError:
            return None
        
        user_data = await DatabaseOperations.find_one("mvp1_users", {"id": user_id})
        if user_data and user_data.get("status") == UserStatus.ACTIVE:
            # Update last activity
            await DatabaseOperations.update_one(
                "mvp1_users",
                {"id": user_id},
                {"last_activity": datetime.utcnow()}
            )
            return MVP1User(**user_data)
        return None
    
    @staticmethod
    async def get_user_by_daakyi_session(session_token: str) -> Optional[MVP1User]:
        """
        Authentication bridge: Get MVP1 user by DAAKYI or MVP1 session token
        SECURITY FIX: Only returns existing MVP1 users, no auto-creation
        RBAC FIX: Maps DAAKYI roles to proper MVP1 UserRole enum values
        """
        # First check if this is an MVP1 session token (format: mvp1_session_{hex})
        if session_token.startswith("mvp1_session_"):
            try:
                user_data = await DatabaseOperations.find_one(
                    "mvp1_users",
                    {"session_token": session_token}
                )
                
                if user_data:
                    logger.info(f"MVP1 session validated for user: {user_data.get('email')}")
                    return MVP1User(**user_data)
                else:
                    logger.warning(f"MVP1 session token not found or invalid")
                    return None
            except Exception as e:
                logger.error(f"MVP1 session validation error: {str(e)}")
                return None
        
        # Otherwise try DAAKYI session token (authentication bridge)
        try:
            # Import the original auth service to get user by session
            from auth import AuthService
            
            # Get the original DAAKYI user
            daakyi_user = await AuthService.get_user_by_session(session_token)
            if not daakyi_user:
                logger.warning("DAAKYI session token invalid or expired")
                return None
            
            # SECURITY FIX: Only look for existing MVP1 users, no auto-creation
            # Check if MVP1 user already exists for this email
            mvp1_user_data = await DatabaseOperations.find_one(
                "mvp1_users", 
                {"email": daakyi_user.email.lower()}
            )
            
            if mvp1_user_data:
                # RBAC FIX: Update role mapping for admin users
                daakyi_role = daakyi_user.role.lower() if daakyi_user.role else "assessment manager"
                
                # Map DAAKYI admin role to MVP1 UserRole.ADMIN
                if daakyi_role in ["admin", "system administrator", "organization admin"]:
                    mapped_role = UserRole.ADMIN
                elif daakyi_role in ["assessment manager", "analyst"]:
                    mapped_role = UserRole.ANALYST
                elif daakyi_role in ["auditor"]:
                    mapped_role = UserRole.AUDITOR
                elif daakyi_role in ["leadership", "executive"]:
                    mapped_role = UserRole.LEADERSHIP
                else:
                    # Default to analyst for unknown roles
                    mapped_role = UserRole.ANALYST
                    logger.warning(f"Unknown DAAKYI role '{daakyi_user.role}', defaulting to analyst")
                
                # Update the MVP1 user record with proper role mapping
                await DatabaseOperations.update_one(
                    "mvp1_users",
                    {"id": mvp1_user_data["id"]},
                    {
                        "role": mapped_role,
                        "last_activity": datetime.utcnow()
                    }
                )
                
                # Return user with updated role
                mvp1_user_data["role"] = mapped_role
                logger.info(f"Authentication bridge: Found existing MVP1 user: {daakyi_user.email}, mapped role: {daakyi_user.role} -> {mapped_role}")
                return MVP1User(**mvp1_user_data)
            
            # SECURITY FIX: Do NOT auto-create users
            # Users must be explicitly created by administrators
            logger.warning(f"Authentication bridge: MVP1 user not found for email: {daakyi_user.email}. User must be created by administrator.")
            return None
            
        except Exception as e:
            logger.error(f"Authentication bridge error: {str(e)}")
            return None
    
    @staticmethod
    async def _ensure_organization_exists(daakyi_org_id: str) -> str:
        """Ensure MVP1 organization exists for DAAKYI organization"""
        try:
            # Check if MVP1 organization already exists
            mvp1_org = await DatabaseOperations.find_one(
                "mvp1_organizations", 
                {"daakyi_org_id": daakyi_org_id}
            )
            
            if mvp1_org:
                return mvp1_org["id"]
            
            # Get DAAKYI organization data
            from database import DatabaseOperations as DAOps
            daakyi_org = await DAOps.find_one("organizations", {"id": daakyi_org_id})
            
            if daakyi_org:
                # Create MVP1 organization from DAAKYI organization
                new_mvp1_org = MVP1Organization(
                    name=daakyi_org.get("name", "Migrated Organization"),
                    industry=daakyi_org.get("industry", "Technology"),
                    size=daakyi_org.get("size", "Medium (51-500)"),
                    headquarters_location="Global",
                    supported_frameworks=daakyi_org.get("compliance_programs", ["ISO 27001", "NIST CSF"]),
                    daakyi_org_id=daakyi_org_id  # Track original organization
                )
                
                await DatabaseOperations.insert_one("mvp1_organizations", new_mvp1_org.dict())
                logger.info(f"Authentication bridge: Created MVP1 organization from DAAKYI org: {daakyi_org.get('name')}")
                
                return new_mvp1_org.id
            else:
                # Create default organization if DAAKYI org not found
                default_org = MVP1Organization(
                    name="Bridge Organization",
                    industry="Technology",
                    size="Medium (51-500)",
                    headquarters_location="Global",
                    supported_frameworks=["ISO 27001", "NIST CSF", "SOC 2 Type I"],
                    daakyi_org_id=daakyi_org_id
                )
                
                await DatabaseOperations.insert_one("mvp1_organizations", default_org.dict())
                logger.info(f"Authentication bridge: Created default MVP1 organization for DAAKYI org: {daakyi_org_id}")
                
                return default_org.id
                
        except Exception as e:
            logger.error(f"Error ensuring organization exists: {str(e)}")
            # Return first available organization as fallback
            first_org = await DatabaseOperations.find_one("mvp1_organizations", {})
            if first_org:
                return first_org["id"]
            else:
                # Create emergency fallback organization
                emergency_org = MVP1Organization(
                    name="Emergency Organization",
                    industry="Technology",
                    size="Small (1-50)",
                    headquarters_location="Global",
                    supported_frameworks=["ISO 27001"]
                )
                await DatabaseOperations.insert_one("mvp1_organizations", emergency_org.dict())
                return emergency_org.id
    
    @staticmethod
    async def login_user(email: str, password: str, organization_id: Optional[str] = None) -> dict:
        """Login user and return token and user info"""
        user = await MVP1AuthService.authenticate_user(email, password, organization_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = MVP1AuthService.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        # Create and persist a session token (SessionManager handles DB update)
        try:
            from mvp1_auth import SessionManager as _SessionManager
        except Exception:
            _SessionManager = SessionManager

        session_token = await SessionManager.create_session(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_token": session_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "organization_id": user.organization_id,
                "permissions": user.permissions,
                "status": user.status
            }
        }
    
    @staticmethod
    async def setup_initial_admin(organization_id: str) -> MVP1User:
        """Setup initial admin user for organization"""
        admin_email = "admin@daakyi.com"
        admin_password = "DaakyiSecure2025!"
        
        # Check if admin already exists
        existing_admin = await DatabaseOperations.find_one(
            "mvp1_users",
            {"email": admin_email, "organization_id": organization_id}
        )
        
        if existing_admin:
            return MVP1User(**existing_admin)
        
        # Create admin user
        hashed_password = MVP1AuthService.hash_password(admin_password)
        
        admin_user = MVP1User(
            name="Nana Awuah",
            email=admin_email,
            organization_id=organization_id,
            role=UserRole.ADMIN,
            department="Administration",
            job_title="Platform Administrator",
            password_hash=hashed_password,
            permissions=UserPermissions.ADMIN_PERMISSIONS,
            status=UserStatus.ACTIVE  # Admin is immediately active
        )
        
        await DatabaseOperations.insert_one("mvp1_users", admin_user.dict())
        
        logger.info(f"Initial admin user created: {admin_email}")
        return admin_user
    
    @staticmethod
    async def create_sample_organizations() -> List[MVP1Organization]:
        """Create sample organizations for testing"""
        sample_orgs = [
            {
                "name": "AlphaTech Solutions",
                "industry": "Technology",
                "size": "Medium (51-500)",
                "headquarters_location": "San Francisco, CA",
                "supported_frameworks": ["ISO 27001", "NIST CSF", "SOC 2 Type I"]
            },
            {
                "name": "BetaSecure Inc.",
                "industry": "Cybersecurity",
                "size": "Small (1-50)",
                "headquarters_location": "Austin, TX",
                "supported_frameworks": ["NIST CSF", "SOC 2 Type I"]
            },
            {
                "name": "CyberNova Group",
                "industry": "Financial Services",
                "size": "Large (500+)",
                "headquarters_location": "New York, NY",
                "supported_frameworks": ["SOC 2 Type I", "ISO 27001", "PCI DSS"]
            },
            {
                "name": "GhanaGovEnergy",
                "industry": "Government - Energy",
                "size": "Large (500+)",
                "headquarters_location": "Accra, Ghana",
                "supported_frameworks": ["Ghana CII Directives", "ISO 27001"]
            },
            {
                "name": "GulfFinTech",
                "industry": "Financial Technology",
                "size": "Medium (51-500)",
                "headquarters_location": "Dubai, UAE",
                "supported_frameworks": ["ISO 27001", "NIST CSF", "SOC 2 Type I"]
            },
            {
                "name": "DAAKYI Internal Testing",
                "industry": "Compliance Technology",
                "size": "Small (1-50)",
                "headquarters_location": "Global",
                "supported_frameworks": ["ISO 27001", "NIST CSF", "SOC 2 Type I", "Ghana CII Directives"]
            }
        ]
        
        created_orgs = []
        
        for org_data in sample_orgs:
            # Check if organization already exists
            existing_org = await DatabaseOperations.find_one(
                "mvp1_organizations",
                {"name": org_data["name"]}
            )
            
            if not existing_org:
                new_org = MVP1Organization(**org_data)
                await DatabaseOperations.insert_one("mvp1_organizations", new_org.dict())
                
                # Create initial admin for each organization
                await MVP1AuthService.setup_initial_admin(new_org.id)
                
                created_orgs.append(new_org)
                logger.info(f"Created organization: {new_org.name}")
            else:
                created_orgs.append(MVP1Organization(**existing_org))
        
        return created_orgs
    
    @staticmethod
    async def _log_audit_event(
        organization_id: str,
        action_type: str,
        action_description: str,
        actor_id: str,
        actor_name: Optional[str] = None,
        actor_role: Optional[UserRole] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        engagement_id: Optional[str] = None,
        changes_made: Optional[dict] = None
    ):
        """Log audit events for compliance tracking"""
        audit_entry = AuditLogEntry(
            organization_id=organization_id,
            engagement_id=engagement_id,
            action_type=action_type,
            action_description=action_description,
            actor_id=actor_id,
            actor_name=actor_name or "Unknown",
            actor_role=actor_role or UserRole.ADMIN,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            changes_made=changes_made or {},
            category="authentication"
        )
        
        await DatabaseOperations.insert_one("mvp1_audit_logs", audit_entry.dict())

# FastAPI Dependencies for MVP 1 Authentication

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> MVP1User:
    """FastAPI dependency to get current authenticated user with authentication bridge"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try MVP1 token format first
    user = await MVP1AuthService.get_user_by_token(credentials.credentials)
    if user:
        return user
    
    # If MVP1 token fails, try DAAKYI session token format (authentication bridge)
    user = await MVP1AuthService.get_user_by_daakyi_session(credentials.credentials)
    if user:
        return user
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[MVP1User]:
    """FastAPI dependency to get current user (optional) with authentication bridge"""
    if not credentials:
        return None
    
    # Try MVP1 token format first
    user = await MVP1AuthService.get_user_by_token(credentials.credentials)
    if user:
        return user
    
    # If MVP1 token fails, try DAAKYI session token format (authentication bridge)
    return await MVP1AuthService.get_user_by_daakyi_session(credentials.credentials)

# Role-based access control decorators for MVP 1
import functools

def require_role(required_roles: Union[UserRole, List[UserRole]]):
    """Decorator to require specific role(s) with admin override"""
    if isinstance(required_roles, UserRole):
        required_roles = [required_roles]
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: MVP1User = Depends(get_current_user), **kwargs):
            # Admin override: Admin users can access all role-specific endpoints
            if current_user.role == UserRole.ADMIN or current_user.role == "admin":
                return await func(*args, current_user=current_user, **kwargs)
            
            # Check if user has required role
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role(s): {[role.value for role in required_roles]}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to require specific permission with admin override"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: MVP1User = Depends(get_current_user), **kwargs):
            # Admin override: Admin users have all permissions
            if current_user.role == UserRole.ADMIN or current_user.role == "admin":
                return await func(*args, current_user=current_user, **kwargs)
                
            if required_permission not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {required_permission}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_admin(func):
    """Decorator to require admin role"""
    @functools.wraps(func)
    async def wrapper(*args, current_user: MVP1User = Depends(get_current_user), **kwargs):
        if current_user.role != UserRole.ADMIN and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

def require_admin_for_user_management(operation: str = "manage users"):
    """Decorator to require admin role with specific error message for user management operations"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: MVP1User = Depends(get_current_user), **kwargs):
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Administrator privileges required to {operation}."
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Organization isolation helper
async def ensure_organization_access(user: MVP1User, resource_org_id: str):
    """Ensure user has access to organization resources"""
    if user.organization_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to organization resources"
        )

# Session management helpers
class SessionManager:
    """Session management for concurrent sessions"""
    
    @staticmethod
    async def create_session(user_id: str) -> str:
        """Create new session for user"""
        session_token = f"mvp1_session_{uuid.uuid4().hex}"
        
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            {
                "session_token": session_token,
                "last_activity": datetime.utcnow()
            }
        )
        
        return session_token
    
    @staticmethod
    async def invalidate_session(user_id: str):
        """Invalidate user session"""
        await DatabaseOperations.update_one(
            "mvp1_users",
            {"id": user_id},
            {"session_token": None}
        )
    
    @staticmethod
    async def cleanup_expired_sessions():
        """Cleanup expired sessions (run periodically)"""
        # Sessions expire after 24 hours of inactivity
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        await DatabaseOperations.update_many(
            "mvp1_users",
            {"last_activity": {"$lt": cutoff_time}},
            {"session_token": None}
        )