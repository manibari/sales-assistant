"""Nexus calendar router — meetings and reminders."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.calendar import (
    create_meeting, get_meeting, get_meetings_by_date, get_meetings_by_month,
    get_meetings_by_deal, update_meeting, complete_meeting, delete_meeting,
    create_reminder, get_reminders_by_date, get_reminders_by_month,
    resolve_reminder, get_pending_reminders,
)

router = APIRouter()


class MeetingCreate(BaseModel):
    deal_id: int
    title: str
    meeting_date: str
    participants_json: str | None = None
    location: str | None = None
    notes: str | None = None


class MeetingUpdate(BaseModel):
    title: str | None = None
    meeting_date: str | None = None
    participants_json: str | None = None
    location: str | None = None
    notes: str | None = None
    status: str | None = None


class ReminderCreate(BaseModel):
    due_date: str
    content: str
    reminder_type: str = "custom"
    deal_id: int | None = None


# --- Meetings ---

@router.get("/meetings")
def list_meetings(date: str | None = None, deal_id: int | None = None):
    if date:
        return get_meetings_by_date(date)
    if deal_id:
        return get_meetings_by_deal(deal_id)
    return []


@router.get("/meetings/month/{year}/{month}")
def meetings_by_month(year: int, month: int):
    return get_meetings_by_month(year, month)


@router.get("/meetings/{meeting_id}")
def read_meeting(meeting_id: int):
    meeting = get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


@router.post("/meetings", status_code=201)
def create_meeting_endpoint(body: MeetingCreate):
    return create_meeting(**body.model_dump())


@router.patch("/meetings/{meeting_id}")
def patch_meeting(meeting_id: int, body: MeetingUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_meeting(meeting_id, **fields)
    if not result:
        raise HTTPException(404, "Meeting not found")
    return result


@router.post("/meetings/{meeting_id}/complete")
def mark_complete(meeting_id: int):
    result = complete_meeting(meeting_id)
    if not result:
        raise HTTPException(404, "Meeting not found")
    return result


@router.delete("/meetings/{meeting_id}", status_code=204)
def remove_meeting(meeting_id: int):
    if not delete_meeting(meeting_id):
        raise HTTPException(404, "Meeting not found")


# --- Reminders ---

@router.get("/reminders")
def list_reminders(date: str | None = None):
    if date:
        return get_reminders_by_date(date)
    return get_pending_reminders()


@router.get("/reminders/month/{year}/{month}")
def reminders_by_month(year: int, month: int):
    return get_reminders_by_month(year, month)


@router.post("/reminders", status_code=201)
def create_reminder_endpoint(body: ReminderCreate):
    return create_reminder(**body.model_dump())


@router.post("/reminders/{reminder_id}/resolve")
def mark_resolved(reminder_id: int):
    result = resolve_reminder(reminder_id)
    if not result:
        raise HTTPException(404, "Reminder not found")
    return result
