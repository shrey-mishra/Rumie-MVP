from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Dict, Any

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("integrations_router")

@router.get("/google/{user_id}")
@limiter.limit("10/minute")
def get_google_workspace_mock(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Mock Google Workspace integration - Gmail and Calendar data"""
    logger.info("Fetching Google Workspace data", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Google Workspace request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock Gmail data
    gmail_data = [
        {
            "id": "msg_001",
            "subject": "Urgent: Project Deadline Update",
            "sender": "manager@company.com",
            "timestamp": "2025-09-29T10:30:00Z",
            "priority": "high",
            "unread": True
        },
        {
            "id": "msg_002", 
            "subject": "Weekly Team Standup",
            "sender": "team@company.com",
            "timestamp": "2025-09-29T09:15:00Z",
            "priority": "medium",
            "unread": False
        },
        {
            "id": "msg_003",
            "subject": "Meeting Notes from Yesterday",
            "sender": "colleague@company.com", 
            "timestamp": "2025-09-29T08:45:00Z",
            "priority": "low",
            "unread": True
        }
    ]
    
    # Mock Calendar data
    calendar_data = [
        {
            "id": "event_001",
            "title": "Project Review Meeting",
            "start_time": "2025-09-29T15:00:00Z",
            "end_time": "2025-09-29T16:00:00Z",
            "attendees": ["manager@company.com", "team@company.com"],
            "location": "Conference Room A",
            "status": "confirmed"
        },
        {
            "id": "event_002",
            "title": "Client Presentation Prep",
            "start_time": "2025-09-29T14:00:00Z", 
            "end_time": "2025-09-29T14:30:00Z",
            "attendees": ["user@company.com"],
            "location": "Office",
            "status": "tentative"
        }
    ]
    
    logger.info("Google Workspace data retrieved", user_id=user_id, gmail_count=len(gmail_data), calendar_count=len(calendar_data))
    
    return {
        "user_id": user_id,
        "gmail": gmail_data,
        "calendar": calendar_data,
        "last_sync": "2025-09-29T10:30:00Z",
        "status": "connected"
    }

@router.get("/notion/{user_id}")
@limiter.limit("10/minute")
def get_notion_mock(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Mock Notion integration - Tasks and Notes data"""
    logger.info("Fetching Notion data", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Notion request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock Tasks data
    tasks_data = [
        {
            "id": "task_001",
            "title": "Finish MVP Development",
            "description": "Complete the core features for Phase II",
            "due_date": "2025-09-30T17:00:00Z",
            "priority": "high",
            "status": "in_progress",
            "assignee": "user@company.com",
            "tags": ["development", "mvp"]
        },
        {
            "id": "task_002",
            "title": "Prepare Client Presentation",
            "description": "Create slides for the quarterly review",
            "due_date": "2025-10-01T12:00:00Z",
            "priority": "medium",
            "status": "todo",
            "assignee": "user@company.com",
            "tags": ["presentation", "client"]
        },
        {
            "id": "task_003",
            "title": "Code Review Session",
            "description": "Review team member's pull request",
            "due_date": "2025-09-29T16:00:00Z",
            "priority": "low",
            "status": "completed",
            "assignee": "user@company.com",
            "tags": ["code-review", "team"]
        }
    ]
    
    # Mock Notes data
    notes_data = [
        {
            "id": "note_001",
            "title": "Meeting Notes - Project Planning",
            "content": "Discussed timeline for Q4 deliverables. Key milestones identified.",
            "created_at": "2025-09-29T09:00:00Z",
            "updated_at": "2025-09-29T09:30:00Z",
            "tags": ["meeting", "planning"],
            "shared_with": ["team@company.com"]
        },
        {
            "id": "note_002",
            "title": "Technical Architecture Decisions",
            "content": "Decided on microservices architecture. Database schema finalized.",
            "created_at": "2025-09-28T14:00:00Z",
            "updated_at": "2025-09-28T15:00:00Z",
            "tags": ["technical", "architecture"],
            "shared_with": ["tech-lead@company.com"]
        }
    ]
    
    logger.info("Notion data retrieved", user_id=user_id, tasks_count=len(tasks_data), notes_count=len(notes_data))
    
    return {
        "user_id": user_id,
        "tasks": tasks_data,
        "notes": notes_data,
        "last_sync": "2025-09-29T10:30:00Z",
        "status": "connected"
    }

@router.get("/status/{user_id}")
@limiter.limit("20/minute")
def get_integrations_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get status of all integrations for a user"""
    logger.info("Checking integration status", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Integration status check failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock integration statuses
    integrations_status = {
        "user_id": user_id,
        "integrations": {
            "google_workspace": {
                "connected": True,
                "last_sync": "2025-09-29T10:30:00Z",
                "services": ["gmail", "calendar", "drive"],
                "status": "active"
            },
            "notion": {
                "connected": True,
                "last_sync": "2025-09-29T10:30:00Z",
                "services": ["tasks", "notes", "pages"],
                "status": "active"
            },
            "slack": {
                "connected": False,
                "last_sync": None,
                "services": [],
                "status": "disconnected"
            }
        },
        "overall_status": "partial"
    }
    
    logger.info("Integration status retrieved", user_id=user_id, active_integrations=2)
    
    return integrations_status
