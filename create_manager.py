import sys
import getpass
from database import db, User, init_db
from auth import hash_password

def create_initial_manager():
    init_db()
    db.connect(reuse_if_open=True)
    print("creating first user")
    username = input("enter your username: ")
    if not username:
        print("username cannot be empty")
        sys.exit(1)
    if User.select().where(User.username == username).exists():
        print("username already exists")
        sys.exit(1)
    email = input("enter your email address: ")
    name = input("enter your name: ")
    surname = input("enter your surname: ")
    password = input("enter your password: ")
    if len(password) < 8:
        print("password must be at least 8 characters")
        sys.exit(1)
    role = int(input("1 for manager, 2 for admin "))
    if role == 1:
        chosen_role="manager"
    elif role == 2:
        chosen_role="superadmin"
    else:
        print("wrong choice")
        sys.exit(1)

    manager = User.create(
        name=name,
        surname=surname,
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=chosen_role)
    print(f"congrats! {manager.username} with id {manager.id} has been created!")

    if not db.is_closed():
        db.close()
if __name__ == "__main__":
    create_initial_manager()