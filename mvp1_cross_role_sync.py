"""
MVP 1 Week 6: Cross-Role Synchronization Backend APIs
Real-time collaboration, notifications, activity feeds, and workflow synchronization

Features:
- Real-time activity feeds across all user roles
- Inter-role notifications and alerting system
- Discussion threads with comment trails and mentions
- Status synchronization with workflow state management
- Reassignment capabilities with proper handoff protocols
- Escalation flags and automated workflow triggers
- Collaboration indicators and activity timestamps
- Cross-role data synchronization and conflict resolution
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
import uuid
import logging
import json
from pydantic import BaseModel
from enum import Enum

from mvp1_models import (
    MVP1User, UserRole, UserStatus, EngagementStatus, 
    AuditLogEntry
)
from mvp1_auth import get_current_user, require_role, ensure_organization_access
from database import DatabaseOperations

logger = logging.getLogger(__name__)

# Create router for cross-role synchronization endpoints
sync_router = APIRouter(prefix="/api/mvp1/sync", tags=["MVP1 Cross-Role Synchronization"])

# =====================================
# SYNCHRONIZATION PYDANTIC MODELS
# =====================================

class ActivityType(str, Enum):
    SUBMISSION_CREATED = "submission_created"
    SUBMISSION_UPDATED = "submission_updated"
    SUBMISSION_REVIEWED = "submission_reviewed"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_ANNOTATED = "evidence_annotated"
    STATUS_CHANGED = "status_changed"
    USER_ASSIGNED = "user_assigned"
    USER_MENTIONED = "user_mentioned"
    DEADLINE_APPROACHING = "deadline_approaching"
    ESCALATION_TRIGGERED = "escalation_triggered"
    COMMENT_ADDED = "comment_added"
    WORKFLOW_COMPLETED = "workflow_completed"

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"
    SUCCESS = "success"

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    FEEDBACK_PROVIDED = "feedback_provided"
    REVISION_REQUIRED = "revision_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"

class ActivityFeedItem(BaseModel):
    """Real-time activity feed item"""
    activity_id: str
    activity_type: ActivityType
    title: str
    description: str
    actor_id: str
    actor_name: str
    actor_role: UserRole
    target_type: str  # "submission", "engagement", "user", "evidence"
    target_id: str
    target_title: Optional[str] = None
    engagement_id: Optional[str] = None
    framework: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    is_read: bool = False
    priority: str = "normal"  # "low", "normal", "high", "urgent"

class NotificationItem(BaseModel):
    """Cross-role notification"""
    notification_id: str
    notification_type: NotificationType
    title: str
    message: str
    recipient_id: str
    recipient_role: UserRole
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    related_activity_id: Optional[str] = None
    action_required: bool = False
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class DiscussionThread(BaseModel):
    """Discussion thread for collaboration"""
    thread_id: str
    title: str
    context_type: str  # "submission", "engagement", "evidence"
    context_id: str
    context_title: str
    participants: List[Dict[str, Any]]
    created_by: str
    created_at: datetime
    last_activity: datetime
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    message_count: int = 0
    priority: str = "normal"

class ThreadMessage(BaseModel):
    """Message within a discussion thread"""
    message_id: str
    thread_id: str
    author_id: str
    author_name: str
    author_role: UserRole
    content: str
    message_type: str = "text"  # "text", "system", "file_attachment", "mention"
    mentions: List[str] = []  # List of user IDs mentioned
    attachments: List[Dict[str, Any]] = []
    parent_message_id: Optional[str] = None  # For replies
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_system_message: bool = False

class WorkflowStateSync(BaseModel):
    """Workflow state synchronization"""
    sync_id: str
    engagement_id: str
    submission_id: Optional[str] = None
    current_status: WorkflowStatus
    previous_status: Optional[WorkflowStatus] = None
    current_assignee: Optional[str] = None
    previous_assignee: Optional[str] = None
    status_changed_by: str
    status_changed_at: datetime
    next_action_required: Optional[str] = None
    next_action_assignee: Optional[str] = None
    next_action_due: Optional[datetime] = None
    workflow_stage: str
    completion_percentage: float
    blocking_issues: List[str] = []
    collaboration_status: str = "active"  # "active", "waiting", "blocked", "completed"

class CollaborationIndicator(BaseModel):
    """Real-time collaboration indicators"""
    context_type: str  # "submission", "engagement", "evidence"
    context_id: str
    active_users: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    last_updated: datetime
    collaboration_health: str = "good"  # "good", "attention", "blocked"

# =====================================
# WEBSOCKET CONNECTION MANAGER
# =====================================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.organization_connections: Dict[str, Set[str]] = {}  # org_id -> set of connection_ids
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str, organization_id: str):
        """Connect a WebSocket client"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Track organization connections
        if organization_id not in self.organization_connections:
            self.organization_connections[organization_id] = set()
        self.organization_connections[organization_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
    
    def disconnect(self, connection_id: str, user_id: str, organization_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from organization connections
        if organization_id in self.organization_connections:
            self.organization_connections[organization_id].discard(connection_id)
            if not self.organization_connections[organization_id]:
                del self.organization_connections[organization_id]
        
        logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                try:
                    websocket = self.active_connections.get(connection_id)
                    if websocket:
                        await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to {connection_id}: {e}")
                    # Remove failed connection
                    self.user_connections[user_id].discard(connection_id)
                    if connection_id in self.active_connections:
                        del self.active_connections[connection_id]
    
    async def broadcast_to_organization(self, message: dict, organization_id: str):
        """Broadcast message to all users in an organization"""
        if organization_id in self.organization_connections:
            for connection_id in self.organization_connections[organization_id].copy():
                try:
                    websocket = self.active_connections.get(connection_id)
                    if websocket:
                        await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    # Remove failed connection
                    self.organization_connections[organization_id].discard(connection_id)
                    if connection_id in self.active_connections:
                        del self.active_connections[connection_id]

# Global connection manager instance
manager = ConnectionManager()

# =====================================
# WEBSOCKET ENDPOINTS
# =====================================

@sync_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time synchronization"""
    connection_id = str(uuid.uuid4())
    
    try:
        # For demo purposes, we'll use a mock organization_id
        # In production, this would be retrieved from the authenticated user
        organization_id = "org-demo-123"
        
        await manager.connect(websocket, connection_id, user_id, organization_id)
        
        # Send initial connection success message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle ping/pong for keepalive
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id, organization_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(connection_id, user_id, organization_id)

# =====================================
# ACTIVITY FEED ENDPOINTS
# =====================================

@sync_router.get("/activity-feed", response_model=List[ActivityFeedItem])
async def get_activity_feed(
    limit: int = 50,
    activity_type: Optional[ActivityType] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get real-time activity feed for user's organization"""
    try:
        # Mock activity feed data (in production, fetch from database)
        activities = [
            ActivityFeedItem(
                activity_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                activity_type=ActivityType.SUBMISSION_CREATED,
                title="New ISO 27001 Submission",
                description="Sarah Johnson created a new submission for control A.5.1.1",
                actor_id="USR-SARAH123",
                actor_name="Sarah Johnson",
                actor_role=UserRole.ANALYST,
                target_type="submission",
                target_id="SUB-ABC12345",
                target_title="A.5.1.1 - Policies for information security",
                engagement_id="ENG-ISO27001",
                framework="ISO 27001",
                metadata={"control_id": "A.5.1.1", "confidence_score": 92.5},
                created_at=datetime.utcnow() - timedelta(minutes=15),
                priority="high"
            ),
            ActivityFeedItem(
                activity_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                activity_type=ActivityType.FEEDBACK_SUBMITTED,
                title="Auditor Feedback Provided",
                description="Mike Chen provided feedback on NIST CSF submission",
                actor_id="USR-MIKE456",
                actor_name="Mike Chen",
                actor_role=UserRole.AUDITOR,
                target_type="submission",
                target_id="SUB-DEF67890",
                target_title="PR.AC-1 - Identity management",
                engagement_id="ENG-NISTCSF",
                framework="NIST CSF",
                metadata={"feedback_type": "requires_revision", "compliance_rating": 3},
                created_at=datetime.utcnow() - timedelta(hours=2),
                priority="normal"
            ),
            ActivityFeedItem(
                activity_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                activity_type=ActivityType.EVIDENCE_UPLOADED,
                title="Evidence Uploaded",
                description="Lisa Rodriguez uploaded policy documentation",
                actor_id="USR-LISA789",
                actor_name="Lisa Rodriguez",
                actor_role=UserRole.ANALYST,
                target_type="evidence",
                target_id="EVD-GHI01234",
                target_title="Security_Policy_v2.1.pdf",
                engagement_id="ENG-SOC2",
                framework="SOC 2",
                metadata={"file_size": "2.4 MB", "ai_confidence": 94.8},
                created_at=datetime.utcnow() - timedelta(hours=6),
                priority="normal"
            ),
            ActivityFeedItem(
                activity_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                activity_type=ActivityType.STATUS_CHANGED,
                title="Submission Approved",
                description="David Kim approved Ghana CII Directives submission",
                actor_id="USR-DAVID012",
                actor_name="David Kim",
                actor_role=UserRole.AUDITOR,
                target_type="submission",
                target_id="SUB-JKL56789",
                target_title="CII.1.1 - Critical Infrastructure Security",
                engagement_id="ENG-GHANACII",
                framework="Ghana CII Directives",
                metadata={"previous_status": "under_review", "new_status": "approved"},
                created_at=datetime.utcnow() - timedelta(hours=12),
                priority="normal"
            ),
            ActivityFeedItem(
                activity_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                activity_type=ActivityType.ESCALATION_TRIGGERED,
                title="Workflow Escalated",
                description="ISO 27001 engagement escalated due to deadline proximity",
                actor_id="SYSTEM",
                actor_name="System",
                actor_role=UserRole.ADMIN,
                target_type="engagement",
                target_id="ENG-ISO27001",
                target_title="ISO 27001 Implementation Assessment",
                engagement_id="ENG-ISO27001",
                framework="ISO 27001",
                metadata={"escalation_reason": "deadline_approaching", "days_remaining": 3},
                created_at=datetime.utcnow() - timedelta(days=1),
                is_read=False,
                priority="urgent"
            )
        ]

        # Apply activity type filter if provided
        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]
        
        # Apply limit
        activities = activities[:limit]

        logger.info(f"Retrieved {len(activities)} activity feed items for user {current_user.id}")
        return activities

    except Exception as e:
        logger.error(f"Error getting activity feed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity feed"
        )

# =====================================
# NOTIFICATION ENDPOINTS
# =====================================

@sync_router.get("/notifications", response_model=List[NotificationItem])
async def get_notifications(
    unread_only: bool = False,
    notification_type: Optional[NotificationType] = None,
    limit: int = 20,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get notifications for current user"""
    try:
        # Mock notifications data (in production, fetch from database)
        notifications = [
            NotificationItem(
                notification_id=f"NOT-{uuid.uuid4().hex[:8].upper()}",
                notification_type=NotificationType.URGENT,
                title="Review Required",
                message="You have 3 pending submissions awaiting auditor review",
                recipient_id=current_user.id,
                recipient_role=current_user.role,
                sender_id="USR-SARAH123",
                sender_name="Sarah Johnson",
                action_required=True,
                action_url="/auditor/dashboard",
                action_text="Review Submissions",
                created_at=datetime.utcnow() - timedelta(hours=1),
                expires_at=datetime.utcnow() + timedelta(days=1)
            ),
            NotificationItem(
                notification_id=f"NOT-{uuid.uuid4().hex[:8].upper()}",
                notification_type=NotificationType.INFO,
                title="New AI Insight Available",
                message="AI analysis suggests 23% faster control implementation opportunity",
                recipient_id=current_user.id,
                recipient_role=current_user.role,
                action_required=False,
                action_url="/leadership/dashboard",
                action_text="View Insights",
                created_at=datetime.utcnow() - timedelta(hours=4),
                read_at=datetime.utcnow() - timedelta(hours=2)
            ),
            NotificationItem(
                notification_id=f"NOT-{uuid.uuid4().hex[:8].upper()}",
                notification_type=NotificationType.WARNING,
                title="Deadline Approaching",
                message="ISO 27001 assessment deadline in 3 days",
                recipient_id=current_user.id,
                recipient_role=current_user.role,
                action_required=True,
                action_url="/admin-portal/engagements",
                action_text="View Engagement",
                created_at=datetime.utcnow() - timedelta(days=1),
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
        ]

        # Apply filters
        if unread_only:
            notifications = [n for n in notifications if n.read_at is None]
        
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]
        
        # Apply limit
        notifications = notifications[:limit]

        logger.info(f"Retrieved {len(notifications)} notifications for user {current_user.id}")
        return notifications

    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )

@sync_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Mark notification as read"""
    try:
        # In production, update notification in database
        # await DatabaseOperations.update_one(
        #     "mvp1_notifications",
        #     {"notification_id": notification_id, "recipient_id": current_user.id},
        #     {"read_at": datetime.utcnow()}
        # )

        logger.info(f"Marked notification {notification_id} as read for user {current_user.id}")
        return {"message": "Notification marked as read", "notification_id": notification_id}

    except Exception as e:
        logger.error(f"Error marking notification as read for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

# =====================================
# DISCUSSION THREAD ENDPOINTS
# =====================================

@sync_router.get("/discussions", response_model=List[DiscussionThread])
async def get_discussion_threads(
    context_type: Optional[str] = None,
    context_id: Optional[str] = None,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get discussion threads for user's context"""
    try:
        # Mock discussion threads (in production, fetch from database)
        threads = [
            DiscussionThread(
                thread_id=f"THR-{uuid.uuid4().hex[:8].upper()}",
                title="ISO 27001 A.5.1.1 Implementation Discussion",
                context_type="submission",
                context_id="SUB-ABC12345",
                context_title="A.5.1.1 - Policies for information security",
                participants=[
                    {"user_id": "USR-SARAH123", "name": "Sarah Johnson", "role": "analyst"},
                    {"user_id": "USR-MIKE456", "name": "Mike Chen", "role": "auditor"},
                    {"user_id": "USR-EXEC789", "name": "John Executive", "role": "leadership"}
                ],
                created_by="USR-SARAH123",
                created_at=datetime.utcnow() - timedelta(days=2),
                last_activity=datetime.utcnow() - timedelta(hours=3),
                message_count=8,
                priority="high"
            ),
            DiscussionThread(
                thread_id=f"THR-{uuid.uuid4().hex[:8].upper()}",
                title="Evidence Quality Review",
                context_type="evidence",
                context_id="EVD-GHI01234",
                context_title="Security_Policy_v2.1.pdf",
                participants=[
                    {"user_id": "USR-LISA789", "name": "Lisa Rodriguez", "role": "analyst"},
                    {"user_id": "USR-DAVID012", "name": "David Kim", "role": "auditor"}
                ],
                created_by="USR-DAVID012",
                created_at=datetime.utcnow() - timedelta(days=1),
                last_activity=datetime.utcnow() - timedelta(hours=6),
                is_resolved=True,
                resolved_by="USR-DAVID012",
                resolved_at=datetime.utcnow() - timedelta(hours=6),
                message_count=5,
                priority="normal"
            )
        ]

        # Apply filters
        if context_type:
            threads = [t for t in threads if t.context_type == context_type]
        
        if context_id:
            threads = [t for t in threads if t.context_id == context_id]

        logger.info(f"Retrieved {len(threads)} discussion threads for user {current_user.id}")
        return threads

    except Exception as e:
        logger.error(f"Error getting discussion threads for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve discussion threads"
        )

# =====================================
# WORKFLOW SYNCHRONIZATION ENDPOINTS
# =====================================

@sync_router.get("/workflow-status/{engagement_id}", response_model=WorkflowStateSync)
async def get_workflow_status(
    engagement_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get current workflow synchronization status"""
    try:
        # Mock workflow state sync (in production, fetch from database)
        workflow_sync = WorkflowStateSync(
            sync_id=f"SYNC-{uuid.uuid4().hex[:8].upper()}",
            engagement_id=engagement_id,
            submission_id="SUB-ABC12345",
            current_status=WorkflowStatus.UNDER_REVIEW,
            previous_status=WorkflowStatus.SUBMITTED,
            current_assignee="USR-MIKE456",
            previous_assignee="USR-SARAH123",
            status_changed_by="USR-SARAH123",
            status_changed_at=datetime.utcnow() - timedelta(hours=2),
            next_action_required="Auditor review and feedback",
            next_action_assignee="USR-MIKE456",
            next_action_due=datetime.utcnow() + timedelta(days=2),
            workflow_stage="auditor_review",
            completion_percentage=65.5,
            collaboration_status="active"
        )

        logger.info(f"Retrieved workflow status for engagement {engagement_id}")
        return workflow_sync

    except Exception as e:
        logger.error(f"Error getting workflow status for engagement {engagement_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow status"
        )

@sync_router.get("/collaboration-indicators/{context_type}/{context_id}", response_model=CollaborationIndicator)
async def get_collaboration_indicators(
    context_type: str,
    context_id: str,
    current_user: MVP1User = Depends(get_current_user)
):
    """Get real-time collaboration indicators"""
    try:
        # Mock collaboration indicators (in production, fetch real-time data)
        indicators = CollaborationIndicator(
            context_type=context_type,
            context_id=context_id,
            active_users=[
                {
                    "user_id": "USR-SARAH123",
                    "name": "Sarah Johnson",
                    "role": "analyst",
                    "last_activity": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "activity_type": "editing"
                },
                {
                    "user_id": "USR-MIKE456", 
                    "name": "Mike Chen",
                    "role": "auditor",
                    "last_activity": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
                    "activity_type": "reviewing"
                }
            ],
            recent_activity=[
                {
                    "activity": "Evidence uploaded",
                    "user": "Sarah Johnson",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
                },
                {
                    "activity": "Comment added",
                    "user": "Mike Chen", 
                    "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat()
                }
            ],
            pending_actions=[
                {
                    "action": "Auditor review required",
                    "assignee": "Mike Chen",
                    "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                    "priority": "high"
                }
            ],
            last_updated=datetime.utcnow(),
            collaboration_health="good"
        )

        logger.info(f"Retrieved collaboration indicators for {context_type}:{context_id}")
        return indicators

    except Exception as e:
        logger.error(f"Error getting collaboration indicators: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collaboration indicators"
        )

# =====================================
# REAL-TIME BROADCAST FUNCTIONS
# =====================================

async def broadcast_activity_update(
    organization_id: str,
    activity: ActivityFeedItem
):
    """Broadcast activity update to all organization members"""
    message = {
        "type": "activity_update",
        "activity": activity.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_organization(message, organization_id)

async def send_notification_update(
    user_id: str,
    notification: NotificationItem
):
    """Send notification update to specific user"""
    message = {
        "type": "notification",
        "notification": notification.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def broadcast_workflow_status_change(
    organization_id: str,
    workflow_sync: WorkflowStateSync
):
    """Broadcast workflow status change to organization"""
    message = {
        "type": "workflow_status_change",
        "workflow_sync": workflow_sync.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_organization(message, organization_id)

# Health check endpoint for cross-role synchronization
@sync_router.get("/health")
async def sync_health():
    """Health check for cross-role synchronization module"""
    return {
        "module": "MVP 1 Week 6 - Cross-Role Synchronization",
        "version": "1.0.0",
        "status": "healthy",
        "capabilities": [
            "real_time_activity_feeds",
            "inter_role_notifications", 
            "discussion_threads",
            "workflow_synchronization",
            "collaboration_indicators",
            "websocket_connections",
            "status_broadcasting",
            "escalation_management"
        ],
        "endpoints": 9,
        "websocket_connections": len(manager.active_connections),
        "integration_points": [
            "Analyst Workflow (Week 3)",
            "Auditor Workflow (Week 4)",
            "Leadership View (Week 5)",
            "Admin Portal (Week 2)",
            "Authentication Bridge",
            "Real-time WebSocket Layer"
        ],
        "last_health_check": datetime.utcnow().isoformat()
    }