from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from auth import get_current_user, require_manager
from database import db, Event, Group, GroupMember, Location, Participant, User, get_all_events_with_details
from schemas import CreateEvent, UpdateEvent
from services.email_service import (
    send_event_cancelled_email,
    send_event_email,
    send_event_updated_email,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/createEvent")
def create_event(
    data: CreateEvent,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_manager)
):
    room_name = None
    loc_id = data.location_id if (data.location_id is not None and data.location_id != 0) else None

    if data.group_id is not None and data.group_id != 0:
        group_exists = Group.select().where(Group.id == data.group_id).exists()
        if not group_exists:
            raise HTTPException(status_code=404, detail="Recipient group not found")

    with db.atomic():
        if loc_id is not None:
            location = Location.get_or_none(Location.id == loc_id)
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
            room_name = location.office_room

            is_occupied = Event.select().where(
                (Event.location == loc_id) &
                (Event.start_time < data.end_time) &
                (Event.end_time > data.start_time)
            ).exists()

            if is_occupied:
                raise HTTPException(
                    status_code=400,
                    detail="Office room is already occupied during this time interval"
                )

        grp_id = data.group_id if (data.group_id is not None and data.group_id != 0) else None
        new_event = Event.create(
            title=data.title,
            description=data.description,
            location=loc_id,
            group=grp_id,
            creator=current_user.id,
            start_time=data.start_time,
            end_time=data.end_time,
            send_email_notification=data.send_email_notification
        )

    if data.group_id is not None and data.group_id != 0:
        members = (
            GroupMember.select(GroupMember, User)
            .join(User, on=(GroupMember.user == User.id))
            .where(GroupMember.group == data.group_id)
        )

        recipient_emails = []
        for member in members:
            Participant.get_or_create(
                event=new_event.id,
                user=member.user.id,
                defaults={"status": "invited"}
            )
            if member.user.email:
                recipient_emails.append(member.user.email)

        if data.send_email_notification and recipient_emails:
            background_tasks.add_task(
                send_event_email,
                recipients=recipient_emails,
                event_id=new_event.id,
                event_title=new_event.title,
                description=new_event.description,
                start_time=new_event.start_time,
                end_time=new_event.end_time,
                room_name=room_name
            )

    return {"message": "Event created", "event_id": new_event.id}


@router.patch("/{event_id}")
def update_event(
    event_id: int,
    data: UpdateEvent,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_manager)
):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this event")

    new_start = data.start_time if data.start_time is not None else event.start_time
    new_end = data.end_time if data.end_time is not None else event.end_time
    new_location_id = data.location_id if data.location_id is not None else event.location_id

    if new_start >= new_end:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    room_name = event.location.office_room if (event.location_id and event.location_id != 0) else None

    with db.atomic():
        if new_location_id is not None and new_location_id != 0:
            location = Location.get_or_none(Location.id == new_location_id)
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
            room_name = location.office_room

            is_occupied = Event.select().where(
                (Event.id != event.id) &
                (Event.location == new_location_id) &
                (Event.start_time < new_end) &
                (Event.end_time > new_start)
            ).exists()

            if is_occupied:
                raise HTTPException(
                    status_code=400,
                    detail="Office room is already occupied during this time interval"
                )
        elif new_location_id == 0:
            room_name = None

        if data.title is not None:
            event.title = data.title
        if data.description is not None:
            event.description = data.description
        if data.location_id is not None:
            event.location = data.location_id if data.location_id != 0 else None
        if data.start_time is not None:
            event.start_time = data.start_time
        if data.end_time is not None:
            event.end_time = data.end_time

        event.save()

    if event.send_email_notification:
        participants = (
            Participant.select(Participant, User)
            .join(User, on=(Participant.user == User.id))
            .where(Participant.event == event.id)
        )
        recipient_emails = [p.user.email for p in participants if p.user.email]
        if recipient_emails:
            background_tasks.add_task(
                send_event_updated_email,
                recipients=recipient_emails,
                event_id=event.id,
                event_title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                room_name=room_name
            )
    return {"message": "Event updated successfully", "event_id": event.id}


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_manager)
):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this event")

    if event.send_email_notification:
        participants = (
            Participant.select(Participant, User)
            .join(User, on=(Participant.user == User.id))
            .where(Participant.event == event.id)
        )
        recipient_emails = [p.user.email for p in participants if p.user.email]
        if recipient_emails:
            background_tasks.add_task(
                send_event_cancelled_email,
                recipients=recipient_emails,
                event_id=event.id,
                event_title=event.title,
                start_time=event.start_time,
                end_time=event.end_time
            )
    with db.atomic():
        Participant.delete().where(Participant.event == event_id).execute()
        event.delete_instance()

    return {"message": "Event deleted successfully"}


@router.get("/")
def read_events(current_user: User = Depends(get_current_user)):
    events = get_all_events_with_details()
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location.office_room if event.location else None,
            "creator": f"{event.creator.name} {event.creator.surname}",
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
        }
        for event in events
    ]


@router.get("/calendar")
def get_calendar_events(
    start: datetime,
    end: datetime,
    current_user: User = Depends(get_current_user)
):
    events = Event.select().where(
        (Event.start_time < end) & (Event.end_time > start)
    )

    return [
        {
            "id": event.id,
            "title": event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat(),
            "location": event.location.office_room if event.location else "Онлайн",
            "description": event.description
        }
        for event in events
    ]

@router.get("/{event_id}")
def read_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "location": event.location.office_room if (event.location_id and event.location_id != 0) else None,
        "creator": f"{event.creator.name} {event.creator.surname}",
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
        "send_email_notification": event.send_email_notification
    }


@router.post("/{event_id}/join")
def join_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    already_joined = Participant.select().where(
        (Participant.event == event_id) &
        (Participant.user == current_user.id)
    ).exists()
    if already_joined:
        raise HTTPException(status_code=400, detail="User has already joined this event")

    if event.group_id:
        group = Group.get_or_none(Group.id == event.group_id)
        if group and group.name.lower() != "all":
            is_member = GroupMember.select().where(
                (GroupMember.group == event.group_id) &
                (GroupMember.user == current_user.id)
            ).exists()
            if not is_member:
                raise HTTPException(
                    status_code=403,
                    detail=f"This event is restricted to members of the '{group.name}' group"
                )

    if event.location_id and event.location_id != 0:
        current_participant_count = Participant.select().where(
            Participant.event == event_id
        ).count()

        if current_participant_count >= event.location.max_occupancy:
            raise HTTPException(status_code=400, detail="Office room has reached maximum capacity")

    participant = Participant.create(
        event=event_id,
        user=current_user.id,
        status="accepted"
    )
    return {
        "message": "Successfully joined the event",
        "participant_id": participant.id
    }


@router.post("/{event_id}/leave")
def leave_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    participant = Participant.get_or_none(
        (Participant.event == event_id) &
        (Participant.user == current_user.id)
    )
    if not participant:
        raise HTTPException(status_code=400, detail="User has not joined this event")

    participant.delete_instance()
    return {
        "message": "Successfully left the event",
    }


@router.get("/{event_id}/participants")
def get_event_participants(
    event_id: int,
    current_user: User = Depends(get_current_user)
):
    event = Event.get_or_none(Event.id == event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    participants = (
        Participant.select(Participant, User)
        .join(User, on=(Participant.user == User.id))
        .where(Participant.event == event_id)
    )

    result = [
        {
            "id": p.user.id,
            "name": p.user.name,
            "surname": p.user.surname,
            "email": p.user.email,
            "role": p.user.role,
            "status": p.status
        }
        for p in participants
    ]

    return {
        "event_id": event.id,
        "event_title": event.title,
        "total_participants": len(result),
        "participants": result
    }