from datetime import datetime, timedelta


def test_create_event_success(client, manager_user):
    # 1. Create a location first
    loc_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Main Room", "max_occupancy": 10}
    )
    loc_id = loc_res.json()["location_id"]

    # 2. Create event
    response = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Strategy Meeting",
            "description": "Discuss Q4 goals",
            "location_id": loc_id,
            "start_time": "2026-11-20T10:00:00",
            "end_time": "2026-11-20T11:00:00",
            "send_email_notification": False
        }
    )
    assert response.status_code == 200
    assert "event_id" in response.json()


def test_create_event_forbidden_for_employee(client, employee_user):
    response = client.post(
        "/events/createEvent",
        headers=employee_user["headers"],
        json={
            "title": "Employee Meeting",
            "start_time": "2026-11-20T10:00:00",
            "end_time": "2026-11-20T11:00:00"
        }
    )
    assert response.status_code == 403


def test_create_event_room_collision(client, manager_user):
    loc_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Collision Room", "max_occupancy": 5}
    )
    loc_id = loc_res.json()["location_id"]

    # First event: 12:00 to 14:00
    res1 = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "First Event",
            "location_id": loc_id,
            "start_time": "2026-11-20T12:00:00",
            "end_time": "2026-11-20T14:00:00"
        }
    )
    assert res1.status_code == 200

    # Overlapping event: 13:00 to 15:00
    res2 = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Overlapping Event",
            "location_id": loc_id,
            "start_time": "2026-11-20T13:00:00",
            "end_time": "2026-11-20T15:00:00"
        }
    )
    assert res2.status_code == 400
    assert "already occupied" in res2.json()["detail"]


def test_read_events_and_calendar(client, manager_user, employee_user):
    # Create offline event
    client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "All Hands",
            "start_time": "2026-11-25T10:00:00",
            "end_time": "2026-11-25T11:00:00"
        }
    )

    # 1. Read events list
    res_list = client.get("/events/", headers=employee_user["headers"])
    assert res_list.status_code == 200
    events = res_list.json()
    assert len(events) >= 1
    assert any(e["title"] == "All Hands" for e in events)

    # 2. Read calendar range
    cal_res = client.get(
        "/events/calendar?start=2026-11-25T00:00:00&end=2026-11-25T23:59:59",
        headers=employee_user["headers"]
    )
    assert cal_res.status_code == 200
    cal_events = cal_res.json()
    assert any(e["title"] == "All Hands" for e in cal_events)


def test_join_and_leave_event(client, manager_user, employee_user):
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Sync Meeting",
            "start_time": "2026-11-26T10:00:00",
            "end_time": "2026-11-26T11:00:00"
        }
    )
    event_id = create_res.json()["event_id"]

    # Join
    join_res = client.post(f"/events/{event_id}/join", headers=employee_user["headers"])
    assert join_res.status_code == 200
    assert "Successfully joined" in join_res.json()["message"]

    # Cannot join twice
    dup_join = client.post(f"/events/{event_id}/join", headers=employee_user["headers"])
    assert dup_join.status_code == 400
    assert "already joined" in dup_join.json()["detail"]

    # Leave
    leave_res = client.post(f"/events/{event_id}/leave", headers=employee_user["headers"])
    assert leave_res.status_code == 200
    assert "Successfully left" in leave_res.json()["message"]


def test_join_event_restricted_by_group(client, manager_user, employee_user):
    # 1. Create a specific group (e.g. "Exclusive Group")
    grp_res = client.post(
        "/groups/",
        headers=manager_user["headers"],
        json={"name": "Exclusive Group", "description": "Managers only"}
    )
    assert grp_res.status_code == 200
    group_id = grp_res.json()["group_id"]

    # 2. Add manager to this group, but NOT employee
    client.post(
        f"/groups/{group_id}/members",
        headers=manager_user["headers"],
        json={"user_id": manager_user["user"].id}
    )

    # 3. Create an event bound to this group
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Exclusive Meeting",
            "group_id": group_id,
            "start_time": "2026-11-27T10:00:00",
            "end_time": "2026-11-27T11:00:00"
        }
    )
    assert create_res.status_code == 200
    event_id = create_res.json()["event_id"]

    # 4. Employee tries to join -> forbidden 403
    emp_join = client.post(f"/events/{event_id}/join", headers=employee_user["headers"])
    assert emp_join.status_code == 403
    assert "restricted to members of the 'Exclusive Group' group" in emp_join.json()["detail"]


def test_delete_event(client, manager_user):
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Event to Delete",
            "start_time": "2026-11-27T10:00:00",
            "end_time": "2026-11-27T11:00:00"
        }
    )
    event_id = create_res.json()["event_id"]

    del_res = client.delete(f"/events/{event_id}", headers=manager_user["headers"])
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # Check that it is gone
    get_res = client.get(f"/events/{event_id}", headers=manager_user["headers"])
    assert get_res.status_code == 404


def test_update_event_success(client, manager_user):
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Original Title",
            "description": "Original Description",
            "start_time": "2026-11-28T10:00:00",
            "end_time": "2026-11-28T11:00:00"
        }
    )
    event_id = create_res.json()["event_id"]

    patch_res = client.patch(
        f"/events/{event_id}",
        headers=manager_user["headers"],
        json={
            "title": "Updated Title",
            "description": "Updated Description"
        }
    )
    assert patch_res.status_code == 200
    assert "updated successfully" in patch_res.json()["message"]

    # Verify updated fields
    get_res = client.get(f"/events/{event_id}", headers=manager_user["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Updated Title"
    assert get_res.json()["description"] == "Updated Description"


def test_update_event_forbidden_for_employee(client, manager_user, employee_user):
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Manager Meeting",
            "start_time": "2026-11-29T10:00:00",
            "end_time": "2026-11-29T11:00:00"
        }
    )
    event_id = create_res.json()["event_id"]

    patch_res = client.patch(
        f"/events/{event_id}",
        headers=employee_user["headers"],
        json={"title": "Hacked Title"}
    )
    assert patch_res.status_code == 403
    assert "Only managers can perform this action" in patch_res.json()["detail"]


def test_delete_event_forbidden_for_employee(client, manager_user, employee_user):
    create_res = client.post(
        "/events/createEvent",
        headers=manager_user["headers"],
        json={
            "title": "Manager Meeting 2",
            "start_time": "2026-11-30T10:00:00",
            "end_time": "2026-11-30T11:00:00"
        }
    )
    event_id = create_res.json()["event_id"]

    del_res = client.delete(f"/events/{event_id}", headers=employee_user["headers"])
    assert del_res.status_code == 403
    assert "Only managers can perform this action" in del_res.json()["detail"]
