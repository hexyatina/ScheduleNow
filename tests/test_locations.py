def test_create_location_success(client, manager_user):
    response = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Conference Room A", "max_occupancy": 15}
    )
    assert response.status_code == 200
    data = response.json()
    assert "location_id" in data


def test_create_location_forbidden_for_employee(client, employee_user):
    response = client.post(
        "/locations/",
        headers=employee_user["headers"],
        json={"office_room": "Conf Room B", "max_occupancy": 10}
    )
    assert response.status_code == 403


def test_create_location_invalid_occupancy(client, manager_user):
    response = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Zero Room", "max_occupancy": 0}
    )
    assert response.status_code == 400
    assert "greater than zero" in response.json()["detail"]


def test_create_duplicate_location(client, manager_user):
    client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Unique Room", "max_occupancy": 5}
    )
    dup_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Unique Room", "max_occupancy": 8}
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


def test_get_locations(client, employee_user, manager_user):
    client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Room 101", "max_occupancy": 10}
    )
    response = client.get("/locations/", headers=employee_user["headers"])
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) >= 1
    assert any(loc["office_room"] == "Room 101" for loc in locations)


def test_update_location_success(client, manager_user):
    create_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Old Room", "max_occupancy": 8}
    )
    loc_id = create_res.json()["location_id"]

    patch_res = client.patch(
        f"/locations/{loc_id}",
        headers=manager_user["headers"],
        json={"office_room": "Renovated Room", "max_occupancy": 16}
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["location"]["office_room"] == "Renovated Room"
    assert data["location"]["max_occupancy"] == 16


def test_update_location_forbidden_for_employee(client, manager_user, employee_user):
    create_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Manager Room", "max_occupancy": 6}
    )
    loc_id = create_res.json()["location_id"]

    patch_res = client.patch(
        f"/locations/{loc_id}",
        headers=employee_user["headers"],
        json={"max_occupancy": 20}
    )
    assert patch_res.status_code == 403
    assert "Only managers can perform this action" in patch_res.json()["detail"]


def test_update_location_invalid_occupancy(client, manager_user):
    create_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Small Room", "max_occupancy": 4}
    )
    loc_id = create_res.json()["location_id"]

    patch_res = client.patch(
        f"/locations/{loc_id}",
        headers=manager_user["headers"],
        json={"max_occupancy": 0}
    )
    assert patch_res.status_code == 400
    assert "greater than zero" in patch_res.json()["detail"]


def test_update_location_duplicate_name(client, manager_user):
    client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Room Alpha", "max_occupancy": 10}
    )
    res2 = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Room Beta", "max_occupancy": 10}
    )
    loc_id = res2.json()["location_id"]

    patch_res = client.patch(
        f"/locations/{loc_id}",
        headers=manager_user["headers"],
        json={"office_room": "Room Alpha"}
    )
    assert patch_res.status_code == 400
    assert "already exists" in patch_res.json()["detail"]


def test_delete_location_success(client, manager_user):
    create_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "To Be Deleted", "max_occupancy": 12}
    )
    loc_id = create_res.json()["location_id"]

    del_res = client.delete(f"/locations/{loc_id}", headers=manager_user["headers"])
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]


def test_delete_location_forbidden_for_employee(client, manager_user, employee_user):
    create_res = client.post(
        "/locations/",
        headers=manager_user["headers"],
        json={"office_room": "Safe Room", "max_occupancy": 10}
    )
    loc_id = create_res.json()["location_id"]

    del_res = client.delete(f"/locations/{loc_id}", headers=employee_user["headers"])
    assert del_res.status_code == 403
    assert "Only managers can perform this action" in del_res.json()["detail"]
