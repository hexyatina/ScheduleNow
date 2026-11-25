from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event as ICalEvent

KYIV_TZ = ZoneInfo("Europe/Kyiv")


def generate_event_ics(
    event_id: int,
    title: str,
    description: str | None,
    start_time: datetime,
    end_time: datetime,
    location: str | None = None,
    sequence: int = 0,
    status: str = "CONFIRMED",
    method: str = "REQUEST"
) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//ScheduleNow Team//UA")
    cal.add("version", "2.0")
    cal.add("method", method)

    if start_time.tzinfo is None:
        start_utc = start_time.replace(tzinfo=KYIV_TZ).astimezone(timezone.utc)
        end_utc = end_time.replace(tzinfo=KYIV_TZ).astimezone(timezone.utc)
    else:
        start_utc = start_time.astimezone(timezone.utc)
        end_utc = end_time.astimezone(timezone.utc)

    event = ICalEvent()
    event.add("uid", f"event-{event_id}@schedulenow.local")
    event.add("summary", title)
    event.add("description", description or "")
    event.add("dtstart", start_utc)
    event.add("dtend", end_utc)
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("status", status)
    event.add("sequence", sequence)

    if location:
        event.add("location", location)

    cal.add_component(event)
    return cal.to_ical()

def round_time(dt: datetime, step_minutes: int = 15) -> datetime:
    dt = dt.replace(second=0, microsecond=0)
    remainder = dt.minute % step_minutes
    if remainder >= step_minutes / 2:
        dt += timedelta(minutes=(step_minutes - remainder))
    else:
        dt -= timedelta(minutes=remainder)
    return dt