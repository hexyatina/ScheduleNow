from fastapi import APIRouter, HTTPException, Depends, status
from database import User, Group, GroupMember
from schemas import CreateUser, LoginRequest, UpdateUserRole, UpdateProfile
from auth import create_access_token, get_current_user, require_superadmin, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(data: CreateUser):

    user_exists = User.select().where(
        (User.email == data.email) | (User.username == data.username)
    ).exists()

    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )

    new_user = User.create(
        name=data.name,
        surname=data.surname,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="employee"
    )

    all_group, _ = Group.get_or_create(
        name="All",
        defaults={"description": "All company employees and managers"}
    )
    GroupMember.get_or_create(group=all_group.id, user=new_user.id)

    return {
        "message": "Successfully registered",
        "user_id": new_user.id
    }

@router.post("/login")
def login_user(data: LoginRequest):
    user = User.get_or_none(User.username == data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token(user_id=user.id, role=user.role)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    memberships = (
        GroupMember.select(GroupMember, Group)
        .join(Group)
        .where(GroupMember.user == current_user.id)
        .order_by(Group.name.asc())
    )
    groups = [{"id": m.group.id, "name": m.group.name} for m in memberships]

    return {
        "id": current_user.id,
        "name": current_user.name,
        "surname": current_user.surname,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "groups": groups
    }

@router.patch("/me")
def update_my_profile(data: UpdateProfile, current_user: User = Depends(get_current_user)):
    if data.email and data.email.lower() != current_user.email.lower():
        email_taken = User.select().where(
            (User.email == data.email) & (User.id != current_user.id)
        ).exists()
        if email_taken:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        current_user.email = data.email

    if data.name:
        current_user.name = data.name
    if data.surname:
        current_user.surname = data.surname

    if data.new_password:
        if not data.current_password:
            raise HTTPException(
                status_code=400,
                detail="Current password is required to change password"
            )
        if not verify_password(data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        current_user.password_hash = hash_password(data.new_password)
    elif data.current_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be provided if current password is entered"
        )

    current_user.save()

    memberships = (
        GroupMember.select(GroupMember, Group)
        .join(Group)
        .where(GroupMember.user == current_user.id)
        .order_by(Group.name.asc())
    )
    groups = [{"id": m.group.id, "name": m.group.name} for m in memberships]

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "surname": current_user.surname,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "groups": groups
        }
    }

@router.get("/")
def get_all_users(current_user: User = Depends(get_current_user)):
    users = User.select().order_by(User.name.asc())
    return [
        {
            "id": u.id,
            "name": u.name,
            "surname": u.surname,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]

@router.patch("/{user_id}/role")
def update_user_role(user_id: int, data: UpdateUserRole, current_user: User = Depends(require_superadmin)):
    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(status_code=400, detail="user not found")
    if current_user.id == user.id and data.role != "superadmin":
        raise HTTPException(status_code=400, detail="you cannot demote yourself from superadmin")

    user.role = data.role
    user.save()

    managers_group = Group.get_or_none(Group.name == "Managers")
    if managers_group:
        if data.role in ("manager", "superadmin"):
            GroupMember.get_or_create(group=managers_group.id, user=user.id)
        else:
            GroupMember.delete().where(
                (GroupMember.group == managers_group.id) &
                (GroupMember.user == user.id)
            ).execute()
    return {
        "message": f"role for user {user_id} has been updated to {data.role}",
        "user_id": user_id,
        "role": data.role
    }
