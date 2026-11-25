def test_create_group_success(client, manager_user):
    response = client.post(
        "/groups/",
        headers=manager_user["headers"],
        json={"name": "Backend Team", "description": "Python devs"}
    )
    assert response.status_code == 200
    assert "group_id" in response.json()


def test_create_group_forbidden_for_employee(client, employee_user):
    response = client.post(
        "/groups/",
        headers=employee_user["headers"],
        json={"name": "Frontend Team", "description": "React devs"}
    )
    assert response.status_code == 403


def test_get_groups(client, manager_user, employee_user):
    client.post(
        "/groups/",
        headers=manager_user["headers"],
        json={"name": "DevOps", "description": "Infra"}
    )
    response = client.get("/groups/", headers=employee_user["headers"])
    assert response.status_code == 200
    groups = response.json()
    assert any(g["name"] == "DevOps" for g in groups)


def test_add_and_remove_member(client, manager_user, employee_user):
    # 1. Create group
    group_res = client.post(
        "/groups/",
        headers=manager_user["headers"],
        json={"name": "QA Team", "description": "Testers"}
    )
    group_id = group_res.json()["group_id"]

    # 2. Add employee
    add_res = client.post(
        f"/groups/{group_id}/members",
        headers=manager_user["headers"],
        json={"user_id": employee_user["user"].id}
    )
    assert add_res.status_code == 200

    # 3. Check details
    details_res = client.get(f"/groups/{group_id}", headers=manager_user["headers"])
    assert details_res.status_code == 200
    assert details_res.json()["total_members"] == 1

    # 4. Remove member
    del_res = client.delete(
        f"/groups/{group_id}/members/{employee_user['user'].id}",
        headers=manager_user["headers"]
    )
    assert del_res.status_code == 200

    # 5. Check details again
    details_res2 = client.get(f"/groups/{group_id}", headers=manager_user["headers"])
    assert details_res2.json()["total_members"] == 0


def test_add_duplicate_member(client, manager_user, employee_user):
    group_res = client.post(
        "/groups/",
        headers=manager_user["headers"],
        json={"name": "Designers", "description": "UI/UX"}
    )
    group_id = group_res.json()["group_id"]

    client.post(
        f"/groups/{group_id}/members",
        headers=manager_user["headers"],
        json={"user_id": employee_user["user"].id}
    )
    dup_res = client.post(
        f"/groups/{group_id}/members",
        headers=manager_user["headers"],
        json={"user_id": employee_user["user"].id}
    )
    assert dup_res.status_code == 400
    assert "already in this group" in dup_res.json()["detail"]


def test_system_all_group_protections(client, manager_user, employee_user):
    from database import Group, GroupMember
    all_group, _ = Group.get_or_create(name="All", defaults={"description": "All employees"})
    GroupMember.get_or_create(group=all_group.id, user=employee_user["user"].id)

    # 1. Cannot delete 'All' group
    del_res = client.delete(f"/groups/{all_group.id}", headers=manager_user["headers"])
    assert del_res.status_code == 400
    assert "system group" in del_res.json()["detail"]

    # 2. Cannot rename 'All' group
    patch_res = client.patch(
        f"/groups/{all_group.id}",
        headers=manager_user["headers"],
        json={"name": "NotAll"}
    )
    assert patch_res.status_code == 400
    assert "cannot be renamed" in patch_res.json()["detail"]

    # 3. Cannot remove member from 'All' group
    rem_res = client.delete(
        f"/groups/{all_group.id}/members/{employee_user['user'].id}",
        headers=manager_user["headers"]
    )
    assert rem_res.status_code == 400
    assert "Cannot remove members" in rem_res.json()["detail"]
