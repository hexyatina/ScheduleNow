from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from routers import users, events, locations, groups
from database import init_db, db, get_all_events_with_details, Event


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Event Management API", lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    db.connect(reuse_if_open=True)
    try:
        response = await call_next(request)
    finally:
        if not db.is_closed():
            db.close()
    return response

@app.get("/")
def root():
    return RedirectResponse(url="/calendar")

@app.get("/calendar")
def calendar(
    request: Request,
    week_start: str | None = None,
    date: str | None = None
):
    today = datetime.now().date()
    target_date = today

    param_val = week_start or date
    if param_val:
        try:
            target_date = datetime.strptime(param_val, "%Y-%m-%d").date()
        except ValueError:
            target_date = today

    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)

    prev_week_monday = monday - timedelta(days=7)
    next_week_monday = monday + timedelta(days=7)
    current_week_monday = today - timedelta(days=today.weekday())
    is_current_week = (monday == current_week_monday)

    prev_week_str = prev_week_monday.strftime("%Y-%m-%d")
    next_week_str = next_week_monday.strftime("%Y-%m-%d")
    current_week_str = current_week_monday.strftime("%Y-%m-%d")

    if monday.year == sunday.year:
        if monday.month == sunday.month:
            week_range_label = f"{monday.strftime('%d')} – {sunday.strftime('%d %b %Y')}"
        else:
            week_range_label = f"{monday.strftime('%d %b')} – {sunday.strftime('%d %b %Y')}"
    else:
        week_range_label = f"{monday.strftime('%d %b %Y')} – {sunday.strftime('%d %b %Y')}"

    day_meta = [
        ("M", "Mon"),
        ("T", "Tue"),
        ("W", "Wed"),
        ("TH", "Thu"),
        ("F", "Fri"),
        ("SA", "Sat"),
        ("SU", "Sun"),
    ]

    days = []
    for i, (code, name) in enumerate(day_meta):
        day_date = monday + timedelta(days=i)
        days.append({
            "code": code,
            "name": name,
            "date_str": day_date.strftime("%d %b"),
            "date_iso": day_date.strftime("%Y-%m-%d"),
            "is_today": (day_date == today),
        })

    hours = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

    start_dt = datetime.combine(monday, datetime.min.time())
    end_dt = datetime.combine(sunday, datetime.max.time())

    week_events = list(
        get_all_events_with_details()
        .where((Event.start_time <= end_dt) & (Event.end_time >= start_dt))
    )

    day_events_map = {d["date_iso"]: [] for d in days}
    for ev in week_events:
        date_iso = ev.start_time.strftime("%Y-%m-%d")
        if date_iso in day_events_map:
            s_hour = ev.start_time.hour + ev.start_time.minute / 60.0
            e_hour = ev.end_time.hour + ev.end_time.minute / 60.0

            vis_start = max(10.0, min(19.0, s_hour))
            vis_end = max(10.0, min(19.0, e_hour))

            duration = max(0.25, vis_end - vis_start)
            offset = max(0.0, vis_start - 10.0)

            ev.left_pct = round((offset / 9.0) * 100.0, 2)
            ev.width_pct = round((duration / 9.0) * 100.0, 2)
            day_events_map[date_iso].append(ev)

    for date_iso, ev_list in day_events_map.items():
        ev_list.sort(key=lambda x: x.start_time)
        tracks_end_time = []
        for ev in ev_list:
            assigned = False
            for track_idx, end_t in enumerate(tracks_end_time):
                if ev.start_time >= end_t:
                    tracks_end_time[track_idx] = ev.end_time
                    ev.track_index = track_idx
                    assigned = True
                    break
            if not assigned:
                ev.track_index = len(tracks_end_time)
                tracks_end_time.append(ev.end_time)

        num_tracks = max(1, len(tracks_end_time))
        for ev in ev_list:
            ev.total_tracks = num_tracks

    return templates.TemplateResponse(
        request=request,
        name="calendar.html",
        context={
            "user_name": "hex",
            "days": days,
            "hours": hours,
            "day_events_map": day_events_map,
            "week_range_label": week_range_label,
            "prev_week_str": prev_week_str,
            "next_week_str": next_week_str,
            "current_week_str": current_week_str,
            "is_current_week": is_current_week,
            "current_monday_str": monday.strftime("%Y-%m-%d"),
        }
    )
app.include_router(users.router)
app.include_router(events.router)
app.include_router(locations.router)
app.include_router(groups.router)