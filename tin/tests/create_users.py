from __future__ import annotations

from django.contrib.auth import get_user_model

__all__ = ("user_data", "add_users_to_database")

# ruff: noqa: T201

# fmt: off
user_data = [
    #[username, is_teacher, is_student, is_staff, is_superuser]
    ["student", False, True, False, False],
    ["teacher", True, False, False, False],
    ["admin", False, False, True, True],
]
# fmt: on


def add_users_to_database(password: str, *, verbose: bool = True) -> None:
    User = get_user_model()

    for (
        username,
        is_teacher,
        is_student,
        is_staff,
        is_superuser,
    ) in user_data:
        user, created = User.objects.get_or_create(username=username)

        if not created:
            if verbose:
                print(f"User {username} already exists, skipping...")
            continue

        if verbose:
            print(f"Creating user {username}...")

        name = username.capitalize()
        user.full_name = name
        user.first_name = name
        user.last_name = name
        user.email = f"{username}@example.com"
        user.is_teacher = is_teacher
        user.is_student = is_student
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()
