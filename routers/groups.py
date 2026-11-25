from fastapi import APIRouter, HTTPException, Depends
from database import Group, GroupMember, User
from schemas import CreateGroup, AddGroupMember, UpdateGroup
from auth import require_manager, get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("/")
def get_groups(current_user: User = Depends(get_current_user)):
    groups = Group.select()
    return [{"id": g.id, "name": g.name, "description": g.description} for g in groups]

@router.post("/")
def create_group(data: CreateGroup, current_user: User = Depends(require_manager)):
    if Group.select().where(Group.name == data.name).exists():
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    group = Group.create(name=data.name, description=data.description)
    return {"message": "Group created successfully", "group_id": group.id}


@router.get("/{group_id}")
def get_group_details(group_id: int, current_user: User = Depends(get_current_user)):
    group = Group.get_or_none(Group.id == group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = (
        GroupMember.select(GroupMember, User)
        .join(User, on=(GroupMember.user == User.id))
        .where(GroupMember.group == group_id)
    )

    members_list = [
        {
            "id": m.user.id,
            "username": m.user.username,
            "name": m.user.name,
            "surname": m.user.surname,
            "email": m.user.email,
            "role": m.user.role,
        }
        for m in members
    ]

    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "total_members": len(members_list),
        "members": members_list,
    }

@router.patch("/{group_id}")
def update_group(
    group_id: int,
    data: UpdateGroup,
    current_user: User = Depends(require_manager)
):
    group = Group.get_or_none(Group.id == group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.name.lower() in ("all", "managers") and data.name is not None and data.name.lower() != group.name.lower():
        raise HTTPException(status_code=400, detail=f"The '{group.name}' group is a system group and cannot be renamed")

    if data.name is not None and data.name != group.name:
        if Group.select().where(Group.name == data.name).exists():
            raise HTTPException(status_code=400, detail="Group with this name already exists")
        group.name = data.name

    if data.description is not None:
        group.description = data.description

    group.save()
    return {"message": "Group updated successfully", "group_id": group.id}

@router.post("/{group_id}/members")
def add_member(
    group_id: int,
    data: AddGroupMember,
    current_user: User = Depends(require_manager)
):
    group = Group.get_or_none(Group.id == group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = User.get_or_none(User.id == data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if GroupMember.select().where((GroupMember.group == group_id) & (GroupMember.user == data.user_id)).exists():
        raise HTTPException(status_code=400, detail="User already in this group")

    GroupMember.create(group=group_id, user=data.user_id)
    return {"message": f"User {user.username} added to {group.name}"}


@router.delete("/{group_id}/members/{user_id}")
def remove_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(require_manager)
):
    group = Group.get_or_none(Group.id == group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.name.lower() == "all":
        raise HTTPException(status_code=400, detail="Cannot remove members from the system 'All' group")

    membership = GroupMember.get_or_none(
        (GroupMember.group == group_id) & (GroupMember.user == user_id)
    )
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this group")

    membership.delete_instance()
    return {"message": "User removed from group"}

@router.delete("/{group_id}")
def delete_group(group_id: int, current_user: User = Depends(require_manager)):
    group = Group.get_or_none(Group.id == group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.name.lower() in ("all", "managers"):
        raise HTTPException(status_code=400, detail=f"The '{group.name}' group is a system group and cannot be deleted")

    group.delete_instance(recursive=True)
    return {"message": "Group deleted successfully"}