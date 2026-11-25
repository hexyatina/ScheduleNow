def test_register_user_success(client):
    response = client.post("/users/register", json={
        "name": "Alice",
        "surname": "Smith",
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Successfully registered"
    assert "user_id" in data


def test_register_user_duplicate_email(client, employee_user):
    response = client.post("/users/register", json={
        "name": "Duplicate",
        "surname": "User",
        "username": "unique_username",
        "email": employee_user["user"].email,
        "password": "password123"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, employee_user):
    response = client.post("/users/login", json={
        "username": employee_user["user"].username,
        "password": "secret123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "employee"


def test_login_wrong_password(client, employee_user):
    response = client.post("/users/login", json={
        "username": employee_user["user"].username,
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"


def test_get_my_profile(client, employee_user):
    response = client.get("/users/me", headers=employee_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == employee_user["user"].username
    assert data["email"] == employee_user["user"].email
    assert data["role"] == "employee"


def test_get_my_profile_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_superadmin_can_promote_employee_to_manager(client, superadmin_user, employee_user):
    target_id = employee_user["user"].id
    response = client.patch(
        f"/users/{target_id}/role",
        headers=superadmin_user["headers"],
        json={"role": "manager"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "manager"


def test_superadmin_can_demote_manager_to_employee(client, superadmin_user, manager_user):
    target_id = manager_user["user"].id
    response = client.patch(
        f"/users/{target_id}/role",
        headers=superadmin_user["headers"],
        json={"role": "employee"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "employee"


def test_superadmin_cannot_demote_self(client, superadmin_user):
    response = client.patch(
        f"/users/{superadmin_user['user'].id}/role",
        headers=superadmin_user["headers"],
        json={"role": "employee"}
    )
    assert response.status_code == 400
    assert "cannot demote yourself from superadmin" in response.json()["detail"]


def test_change_role_forbidden_for_manager(client, manager_user, employee_user):
    response = client.patch(
        f"/users/{employee_user['user'].id}/role",
        headers=manager_user["headers"],
        json={"role": "manager"}
    )
    assert response.status_code == 403
    assert "Only superadmins can perform this action" in response.json()["detail"]


def test_change_role_forbidden_for_employee(client, employee_user):
    response = client.patch(
        f"/users/{employee_user['user'].id}/role",
        headers=employee_user["headers"],
        json={"role": "manager"}
    )
    assert response.status_code == 403
    assert "Only superadmins can perform this action" in response.json()["detail"]


def test_superadmin_forbidden_from_manager_actions(client, superadmin_user):
    event_res = client.post(
        "/events/createEvent",
        headers=superadmin_user["headers"],
        json={
            "title": "Superadmin Event",
            "start_time": "2026-11-20T10:00:00",
            "end_time": "2026-11-20T11:00:00"
        }
    )
    assert event_res.status_code == 403
    assert "Only managers can perform this action" in event_res.json()["detail"]

    loc_res = client.post(
        "/locations/",
        headers=superadmin_user["headers"],
        json={"office_room": "Admin Room", "max_occupancy": 10}
    )
    assert loc_res.status_code == 403
    assert "Only managers can perform this action" in loc_res.json()["detail"]


def test_get_all_users(client, employee_user):
    res = client.get("/users/", headers=employee_user["headers"])
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_update_my_profile_success(client, employee_user):
    res = client.patch(
        "/users/me",
        headers=employee_user["headers"],
        json={
            "name": "UpdatedName",
            "surname": "UpdatedSurname",
            "email": "updated_employee@example.com"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Profile updated successfully"
    assert data["user"]["name"] == "UpdatedName"
    assert data["user"]["surname"] == "UpdatedSurname"
    assert data["user"]["email"] == "updated_employee@example.com"
    assert "groups" in data["user"]


def test_update_my_profile_duplicate_email(client, employee_user, manager_user):
    res = client.patch(
        "/users/me",
        headers=employee_user["headers"],
        json={"email": manager_user["user"].email}
    )
    assert res.status_code == 400
    assert "User with this email already exists" in res.json()["detail"]


def test_update_my_profile_change_password(client, employee_user):
    res = client.patch(
        "/users/me",
        headers=employee_user["headers"],
        json={
            "current_password": "password123",
            "new_password": "brandnewpassword999"
        }
    )
    assert res.status_code == 200
    assert res.json()["message"] == "Profile updated successfully"

    login_res = client.post(
        "/users/login",
        json={
            "username": employee_user["user"].username,
            "password": "brandnewpassword999"
        }
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_update_my_profile_wrong_current_password(client, employee_user):
    res = client.patch(
        "/users/me",
        headers=employee_user["headers"],
        json={
            "current_password": "wrongcurrentpassword",
            "new_password": "brandnewpassword999"
        }
    )
    assert res.status_code == 400
    assert "Current password is incorrect" in res.json()["detail"]


def test_update_my_profile_missing_current_password(client, employee_user):
    res = client.patch(
        "/users/me",
        headers=employee_user["headers"],
        json={
            "new_password": "brandnewpassword999"
        }
    )
    assert res.status_code == 400
    assert "Current password is required to change password" in res.json()["detail"]


def test_update_my_profile_unauthorized(client):
    res = client.patch(
        "/users/me",
        json={"name": "Hacker"}
    )
    assert res.status_code == 401


