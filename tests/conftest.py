import os
import pytest
from unittest.mock import MagicMock
from peewee import SqliteDatabase
from fastapi.testclient import TestClient

import database
database.init_db = lambda: None

import main
import routers.events as events_router
import services.email_service as email_service
from auth import create_access_token, hash_password
from database import User, Location, Group, GroupMember, Event, Participant

TEST_DB_PATH = "/tmp/test_event_mgmt.db"
MODELS = [User, Location, Group, GroupMember, Event, Participant]


@pytest.fixture(autouse=True)
def test_db():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    db = SqliteDatabase(TEST_DB_PATH, pragmas={"foreign_keys": 1})
    db.bind(MODELS, bind_refs=False, bind_backrefs=False)
    db.connect(reuse_if_open=True)
    db.create_tables(MODELS)

    orig_db = database.db
    orig_events_db = events_router.db
    orig_main_db = main.db

    database.db = db
    events_router.db = db
    main.db = db

    yield db

    if not db.is_closed():
        db.close()

    database.db = orig_db
    events_router.db = orig_events_db
    main.db = orig_main_db

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_smtp_sender(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(email_service, "_send_calendar_messages_batch", mock)
    return mock


@pytest.fixture
def manager_user():
    user = User.create(
        name="Admin",
        surname="Manager",
        username="manager_test",
        email="manager@example.com",
        password_hash=hash_password("secret123"),
        role="manager"
    )
    token = create_access_token(user.id, user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return {"user": user, "token": token, "headers": headers}


@pytest.fixture
def employee_user():
    user = User.create(
        name="John",
        surname="Employee",
        username="employee_test",
        email="employee@example.com",
        password_hash=hash_password("secret123"),
        role="employee"
    )
    token = create_access_token(user.id, user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return {"user": user, "token": token, "headers": headers}


@pytest.fixture
def superadmin_user():
    user = User.create(
        name="Root",
        surname="Superadmin",
        username="superadmin_test",
        email="superadmin@example.com",
        password_hash=hash_password("secret123"),
        role="superadmin"
    )
    token = create_access_token(user.id, user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return {"user": user, "token": token, "headers": headers}

