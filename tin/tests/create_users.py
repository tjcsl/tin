from django.contrib.auth import get_user_model

__all__ = ("user_data", "add_users_to_database")

# fmt: off
user_data = [
    #[username, is_teacher, is_student, is_staff, is_superuser]
    ["student", False, True, False, False],
    ["teacher", True, False, False, False],
    ["admin", False, False, True, True],
]
# fmt: on


def add_users_to_database(password: str, debug: bool = True) -> None:
    User = get_user_model()

    for (
        username,
        is_teacher,
        is_student,
        is_staff,
        is_superuser,
    ) in user_data:
        if debug:
            print(f"Creating user {username}")

        user = User.objects.get_or_create(username=username)[0]

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
