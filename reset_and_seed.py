from datetime import datetime
from database import db, User, Location, Event, Participant, Group, GroupMember
from auth import hash_password

MODELS = [Participant, GroupMember, Event, Location, Group, User]

def reset_and_seed():
    db.connect(reuse_if_open=True)
    db.drop_tables(MODELS, safe=True, cascade=True)
    db.create_tables([User, Location, Event, Participant, Group, GroupMember], safe=True)

    pw_hash = hash_password("111222333")

    hex_user = User.create(
        name="Hex",
        surname="Manager",
        username="hex",
        email="hex@company.com",
        password_hash=pw_hash,
        role="manager"
    )
    john = User.create(
        name="John",
        surname="Miller",
        username="john_hr",
        email="john.miller@company.com",
        password_hash=pw_hash,
        role="employee"
    )
    alice = User.create(
        name="Alice",
        surname="Smith",
        username="alice_hq",
        email="alice.smith@company.com",
        password_hash=pw_hash,
        role="employee"
    )
    bob = User.create(
        name="Bob",
        surname="Taylor",
        username="bob_dev",
        email="bob.taylor@company.com",
        password_hash=pw_hash,
        role="employee"
    )

    all_grp = Group.create(name="All", description="All company employees and managers")
    mgr_grp = Group.create(name="Managers", description="All company managers and executives")
    hr_grp = Group.create(name="HR", description="Human Resources department")
    hq_grp = Group.create(name="HQ", description="Headquarters operations team")
    eng_grp = Group.create(name="Engineering", description="Product & Engineering team")

    for u in [hex_user, john, alice, bob]:
        GroupMember.create(group=all_grp.id, user=u.id)

    GroupMember.create(group=mgr_grp.id, user=hex_user.id)
    GroupMember.create(group=hr_grp.id, user=john.id)
    GroupMember.create(group=hq_grp.id, user=alice.id)
    GroupMember.create(group=eng_grp.id, user=bob.id)

    loc1 = Location.create(office_room="Conference Room A", max_occupancy=20)
    loc2 = Location.create(office_room="Meeting Room 1", max_occupancy=8)
    loc3 = Location.create(office_room="HQ Lounge", max_occupancy=15)

    ev1 = Event.create(
        title="Weekly Kickoff & Strategy",
        description="All-hands weekly sync to review key priorities and sprint goals.",
        location=loc1.id,
        group=all_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 25, 10, 0),
        end_time=datetime(2026, 11, 25, 12, 0),
        send_email_notification=False
    )
    ev2 = Event.create(
        title="HR Policy & Onboarding Review",
        description="Review updated recruitment pipeline and employee benefits.",
        location=loc2.id,
        group=hr_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 26, 11, 0),
        end_time=datetime(2026, 11, 26, 12, 30),
        send_email_notification=False
    )
    ev3 = Event.create(
        title="HQ Operations Workshop",
        description="Quarterly headquarters roadmap and infrastructure planning.",
        location=loc3.id,
        group=hq_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 27, 14, 0),
        end_time=datetime(2026, 11, 27, 17, 0),
        send_email_notification=False
    )
    ev4 = Event.create(
        title="Tech Architecture Sync",
        description="Database scaling discussion and API performance review.",
        location=None,
        group=eng_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 28, 15, 0),
        end_time=datetime(2026, 11, 28, 16, 0),
        send_email_notification=False
    )
    ev5 = Event.create(
        title="Management & Group Status",
        description="Leadership review of team milestones and weekly retrospectives.",
        location=loc2.id,
        group=mgr_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 29, 10, 0),
        end_time=datetime(2026, 11, 29, 11, 30),
        send_email_notification=False
    )
    ev6 = Event.create(
        title="Company Demo & Happy Hour",
        description="Showcase completed features, Q&A, and casual team mixer.",
        location=loc1.id,
        group=all_grp.id,
        creator=hex_user.id,
        start_time=datetime(2026, 11, 30, 16, 0),
        end_time=datetime(2026, 11, 30, 18, 0),
        send_email_notification=False
    )

    for ev, users in [
        (ev1, [hex_user, john, alice, bob]),
        (ev2, [hex_user, john]),
        (ev3, [hex_user, alice]),
        (ev4, [hex_user, bob]),
        (ev5, [hex_user]),
        (ev6, [hex_user, john, alice, bob])
    ]:
        for u in users:
            Participant.create(event=ev.id, user=u.id, status="accepted")

    if not db.is_closed():
        db.close()

if __name__ == "__main__":
    reset_and_seed()
