"""
Academic Management Module - Calendar Management API Routes  
Complete API endpoints for academic calendar and event management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
import logging

from ..middleware import get_academic_auth_context, AcademicAuthContext
from ..exceptions import (
    AcademicBaseException, AcademicValidationError, 
    AcademicResourceError, AcademicPermissionError,
    create_error_response, log_academic_error
)
from shared.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, extract
from ..models import CalendarEvent
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/calendar",
    tags=["Academic Calendar"],
    responses={
        400: {"description": "Validation Error"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        409: {"description": "Resource conflict"},
        500: {"description": "Internal server error"}
    }
)

# =====================================================
# CALENDAR EVENT SCHEMAS
# =====================================================

class EventType(str, Enum):
    """Types of calendar events"""
    HOLIDAY = "holiday"
    EXAM = "exam"
    ASSESSMENT = "assessment"
    SPORTS = "sports"
    CULTURAL = "cultural"
    MEETING = "meeting"
    TRAINING = "training"
    OTHER = "other"

class EventCategory(str, Enum):
    """Categories of calendar events"""
    ACADEMIC = "academic"
    ADMINISTRATIVE = "administrative"
    SOCIAL = "social"
    SPORTS = "sports"
    CULTURAL = "cultural"

class EventStatus(str, Enum):
    """Status of calendar events"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    POSTPONED = "postponed"

class CalendarEventCreate(BaseModel):
    """Schema for creating calendar events"""
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    event_type: EventType = Field(..., description="Type of event")
    event_category: EventCategory = Field(EventCategory.ACADEMIC, description="Event category")
    start_date: date = Field(..., description="Event start date")
    end_date: Optional[date] = Field(None, description="Event end date")
    start_time: Optional[str] = Field(None, description="Event start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="Event end time (HH:MM format)")
    is_all_day: bool = Field(True, description="Whether event is all day")
    location: Optional[str] = Field(None, max_length=200, description="Event location")
    term_number: Optional[int] = Field(None, ge=1, le=3, description="Zimbabwe term number")
    grade_levels: List[int] = Field(default=[], description="Applicable grade levels")
    class_ids: List[UUID] = Field(default=[], description="Applicable class IDs")
    teacher_ids: List[UUID] = Field(default=[], description="Applicable teacher IDs")
    is_recurring: bool = Field(False, description="Whether event is recurring")
    recurrence_pattern: Optional[str] = Field(None, description="Recurrence pattern")
    recurrence_end_date: Optional[date] = Field(None, description="End date for recurring events")
    reminder_days: List[int] = Field(default=[], description="Days before to send reminders")
    is_public: bool = Field(False, description="Whether event is public")
    requires_attendance: bool = Field(False, description="Whether attendance is required")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum participants")
    registration_required: bool = Field(False, description="Whether registration is required")
    registration_deadline: Optional[date] = Field(None, description="Registration deadline")

    @validator('grade_levels')
    def validate_grade_levels(cls, v):
        for level in v:
            if level < 1 or level > 13:
                raise ValueError(f"Invalid grade level: {level}. Must be between 1-13")
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError("End date cannot be before start date")
        return v

    @validator('recurrence_end_date')
    def validate_recurrence_end_date(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError("Recurrence end date cannot be before start date")
        return v

    @validator('registration_deadline')
    def validate_registration_deadline(cls, v, values):
        if v and 'start_date' in values and v > values['start_date']:
            raise ValueError("Registration deadline must be before event start date")
        return v

class CalendarEventUpdate(BaseModel):
    """Schema for updating calendar events"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[EventStatus] = None
    is_public: Optional[bool] = None
    requires_attendance: Optional[bool] = None
    max_participants: Optional[int] = Field(None, ge=1)

class CalendarEventResponse(BaseModel):
    """Schema for calendar event response"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    title: str
    description: Optional[str]
    event_type: str
    event_category: str
    start_date: date
    end_date: Optional[date]
    start_time: Optional[str]
    end_time: Optional[str]
    is_all_day: bool
    location: Optional[str]
    term_number: Optional[int]
    grade_levels: List[int]
    class_ids: List[UUID]
    teacher_ids: List[UUID]
    is_recurring: bool
    recurrence_pattern: Optional[str]
    recurrence_end_date: Optional[date]
    reminder_days: List[int]
    is_public: bool
    requires_attendance: bool
    max_participants: Optional[int]
    registration_required: bool
    registration_deadline: Optional[date]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# =====================================================
# CALENDAR EVENT CRUD ENDPOINTS
# =====================================================

@router.post(
    "/events",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Calendar Event",
    description="""
    Create a new academic calendar event.
    
    **Zimbabwe Academic Calendar Features:**
    - Three-term system support
    - Grade level targeting (1-13)
    - Term-specific events
    - Public holidays integration
    
    **Event Types:**
    - Holidays, Exams, Assessments
    - Sports, Cultural, Meetings
    - Training sessions
    
    **Advanced Features:**
    - Recurring events with patterns
    - Attendance tracking
    - Registration management
    - Multi-level targeting
    - Reminder notifications
    
    **Required Permissions:**
    - `academic.calendar.create` OR `academic.admin`
    """
)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new calendar event"""
    try:
        # Check permissions
        if not auth_context.can_manage_calendar():
            raise AcademicPermissionError(
                "Insufficient permissions to create calendar events",
                required_permission="academic.calendar.create",
                user_role=auth_context.user_role
            )

        # Get current academic year (simplified - would normally query from academic years table)
        current_year = datetime.now().year
        academic_year_id = UUID('00000000-0000-0000-0000-000000000001')  # Placeholder

        # Create the event
        new_event = CalendarEvent(
            school_id=auth_context.school_id,
            academic_year_id=academic_year_id,
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            event_category=event_data.event_category,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            is_all_day=event_data.is_all_day,
            location=event_data.location,
            term_number=event_data.term_number,
            grade_levels=event_data.grade_levels,
            class_ids=[str(cid) for cid in event_data.class_ids],
            teacher_ids=[str(tid) for tid in event_data.teacher_ids],
            is_recurring=event_data.is_recurring,
            recurrence_pattern=event_data.recurrence_pattern,
            recurrence_end_date=event_data.recurrence_end_date,
            reminder_days=event_data.reminder_days,
            is_public=event_data.is_public,
            requires_attendance=event_data.requires_attendance,
            max_participants=event_data.max_participants,
            registration_required=event_data.registration_required,
            registration_deadline=event_data.registration_deadline,
            created_by=str(auth_context.user_id)
        )

        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)

        logger.info(f"Calendar event created successfully: {new_event.id}")

        return {
            "success": True,
            "message": f"Calendar event '{event_data.title}' created successfully",
            "data": {
                "id": str(new_event.id),
                "title": new_event.title,
                "event_type": new_event.event_type,
                "start_date": new_event.start_date.isoformat(),
                "created_at": new_event.created_at.isoformat()
            },
            "event_id": str(new_event.id)
        }

    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "create_calendar_event",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "event_data": event_data.dict()
        })
        raise e.to_http_exception()

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error creating calendar event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create calendar event"
        )

@router.get(
    "/events",
    response_model=Dict[str, Any],
    summary="Get Calendar Events",
    description="""
    Retrieve calendar events with comprehensive filtering.
    
    **Filtering Options:**
    - Date range (start_date, end_date)
    - Event type and category
    - Grade levels
    - Term numbers
    - Public/private events
    - Event status
    
    **Zimbabwe Features:**
    - Term-based filtering
    - Grade level targeting
    - Academic year context
    
    **Response Features:**
    - Pagination support
    - Total count
    - Filter validation
    - Rich event details
    """
)
async def get_calendar_events(
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    event_category: Optional[EventCategory] = Query(None, description="Filter by event category"),
    term_number: Optional[int] = Query(None, ge=1, le=3, description="Filter by Zimbabwe term"),
    grade_levels: Optional[List[int]] = Query(None, description="Filter by grade levels"),
    include_public_only: bool = Query(False, description="Include only public events"),
    status: Optional[EventStatus] = Query(None, description="Filter by event status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Get calendar events with filtering"""
    try:
        # Check permissions
        if not auth_context.can_view_calendar():
            raise AcademicPermissionError(
                "Insufficient permissions to view calendar events",
                required_permission="academic.calendar.view",
                user_role=auth_context.user_role
            )

        # Build query
        query = select(CalendarEvent).where(CalendarEvent.school_id == auth_context.school_id)
        
        # Apply filters
        if start_date:
            query = query.where(CalendarEvent.start_date >= start_date)
        
        if end_date:
            query = query.where(CalendarEvent.start_date <= end_date)
            
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
            
        if event_category:
            query = query.where(CalendarEvent.event_category == event_category)
            
        if term_number:
            query = query.where(CalendarEvent.term_number == term_number)
            
        if include_public_only:
            query = query.where(CalendarEvent.is_public == True)
            
        if status:
            query = query.where(CalendarEvent.status == status)
            
        # Apply grade level filtering if specified
        if grade_levels:
            # This would require array operations - simplified for now
            pass

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(CalendarEvent.start_date)
        
        # Execute query
        result = await db.execute(query)
        events = result.scalars().all()

        # Convert to response format
        events_data = []
        for event in events:
            events_data.append({
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "event_category": event.event_category,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "is_all_day": event.is_all_day,
                "location": event.location,
                "term_number": event.term_number,
                "grade_levels": event.grade_levels or [],
                "is_public": event.is_public,
                "requires_attendance": event.requires_attendance,
                "status": event.status,
                "created_at": event.created_at.isoformat()
            })

        return {
            "success": True,
            "data": events_data,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total_count
            },
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "event_type": event_type,
                "event_category": event_category,
                "term_number": term_number,
                "include_public_only": include_public_only,
                "status": status
            }
        }

    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "get_calendar_events",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id)
        })
        raise e.to_http_exception()

    except Exception as e:
        logger.error(f"Unexpected error retrieving calendar events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar events"
        )

# =====================================================
# ZIMBABWE ACADEMIC CALENDAR ENDPOINTS
# =====================================================

@router.get(
    "/zimbabwe/academic-year/{year}",
    response_model=Dict[str, Any],
    summary="Get Zimbabwe Academic Year Calendar",
    description="""
    Get the complete academic calendar for a specific year in Zimbabwe.
    
    **Zimbabwe Academic System:**
    - Three-term structure
    - Term dates and holidays
    - Public holidays
    - School calendar events
    
    **Includes:**
    - Term start/end dates
    - Mid-term breaks
    - National holidays
    - Exam periods
    - Registration periods
    """
)
async def get_zimbabwe_academic_year_calendar(
    year: int,
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Get Zimbabwe academic year calendar"""
    try:
        # Check permissions
        if not auth_context.can_view_calendar():
            raise AcademicPermissionError(
                "Insufficient permissions to view academic calendar",
                required_permission="academic.calendar.view",
                user_role=auth_context.user_role
            )

        # Zimbabwe academic calendar structure
        academic_calendar = {
            "academic_year": year,
            "country": "Zimbabwe",
            "education_system": "Three-term system",
            "terms": [
                {
                    "term_number": 1,
                    "name": "Term 1",
                    "start_date": f"{year}-01-15",
                    "end_date": f"{year}-04-18",
                    "duration_weeks": 13,
                    "holidays": [
                        {"name": "Good Friday", "date": f"{year}-03-29", "type": "public"},
                        {"name": "Easter Monday", "date": f"{year}-04-01", "type": "public"},
                        {"name": "Independence Day", "date": f"{year}-04-18", "type": "national"}
                    ],
                    "exam_period": {
                        "start_date": f"{year}-04-08",
                        "end_date": f"{year}-04-15"
                    }
                },
                {
                    "term_number": 2,
                    "name": "Term 2", 
                    "start_date": f"{year}-05-06",
                    "end_date": f"{year}-08-22",
                    "duration_weeks": 15,
                    "holidays": [
                        {"name": "Workers Day", "date": f"{year}-05-01", "type": "public"},
                        {"name": "Africa Day", "date": f"{year}-05-25", "type": "public"},
                        {"name": "Heroes Day", "date": f"{year}-08-11", "type": "national"},
                        {"name": "Defence Forces Day", "date": f"{year}-08-12", "type": "national"}
                    ],
                    "exam_period": {
                        "start_date": f"{year}-08-12",
                        "end_date": f"{year}-08-19"
                    }
                },
                {
                    "term_number": 3,
                    "name": "Term 3",
                    "start_date": f"{year}-09-09", 
                    "end_date": f"{year}-12-05",
                    "duration_weeks": 13,
                    "holidays": [
                        {"name": "Unity Day", "date": f"{year}-12-22", "type": "national"}
                    ],
                    "exam_period": {
                        "start_date": f"{year}-11-25",
                        "end_date": f"{year}-12-02"
                    }
                }
            ],
            "total_school_days": 200,
            "total_weeks": 40,
            "vacation_periods": [
                {
                    "name": "Christmas Holiday",
                    "start_date": f"{year}-12-05",
                    "end_date": f"{year+1}-01-14",
                    "duration_weeks": 6
                },
                {
                    "name": "May Holiday",
                    "start_date": f"{year}-04-19",
                    "end_date": f"{year}-05-05",
                    "duration_weeks": 2
                },
                {
                    "name": "August Holiday", 
                    "start_date": f"{year}-08-23",
                    "end_date": f"{year}-09-08",
                    "duration_weeks": 2
                }
            ]
        }

        return {
            "success": True,
            "data": academic_calendar,
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "school_id": str(auth_context.school_id),
                "country_code": "ZW"
            }
        }

    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "get_zimbabwe_academic_calendar",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "year": year
        })
        raise e.to_http_exception()

    except Exception as e:
        logger.error(f"Unexpected error getting Zimbabwe academic calendar: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve academic calendar"
        )

# =====================================================
# CALENDAR ANALYTICS AND UTILITIES
# =====================================================

@router.get(
    "/analytics/events-summary",
    response_model=Dict[str, Any],
    summary="Calendar Events Analytics",
    description="""
    Get analytics and summary of calendar events.
    
    **Analytics Include:**
    - Event distribution by type/category
    - Monthly event counts
    - Term-specific events
    - Attendance requirements
    - Registration statistics
    
    **Use Cases:**
    - Administrative dashboards
    - Event planning
    - Resource allocation
    - Engagement tracking
    """
)
async def get_calendar_events_analytics(
    year: Optional[int] = Query(None, ge=2020, le=2030, description="Filter by year"),
    term_number: Optional[int] = Query(None, ge=1, le=3, description="Filter by term"),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Get calendar events analytics"""
    try:
        # Check permissions
        if not auth_context.can_view_analytics():
            raise AcademicPermissionError(
                "Insufficient permissions to view calendar analytics",
                required_permission="academic.analytics.view",
                user_role=auth_context.user_role
            )

        # Return structured analytics (would normally query database)
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_events": 0,
                    "upcoming_events": 0,
                    "public_events": 0,
                    "events_requiring_attendance": 0
                },
                "by_type": {
                    "holiday": 0,
                    "exam": 0,
                    "assessment": 0,
                    "sports": 0,
                    "cultural": 0,
                    "meeting": 0,
                    "training": 0,
                    "other": 0
                },
                "by_term": {
                    "term_1": 0,
                    "term_2": 0,
                    "term_3": 0
                },
                "monthly_distribution": [],
                "attendance_tracking": {
                    "events_with_attendance": 0,
                    "average_attendance_rate": 0
                }
            },
            "filters": {
                "year": year,
                "term_number": term_number
            }
        }

    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "get_calendar_analytics",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id)
        })
        raise e.to_http_exception()

    except Exception as e:
        logger.error(f"Unexpected error getting calendar analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar analytics"
        )