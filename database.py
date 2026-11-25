import time
from datetime import datetime, timedelta
from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    OperationalError,
    PostgresqlDatabase,
    TextField,
    JOIN
)
from config import settings

db = PostgresqlDatabase(
    settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
)


def get_default_end_time():
    return datetime.now() + timedelta(hours=2)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField(max_length=100)
    surname = CharField(max_length=100)
    username = CharField(unique=True, max_length=50)
    email = CharField(unique=True, max_length=100)
    password_hash = CharField(max_length=255)
    role = CharField(default="employee")  # 'manager' or 'employee'
    created_at = DateTimeField(default=datetime.now)


class Location(BaseModel):
    office_room = CharField(max_length=100)
    max_occupancy = IntegerField(default=10)


class Group(BaseModel):
    name = CharField(unique=True, max_length=100)
    description = TextField(null=True)


class GroupMember(BaseModel):
    group = ForeignKeyField(Group, backref="members", on_delete="CASCADE")
    user = ForeignKeyField(User, backref="group_memberships", on_delete="CASCADE")

    class Meta:
        indexes = ((("group", "user"), True),)


class Event(BaseModel):
    title = CharField(max_length=150)
    description = TextField(null=True)
    location = ForeignKeyField(Location, backref="events", null=True, on_delete="SET NULL")
    group = ForeignKeyField(Group, backref="events", null=True, on_delete="SET NULL")
    creator = ForeignKeyField(User, backref="created_events", on_delete="CASCADE")
    start_time = DateTimeField(default=datetime.now)
    end_time = DateTimeField(default=get_default_end_time)
    send_email_notification = BooleanField(default=False)


class Participant(BaseModel):
    event = ForeignKeyField(Event, backref="participants", on_delete="CASCADE")
    user = ForeignKeyField(User, backref="participations", on_delete="CASCADE")
    status = CharField(default="invited")  # invited, accepted, declined

    class Meta:
        indexes = ((("event", "user"), True),)


def get_all_events_with_details():
    return (
        Event.select(Event, Location, User, Group)
        .join(Location, JOIN.LEFT_OUTER)
        .switch(Event)
        .join(User)
        .switch(Event)
        .join(Group, JOIN.LEFT_OUTER)
    )


def ensure_all_group():
    all_group, _ = Group.get_or_create(
        name="All",
        defaults={"description": "All company employees and managers"}
    )
    users = User.select()
    for u in users:
        GroupMember.get_or_create(group=all_group.id, user=u.id)
    return all_group


def ensure_managers_group():
    managers_group, _ = Group.get_or_create(
        name="Managers",
        defaults={"description": "All company managers and executives"}
    )
    managers = User.select().where(User.role.in_(["manager", "superadmin"]))
    for m in managers:
        GroupMember.get_or_create(group=managers_group.id, user=m.id)
    return managers_group


def init_db(retries: int = 5, delay: float = 1.0):
    for attempt in range(1, retries + 1):
        try:
            db.connect(reuse_if_open=True)
            break
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)

    db.create_tables([User, Location, Group, GroupMember, Event, Participant], safe=True)
    try:
        db.execute_sql('ALTER TABLE "event" ADD COLUMN IF NOT EXISTS "group_id" INTEGER REFERENCES "group" ("id") ON DELETE SET NULL;')
    except Exception:
        pass
    ensure_all_group()
    ensure_managers_group()
    if not db.is_closed():
        db.close()


if __name__ == "__main__":
    init_db()